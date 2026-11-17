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
