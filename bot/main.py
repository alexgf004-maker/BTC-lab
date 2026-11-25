"""Punto de entrada del bot.

  python -m bot.main --config bot/config.yaml            # bucle continuo (se ejecuta cada hora en punto + 2 min)
  python -m bot.main --config bot/config.yaml --once     # un solo ciclo (para cron o pruebas)
  python -m bot.main --config bot/config.yaml --status   # muestra el estado sin operar
"""
from __future__ import annotations

import argparse
import logging
import logging.handlers
import time
from pathlib import Path

import pandas as pd
import yaml

from .binance import Binance
from .broker import ExchangeBroker, PaperBroker
from .journal import Journal
from .market import LiveMarket
from .notify import Telegram
from .reconcile import futures_margin_guard, reconcile
from .risk import RiskGuard
from .state import State
from .strategies.carry import Carry
from .strategies.momentum import Rafaga
from .strategies.premium import PrimaRapida
from .strategies.trend import Trend
from .strategies.weak_alts import WeakAlts
from .strategies.weekend import Weekend
from .universe_live import LiveUniverse

log = logging.getLogger("bot")


H_DEFAULT = {"activo": True, "seguimiento": True, "fraccion": 0.10, "slot": 0.25, "max_pos": 4, "entrada": -0.005,
             "salida": 0.001, "max_horas": 24, "K": 30, "borrow_apr": 0.30}
G_DEFAULT = {"activo": True, "seguimiento": False, "fraccion": 0.20, "risk": 0.0025, "filtro_euforia": 0.0003, "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]}


def build(cfg):
    mode = cfg["modo"]
    # fuente de los datos de mercado: en paper se usan los reales salvo que se indique "testnet" (útil donde la API real está bloqueada)
    client = Binance(cfg.get("fuente_datos", "live") if mode == "paper" else ("live" if mode == "live" else "testnet"))
    market = LiveMarket(client)
    broker = PaperBroker(market) if mode == "paper" else ExchangeBroker(client)
    state, journal = State(cfg["estado"]), Journal(cfg["diario"], mode, Telegram(prefix=f"BTC-lab {mode}"))
    uni = LiveUniverse(client)
    total = cfg["capital"]
    B = cfg["bloques"]
    sc = lambda k: {**B[k], "capital": total * B[k]["fraccion"]}
    strategies = []
    if B["D_tendencia"]["activo"]:
        strategies.append(Trend(sc("D_tendencia"), state, broker, market, journal))
    if B["B_corto_alt_btc"]["activo"]:
        strategies.append(WeakAlts({**sc("B_corto_alt_btc"), "salidas_horarias": True}, state, broker, market, journal,
                                   lambda now: uni.top(now, B["B_corto_alt_btc"]["K"])))
    if B["F_fin_de_semana"]["activo"]:
        strategies.append(Weekend(sc("F_fin_de_semana"), state, broker, market, journal, lambda: uni.equities(market.now)))
    spot_ok = mode in ("paper", "live")                     # el testnet de futuros no tiene spot ni margen
    if B["A_carry"]["activo"] and spot_ok:
        strategies.append(Carry(sc("A_carry"), state, broker, market, journal, lambda now: uni.top(now, B["A_carry"]["K"], need_spot=True), 1))
    if B["E_carry_inverso"]["activo"] and spot_ok:
        cfgE = B["E_carry_inverso"]

        def borrow_rate(sym):                                # interés real del préstamo por 8h (en paper: el máximo configurado)
            if mode != "live":
                return cfgE.get("borrow_apr_paper", 0.30) / (365 * 3)
            r = client.margin_interest_rate(sym.replace("USDT", ""))
            return (r or 1.0) * 8

        def borrow_ok(sym, qty):
            if mode != "live":
                return True
            try:
                return client.margin_max_borrowable(sym.replace("USDT", "")) >= qty
            except Exception:
                return False
        strategies.append(Carry(sc("E_carry_inverso"), state, broker, market, journal,
                                lambda now: uni.top(now, cfgE["K"], need_spot=True), -1, borrow_rate, borrow_ok))
    cfgG = {**G_DEFAULT, **B.get("G_rafaga", {})}
    cfgH = {**H_DEFAULT, **B.get("H_prima", {})}
    state.d["seguimiento"] = [k for k, v in {"G_rafaga": cfgG, "H_prima": cfgH}.items() if v.get("seguimiento")]
    if cfgH.get("activo", True) and spot_ok:
        brH = PaperBroker(market) if cfgH.get("seguimiento") else broker
        strategies.append(PrimaRapida({**cfgH, "capital": total * cfgH["fraccion"]}, state, brH, market, journal,
                                      lambda now: uni.top(now, cfgH["K"], need_spot=True)))
    if cfgG.get("activo", True):                             # en seguimiento: siempre con el bróker simulado
        brG = PaperBroker(market) if cfgG.get("seguimiento") else broker
        strategies.append(Rafaga({**cfgG, "capital": total * cfgG["fraccion"]}, state, brG, market, journal))
    return client, market, broker, state, journal, strategies


def initial_capital(cfg):
    """Capital inicial de la cartera: capital × suma de las fracciones de los bloques activos que cuentan (incluido G)."""
    B = cfg["bloques"]
    fr = sum(float(v.get("fraccion", 0)) for k, v in B.items() if v.get("activo") and k not in ("G_rafaga", "H_prima"))
    for name, dflt in (("G_rafaga", G_DEFAULT), ("H_prima", H_DEFAULT)):
        g = {**dflt, **B.get(name, {})}
        if g.get("activo", True) and not g.get("seguimiento"):
            fr += float(g["fraccion"])
    return cfg["capital"] * fr


def incorporate_g(cfg, state):
    """Una sola vez: al entrar G en la cartera, se suma su capital a la curva anterior y al máximo, para no crear un salto falso."""
    g = {**G_DEFAULT, **cfg["bloques"].get("G_rafaga", {})}
    if not g.get("activo", True) or g.get("seguimiento") or state.d.get("g_en_cartera"):
        return
    add = cfg["capital"] * float(g["fraccion"])
    f = Path(cfg["estado"]).parent / "capital.csv"
    if f.exists():
        import csv
        rows = list(csv.reader(open(f)))
        for r in rows[1:]:
            try:
                r[1] = str(round(float(r[1]) + add, 4))
            except (ValueError, IndexError):
                pass
        with open(f, "w", newline="") as fh:
            csv.writer(fh).writerows(rows)
    if state.d.get("equity_peak"):
        state.d["equity_peak"] += add
    state.d["g_en_cartera"] = True


def equity(state):
    """Capital de la cartera (sin los bloques en prueba, que se siguen aparte)."""
    skip = set(state.d.get("seguimiento", []))
    return sum(s["balance"] for k, s in state.d["sleeves"].items() if k not in skip)


def record_cycle(cfg, state, status):
    """Deja constancia de cada ciclo (para el panel web): hora real del ciclo y curva de capital."""
    import csv
    import json
    from datetime import datetime, timezone
    wall = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state.d["ultimo_ciclo"] = wall
    state.d["ultimo_estado"] = status
    f = Path(cfg["estado"]).parent / "capital.csv"
    new = not f.exists()
    with open(f, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["ts", "capital", "caida", "bloques"])
        w.writerow([wall, round(equity(state), 4), round(state.d.get("drawdown", 0), 6),
                    json.dumps({k: round(v["balance"], 4) for k, v in state.d["sleeves"].items()})])


def daily_summary(state, journal, now):
    if now.hour != 8 or state.d.get("ultimo_resumen") == str(now.date()):
        return
    lines = [f"capital {equity(state):,.2f} | caída {100 * state.d.get('drawdown', 0):.1f} %"]
    for k, s in state.d["sleeves"].items():
        tag = " (en prueba)" if k in state.d.get("seguimiento", []) else ""
        lines.append(f"{k}{tag}: {s['balance']:,.2f} | abiertas {len(s['positions'])} | cerradas {s['closed']}")
    if state.d.get("bloqueados"):
        lines.append(f"bloqueados: {list(state.d['bloqueados'])}")
    journal.log("cartera", "resumen", detail=" · ".join(lines))
    state.d["ultimo_resumen"] = str(now.date())


def cycle(cfg, client, market, broker, state, journal, strategies, guard):
    market.refresh_clock()
    now = market.now
    if cfg["modo"] in ("testnet", "live"):
        try:
            reconcile(state, client, journal, broker, check_spot=(cfg["modo"] == "live"))
            if cfg["modo"] == "live":
                futures_margin_guard(client, journal)
        except Exception as e:
            log.exception("comprobación con el exchange fallida: %s", e)
            journal.log("cartera", "error", detail=f"comprobación con el exchange: {str(e)[:150]}")
    status = guard.update(equity(state))
    if status == "revisar" and state.d.get("aviso_revisar") != str(now.date()):
        journal.log("cartera", "revisar", detail=f"caída {100 * state.d.get('drawdown', 0):.1f} % desde el máximo")
        state.d["aviso_revisar"] = str(now.date())
    if status == "parar":
        journal.log("cartera", "detenido", detail=f"caída {state.d.get('drawdown', 0):.1%}")
        state.save(); return
    for s in strategies:
        name = getattr(s, "name", None) or s.__class__.__module__.split(".")[-1]
        key = f"{name}"
        if state.d["last_run"].get(key) == str(now) or not s.due(now):
            continue
        try:
            s.run(now)
            state.d["last_run"][key] = str(now)
        except Exception as e:
            log.exception("error en %s: %s", key, e)
            journal.log(key, "error", detail=str(e)[:200])
        state.save()                                         # tras cada bloque: un fallo no deshace lo ya hecho
    daily_summary(state, journal, now)
    record_cycle(cfg, state, status)
    state.save()
    log.info("ciclo %s | capital %.2f | caída %.1f %% | %s", now, equity(state), 100 * state.d.get("drawdown", 0), status)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="bot/config.yaml")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    Path(cfg["estado"]).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.StreamHandler(), logging.handlers.RotatingFileHandler(Path(cfg["estado"]).parent / "bot.log",
                                                                                          maxBytes=5_000_000, backupCount=5)])
    prev = State(cfg["estado"]).d                              # nunca mezclar un estado simulado con dinero real
    if prev["sleeves"] and prev.get("modo", "paper") != cfg["modo"]:
        raise SystemExit(f"El estado {cfg['estado']} es de modo {prev.get('modo', 'paper')}, no de {cfg['modo']}. "
                         f"Muévelo (mv {cfg['estado']} {cfg['estado']}.antiguo) y vuelve a arrancar.")
    client, market, broker, state, journal, strategies = build(cfg)
    state.d["modo"] = cfg["modo"]
    incorporate_g(cfg, state)
    state.d["capital_inicial"] = initial_capital(cfg)
    guard = RiskGuard(state, cfg["riesgo"]["revisar_caida"], cfg["riesgo"]["parar_caida"], cfg["riesgo"]["apalancamiento_max"])
    if a.status:
        for k, s in state.d["sleeves"].items():
            print(f"{k}: saldo {s['balance']:.2f} | posiciones {list(s['positions'])} | operaciones cerradas {s['closed']}")
        return
    log.info("modo %s | bloques activos: %s", cfg["modo"], [type(s).__name__ for s in strategies])
    journal.log("cartera", "arranque", detail=f"modo {cfg['modo']} · bloques {[s.name for s in strategies]} · capital {equity(state):,.2f}"
                + (" · avisos de Telegram activos" if journal.notifier.enabled else " · Telegram no configurado"))
    while True:
        cycle(cfg, client, market, broker, state, journal, strategies, guard)
        if a.once:
            break
        nxt = (pd.Timestamp.now(tz="UTC").floor("1h") + pd.Timedelta("1h") + pd.Timedelta("2min"))
        time.sleep(max(5.0, (nxt - pd.Timestamp.now(tz="UTC")).total_seconds()))


if __name__ == "__main__":
    main()
