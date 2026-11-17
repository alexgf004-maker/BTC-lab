"""Lección 18: eventos de listado. Reglas: docs/leccion_18.md"""
import numpy as np
import pandas as pd

from . import data

LEG = 0.0028


def _f(s):
    try:
        return data.load_funding(s)
    except Exception:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))


def event_trade(sym, t_entry, hold_days, btc, fbtc, stop_rel=0.5):
    c = data.load(sym, "1h")["close"]; hi = data.load(sym, "1h")["high"]
    c = c[c.index >= t_entry]
    if len(c) < 24:
        return None
    t0 = c.index[0]; end = t0 + pd.Timedelta(days=hold_days)
    seg = c[c.index <= end]; hseg = hi.reindex(seg.index)
    b = btc.reindex(seg.index).ffill()
    rel_hi = (hseg / seg.iloc[0]) / (b / b.iloc[0])
    hit = rel_hi >= 1 + stop_rel
    if hit.iloc[1:].any():
        t1 = hit.iloc[1:].idxmax(); r_alt = (1 + stop_rel) * (b[t1] / b.iloc[0]) - 1; stopped = True
    else:
        t1 = seg.index[-1]; r_alt = seg.iloc[-1] / seg.iloc[0] - 1; stopped = False
    r_btc = b[t1] / b.iloc[0] - 1
    f_alt = _f(sym); fa = float(f_alt[(f_alt.index > t0) & (f_alt.index <= t1)].sum())
    fb = float(fbtc[(fbtc.index > t0) & (fbtc.index <= t1)].sum())
    net = -r_alt + r_btc + fa - fb - LEG
    return {"symbol": sym, "entry": t0, "exit": t1, "ret": net, "stopped": stopped, "funding_alt": fa}


def car_path(sym, t_event, days, btc):
    c = data.load(sym, "1h")["close"]
    out = {}
    base = c.asof(t_event) if t_event > c.index[0] else c.iloc[0]
    bb = btc.asof(t_event)
    for d in days:
        t = t_event + pd.Timedelta(days=d)
        if t < c.index[0] or t > c.index[-1]:
            out[d] = np.nan; continue
        out[d] = (c.asof(t) / base) / (btc.asof(t) / bb) - 1
    return out


def stats(r):
    r = pd.Series(r).dropna()
    return {"n": len(r), "media": r.mean(), "mediana": r.median(), "t": r.mean() / r.std() * np.sqrt(len(r)),
            "WR": (r > 0).mean(), "PF": r[r > 0].sum() / -r[r <= 0].sum()}
