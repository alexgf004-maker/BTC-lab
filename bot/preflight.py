"""Comprobación previa antes de operar con dinero real. NO envía ninguna orden: solo lee.

  python -m bot.preflight --config bot/config.yaml

Termina con código 0 si todo es correcto, 1 si hay algún fallo que impide arrancar en real.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .binance import Binance

OK, WARN, FAIL = "✅", "⚠️ ", "❌"


class Report:
    def __init__(self):
        self.fails = 0

    def __call__(self, level, msg):
        self.fails += level == FAIL
        print(f"{level} {msg}")


def atr_frac(kl, n=14):
    """ATR(n) en 4h como fracción del precio, a partir de velas de Binance."""
    df = pd.DataFrame(kl, columns=list(range(len(kl[0])))).iloc[:, 1:5].astype(float)
    df.columns = ["o", "h", "l", "c"]
    tr = pd.concat([df.h - df.l, (df.h - df.c.shift()).abs(), (df.l - df.c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1] / df.c.iloc[-1])


def ratio_atr_frac(client, alt, n=14):
    a = pd.DataFrame(client.klines(alt, "4h", limit=200)).iloc[:, [2, 3, 4]].astype(float).values
    b = pd.DataFrame(client.klines("BTCUSDT", "4h", limit=200)).iloc[:, [2, 3, 4]].astype(float).values
    k = min(len(a), len(b))
    r = a[-k:] / b[-k:, [0, 1, 2]]                           # aprox. del ratio con máximos/mínimos de cada pata
    h, l, c = r[:, 0], r[:, 1], r[:, 2]
    tr = np.maximum(h - l, np.maximum(abs(h - np.roll(c, 1)), abs(l - np.roll(c, 1))))[1:]
    return float(pd.Series(tr).rolling(n).mean().iloc[-1] / c[-1])


def check_minimums(rep, client, cfg):
    """¿Las órdenes típicas de cada bloque superan los mínimos de Binance con este capital?"""
    total, B = cfg["capital"], cfg["bloques"]
    sl = {k: total * v["fraccion"] for k, v in B.items()}
    mn = lambda s: client.rules(s)["min_notional"] * 1.05

    if B["D_tendencia"]["activo"]:
        for s in B["D_tendencia"]["symbols"]:
            R = B["D_tendencia"]["m"] * atr_frac(client.klines(s, "4h", limit=100))
            notional = B["D_tendencia"]["risk"] * sl["D_tendencia"] / R
            lvl = OK if notional >= mn(s) else FAIL
            rep(lvl, f"D tendencia {s}: orden típica ≈ {notional:,.0f} USDT (mínimo {mn(s):,.0f})")

    if B["B_corto_alt_btc"]["activo"]:
        fr = [ratio_atr_frac(client, a) for a in ("ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT")]
        R = B["B_corto_alt_btc"]["m"] * float(np.median(fr))
        notional = B["B_corto_alt_btc"]["risk"] * sl["B_corto_alt_btc"] / R
        need = 1.5 * mn("BTCUSDT") * R / B["B_corto_alt_btc"]["risk"] / B["B_corto_alt_btc"]["fraccion"]   # 1,5x: las altcoins débiles son más volátiles
        lvl = OK if notional >= 1.5 * mn("BTCUSDT") else (WARN if notional >= mn("BTCUSDT") else FAIL)
        rep(lvl, f"B corto altcoins: pata típica ≈ {notional:,.0f} USDT; la pata de BTC exige ≥ {mn('BTCUSDT'):,.0f} "
                 f"→ capital total recomendado ≥ {need:,.0f} USDT (o desactiva B)")

    for k in ("A_carry", "E_carry_inverso"):
        if B[k]["activo"]:
            notional = sl[k] * B[k]["slot"] * B[k]["notional_frac"]
            lvl = OK if notional >= 30 else FAIL
            rep(lvl, f"{k}: cada posición ≈ {notional:,.0f} USDT por pata (mínimo práctico ≈ 30 en altcoins)")

    if B["F_fin_de_semana"]["activo"]:
        per = min(B["F_fin_de_semana"]["per_trade_usd"], B["F_fin_de_semana"]["max_frac_per_trade"] * sl["F_fin_de_semana"])
        lvl = OK if per >= 10 else WARN
        rep(lvl, f"F fin de semana: ≈ {per:,.0f} USDT por operación (requiere haber aceptado los contratos de acciones/TradFi en Binance)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="bot/config.yaml")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    rep = Report()
    env = "live" if cfg["modo"] == "live" else "testnet"
    print(f"Comprobación previa · modo {cfg['modo']} · capital configurado {cfg['capital']:,.2f} USDT\n")
    c = Binance(env)
    if not c.key or not c.secret:
        rep(FAIL, "faltan BINANCE_API_KEY / BINANCE_API_SECRET en el entorno (/etc/btclab/entorno)"); sys.exit(1)

    # 1) permisos de la clave
    need_spot = cfg["modo"] == "live" and (cfg["bloques"]["A_carry"]["activo"] or cfg["bloques"]["E_carry_inverso"]["activo"])
    if env == "live":
        try:
            r = c.api_restrictions()
        except Exception as e:
            rep(FAIL, f"no puedo leer los permisos de la clave: {e}"); sys.exit(1)
        if r.get("enableWithdrawals"):
            rep(FAIL, "la clave TIENE PERMISO DE RETIRADA. Quítalo en Binance antes de seguir. No se arranca."); sys.exit(1)
        rep(OK, "la clave no tiene permiso de retirada")
        rep(OK if r.get("ipRestrict") else FAIL, "clave restringida a la IP del servidor" if r.get("ipRestrict")
            else "la clave NO está restringida por IP: restríngela a la IP del VPS")
        rep(OK if r.get("enableFutures") else FAIL, "permiso de futuros" + ("" if r.get("enableFutures") else " DESACTIVADO"))
        if need_spot:
            for k, txt in (("enableSpotAndMarginTrading", "trading spot y margen"), ("enableMargin", "margen (préstamos)"),
                           ("permitsUniversalTransfer", "transferencia universal entre cuentas propias")):
                rep(OK if r.get(k) else FAIL, txt + ("" if r.get(k) else " DESACTIVADO (lo necesitan los bloques A/E)"))

    # 2) modo de posición
    try:
        hedge = c.position_mode_hedge()
        rep(FAIL if hedge else OK, "futuros en modo Cobertura (Hedge): cámbialo a Unidireccional (One-way)" if hedge
            else "futuros en modo Unidireccional (One-way)")
    except Exception as e:
        rep(FAIL, f"no puedo leer el modo de posición: {e}")

    # 3) saldos y posiciones ajenas
    total = 0.0
    try:
        acc = c.account()
        fut = float(acc["totalWalletBalance"])
        total += fut
        rep(OK, f"cuenta de futuros: {fut:,.2f} USDT (margen disponible {float(acc['availableBalance']):,.2f})")
        lev = {p["symbol"]: int(float(p.get("leverage", 0))) for p in acc.get("positions", [])}
        for s in ("BTCUSDT", "ETHUSDT"):
            if s in lev and lev[s] < 3:
                rep(WARN, f"apalancamiento máximo de {s} fijado en {lev[s]}x: súbelo a ≥ 5x (el bot no usa más de 1-1,5x en total)")
        foreign = [p for p in c.positions() if float(p["positionAmt"]) != 0]
        rep(WARN if foreign else OK, f"posiciones de futuros abiertas que no son del bot: {[p['symbol'] for p in foreign]} — ciérralas"
            if foreign else "sin posiciones de futuros abiertas")
        orders = [o for o in c.open_orders() if not str(o.get("clientOrderId", "")).startswith("btclab-")]
        if orders:
            rep(WARN, f"órdenes abiertas ajenas al bot en futuros: {sorted({o['symbol'] for o in orders})}")
    except Exception as e:
        rep(FAIL, f"no puedo leer la cuenta de futuros: {e}")
    if env == "live":
        try:
            spot = c.spot_balances().get("USDT", 0.0)
            total += spot
            rep(OK, f"cuenta spot: {spot:,.2f} USDT")
        except Exception as e:
            rep(FAIL if need_spot else WARN, f"no puedo leer la cuenta spot: {e}")
        try:
            m = c.margin_account()
            mu = m["activos"].get("USDT", {}).get("neto", 0.0)
            total += mu
            debts = [k for k, v in m["activos"].items() if v["prestado"] > 0]
            rep(WARN if debts else OK, f"cuenta de margen: {mu:,.2f} USDT" + (f" · préstamos abiertos ajenos: {debts}" if debts else ""))
        except Exception as e:
            rep(FAIL if cfg["bloques"]["E_carry_inverso"]["activo"] else WARN,
                f"no puedo leer la cuenta de margen (¿está activada?): {e}")
        lvl = OK if total >= cfg["capital"] * 0.98 else FAIL
        rep(lvl, f"USDT total en las tres cuentas: {total:,.2f} · capital configurado {cfg['capital']:,.2f}"
            + ("" if lvl == OK else " → baja 'capital' en config.yaml o deposita más"))

    # 4) mínimos de Binance por bloque
    print()
    try:
        check_minimums(rep, c, cfg)
    except Exception as e:
        rep(WARN, f"no pude estimar los mínimos por bloque: {e}")

    # 5) estado previo (p. ej. de una prueba en paper)
    st = Path(cfg["estado"])
    if st.exists():
        import json
        d = json.loads(st.read_text())
        old = d.get("modo", "paper")
        if d.get("sleeves") and old != cfg["modo"]:
            rep(FAIL, f"existe un estado de modo {old} en {st}: muévelo antes de arrancar (mv {st} {st}.{old})")

    print()
    if rep.fails:
        print(f"{FAIL} {rep.fails} fallo(s). Corrige lo anterior antes de arrancar en real."); sys.exit(1)
    print(f"{OK} Todo listo. Puedes arrancar el servicio.")


if __name__ == "__main__":
    main()
