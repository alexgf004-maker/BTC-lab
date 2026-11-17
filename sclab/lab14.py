"""Lección 14: familia W generalizada, grid neutral y prima de volatilidad. Reglas: docs/leccion_14.md"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data, portfolio, universe
from .universe import is_member

ROOT = Path(__file__).resolve().parent.parent
MAKER, TAKER_SLIP, THROUGH = 0.0002, 0.0007, 0.0001


def w_candidates(sym, members, k_sigma=5.0, direction=1, use_stop=True, tp_frac=0.5, hold=24):
    """direction=+1: compra en mechas hacia abajo; -1: venta en mechas hacia arriba."""
    b = data.load(sym, "1h")
    o, h, l, c = (b[x].to_numpy() for x in ("open", "high", "low", "close"))
    sd = pd.Series(c).pct_change().rolling(720, min_periods=360).std().shift(1).to_numpy()
    mem = is_member(members, sym, b.index)
    t, n, d = b.index, len(b), direction
    one = pd.Timedelta("1h")
    # se trabaja con precios "reflejados" para el lado corto: adverso = -d * precio
    lo = l if d == 1 else h          # extremo que ejecuta la entrada y el stop
    hi = h if d == 1 else l          # extremo que ejecuta el objetivo
    rows = []
    for i in range(361, n - 1):
        if not mem[i] or not (sd[i] > 0):
            continue
        L = c[i - 1] * (1 - d * k_sigma * sd[i])
        if (lo[i] - L * (1 - d * THROUGH)) * d > 0:
            continue
        entry = min(L, o[i]) if d == 1 else max(L, o[i])
        D = abs(c[i - 1] - L)
        stop, tp = L - d * D, L + d * tp_frac * D
        R = abs(entry - stop)
        px, why, j = None, "time", i
        if use_stop and (lo[i] - stop) * d <= 0:
            px, why = stop, "sl"
        else:
            last = min(i + hold, n - 1)
            for j in range(i + 1, last + 1):
                if use_stop and (o[j] - stop) * d <= 0:
                    px, why = o[j], "sl"; break
                if use_stop and (lo[j] - stop) * d <= 0:
                    px, why = stop, "sl"; break
                if (hi[j] - tp * (1 + d * THROUGH)) * d >= 0:
                    px, why = (max(tp, o[j]) if d == 1 else min(tp, o[j])), "tp"; break
            if px is None:
                px, j = c[last], last
        fee = entry * MAKER + px * (MAKER if why == "tp" else TAKER_SLIP)
        rows.append((sym, t[i], t[j] + one, d, entry, px, R, (d * (px - entry) - fee) / R, why, D / c[i - 1]))
    out = pd.DataFrame(rows, columns=["symbol", "entry_time", "exit_time", "side", "entry", "exit", "R", "r_net", "reason", "dist"])
    out["entry_time"] = pd.to_datetime(out["entry_time"], utc=True); out["exit_time"] = pd.to_datetime(out["exit_time"], utc=True)
    return out


def w_portfolio(symbols, K=20, risk=0.005, max_pos=10, **kw):
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    cands = pd.concat([w_candidates(s, members, **kw) for s in symbols], ignore_index=True)
    closes = {s: data.load(s, "1h")["close"] for s in cands.symbol.unique()}
    curve, tk, lev = portfolio.run(cands, closes, risk, K=max_pos)
    daily = curve.resample("1D").last().pct_change().dropna()
    tk["entry_time"] = pd.to_datetime(tk["entry_time"], utc=True)
    daily = daily[daily.index >= tk.entry_time.min().floor("1D")]
    key = cands[["symbol", "entry_time", "reason"]].copy()
    key["entry_time"] = pd.to_datetime(key["entry_time"], utc=True).astype(tk["entry_time"].dtype)
    tk = tk.merge(key, on=["symbol", "entry_time"], how="left").rename(columns={"r_net": "ret"})
    tk["entry_ts"] = tk["entry_time"]
    return daily, tk, cands


def tstats(r):
    return {"n": len(r), "WR": float((r > 0).mean()), "E": float(r.mean()), "PF": float(r[r > 0].sum() / -r[r <= 0].sum()),
            "peor": float(r.min())}


# ------------------------------------------------------------------ G1 grid neutral
def grid(sym, g=0.005, max_units=20, stop_levels=24, unit_frac=0.05, start="2020-01-01"):
    m = data.load(sym, "1m")
    m = m[m.index >= pd.Timestamp(start, tz="UTC")]
    o, h, l, c = (m[x].to_numpy() for x in ("open", "high", "low", "close"))
    day_end = np.flatnonzero(np.r_[np.diff(m.index.dayofyear.to_numpy()) != 0, True])
    is_end = np.zeros(len(c), bool); is_end[day_end] = True
    equity0, cash, inv, last = 1.0, 0.0, 0.0, 0          # cash = PnL realizado acumulado (sobre capital 1,0)
    pref = o[0]; qty = unit_frac * equity0 / pref
    up, dn = pref * (1 + g), pref / (1 + g)
    fills = stops = 0
    eq = []

    def target(lv):
        return -max(-max_units, min(max_units, lv)) * qty

    for i in range(len(c)):
        hi, lo = h[i], l[i]
        if hi >= up or lo <= dn:
            pts = (lo, hi, c[i]) if c[i] >= o[i] else (hi, lo, c[i])
            for p in pts:
                while True:
                    if p >= up:
                        last += 1; px = up
                    elif p <= dn:
                        last -= 1; px = dn
                    else:
                        break
                    tq = target(last)
                    if tq != inv:
                        dq = tq - inv
                        cash -= dq * px + abs(dq) * px * MAKER
                        inv = tq; fills += 1
                    if abs(last) >= stop_levels:                         # fuera de rango: cerrar y recentrar
                        cash += inv * px - abs(inv) * px * TAKER_SLIP
                        inv, last, stops = 0.0, 0, stops + 1
                        pref = px; qty = unit_frac * (equity0 + cash) / pref
                    lvl = pref * (1 + g) ** last
                    up, dn = lvl * (1 + g), lvl / (1 + g)
        if is_end[i]:
            eq.append(equity0 + cash + inv * c[i])
    curve = pd.Series(eq, index=m.index[day_end].floor("1D"))
    return curve, {"ejecuciones": fills, "salidas_de_rango": stops}
