"""Punto de entrada del bot.

  python -m bot.main --config bot/config.yaml            # bucle continuo (se ejecuta cada hora en punto + 2 min)
  python -m bot.main --config bot/config.yaml --once     # un solo ciclo (para cron o pruebas)
  python -m bot.main --config bot/config.yaml --status   # muestra el estado sin operar
"""
from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import pandas as pd
import yaml

from .binance import Binance
from .broker import ExchangeBroker, PaperBroker
from .journal import Journal
from .market import LiveMarket
from .risk import RiskGuard
from .state import State
from .strategies.carry import Carry
from .strategies.trend import Trend
from .strategies.weak_alts import WeakAlts
from .strategies.weekend import Weekend
from .universe_live import LiveUniverse

log = logging.getLogger("bot")


def build(cfg):
    mode = cfg["modo"]
    # fuente de los datos de mercado: en paper se usan los reales salvo que se indique "testnet" (útil donde la API real está bloqueada)
    client = Binance(cfg.get("fuente_datos", "live") if mode == "paper" else ("live" if mode == "live" else "testnet"))
    market = LiveMarket(client)
    broker = PaperBroker(market) if mode == "paper" else ExchangeBroker(client)
    state, journal = State(cfg["estado"]), Journal(cfg["diario"], mode)
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
    return client, market, broker, state, journal, strategies


def equity(state):
    return sum(s["balance"] for s in state.d["sleeves"].values())


def cycle(cfg, client, market, broker, state, journal, strategies, guard):
    market.refresh_clock()
    now = market.now
    status = guard.update(equity(state))
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
                        handlers=[logging.StreamHandler(), logging.FileHandler(Path(cfg["estado"]).parent / "bot.log")])
    client, market, broker, state, journal, strategies = build(cfg)
    guard = RiskGuard(state, cfg["riesgo"]["revisar_caida"], cfg["riesgo"]["parar_caida"], cfg["riesgo"]["apalancamiento_max"])
    if a.status:
        for k, s in state.d["sleeves"].items():
            print(f"{k}: saldo {s['balance']:.2f} | posiciones {list(s['positions'])} | operaciones cerradas {s['closed']}")
        return
    log.info("modo %s | bloques activos: %s", cfg["modo"], [type(s).__name__ for s in strategies])
    while True:
        cycle(cfg, client, market, broker, state, journal, strategies, guard)
        if a.once:
            break
        nxt = (pd.Timestamp.now(tz="UTC").floor("1h") + pd.Timedelta("1h") + pd.Timedelta("2min"))
        time.sleep(max(5.0, (nxt - pd.Timestamp.now(tz="UTC")).total_seconds()))


if __name__ == "__main__":
    main()
