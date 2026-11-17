"""Lección 23: T1/T2 fines de semana de perpetuos no cripto; T3 techo del funding. Reglas: docs/leccion_23.md"""
import numpy as np
import pandas as pd

from . import data

ASIA = {"HK0625USDT", "HK0700USDT", "HK0992USDT", "HK1810USDT", "KUAISHOUUSDT", "MEITUANUSDT", "TENCENTUSDT", "POPMARTUSDT",
        "SAMSUNGUSDT", "SAMSUNGEMUSDT", "SKHYNIXUSDT", "SKHYUSDT", "HYUNDAIUSDT", "NAVERUSDT", "LGELECTRONICSUSDT", "HANMIUSDT",
        "KODEX200USDT", "CSOPSAMSUNG2LUSDT", "CSOPSKHYNIX2LUSDT", "CXMTUSDT", "ZHIPUUSDT", "MINIMAXUSDT", "UNITREEUSDT", "ZHONGJIUSDT", "BYDUSDT"}
COMMOD = {"XAUUSDT", "XAGUSDT", "PAXGUSDT", "XAUTUSDT", "XPTUSDT", "XPDUSDT", "CLUSDT", "NATGASUSDT", "COPPERUSDT", "BZUSDT"}


def windows(sym):
    if sym in COMMOD:
        return ("FRI", 21), ("SUN", 21), ("MON", 1)
    if sym in ASIA:
        return ("FRI", 9), ("MON", 0), ("MON", 3)
    return ("FRI", 21), ("MON", 13), ("MON", 16)


DOW = {"FRI": 4, "SUN": 6, "MON": 0}


def weekend_obs(sym):
    c = data.load(sym, "1h")["open"]                # precio al INICIO de cada hora
    (d0, h0), (d1, h1), (d2, h2) = windows(sym)
    out = []
    mondays = c.index[(c.index.dayofweek == 0) & (c.index.hour == 0)]
    for m in mondays:
        def at(d, h):
            base = m - pd.Timedelta(days=3) if d == "FRI" else (m - pd.Timedelta(days=1) if d == "SUN" else m)
            t = base + pd.Timedelta(hours=h)
            return c.get(t, np.nan), t
        p0, t0 = at(d0, h0); p1, t1 = at(d1, h1); p2, t2 = at(d2, h2)
        if np.isfinite(p0) and np.isfinite(p1) and np.isfinite(p2) and p0 > 0:
            out.append({"symbol": sym, "lunes": m, "t1": t1, "t2": t2, "W": np.log(p1 / p0), "R": np.log(p2 / p1)})
    return pd.DataFrame(out)


def btc_window(t_a, t_b, btc):
    return np.log(btc.get(t_b, np.nan) / btc.get(t_a, np.nan))


def hedged_trade(sym, t_entry, hours, side, btc, fbtc, stop=0.30, leg=0.0028):
    """side=+1: largo moneda / corto BTC; −1: corto moneda / largo BTC. Stop si se mueve `stop` en contra frente a BTC (con extremos horarios)."""
    h = data.load(sym, "1h")
    c = h["close"][h.index >= t_entry]
    if len(c) < 3:
        return None
    t0 = c.index[0]; end = t0 + pd.Timedelta(hours=hours)
    seg = c[c.index <= end]; b = btc.reindex(seg.index).ffill()
    adverse = (h["low"] if side == 1 else h["high"]).reindex(seg.index)
    rel_adv = (adverse / seg.iloc[0]) / (b / b.iloc[0]) - 1
    hit = (rel_adv * side <= -stop)
    if hit.iloc[1:].any():
        t1 = hit.iloc[1:].idxmax(); r_rel = -stop; stopped = True
    else:
        t1 = seg.index[-1]; r_rel = side * ((seg.iloc[-1] / seg.iloc[0]) / (b.iloc[-1] / b.iloc[0]) - 1); stopped = False
    try:
        f = data.load_funding(sym); fa = float(f[(f.index > t0) & (f.index <= t1)].sum())
    except Exception:
        fa = 0.0
    fb = float(fbtc[(fbtc.index > t0) & (fbtc.index <= t1)].sum())
    net = r_rel - side * fa + side * fb - leg
    return {"symbol": sym, "entry": t0, "exit": t1, "ret": net, "stopped": stopped, "funding": -side * fa}
