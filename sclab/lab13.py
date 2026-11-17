"""Lección 13: W1 pescar mechas, B1 carry con trimestrales, C1 valoración en cadena. Reglas: docs/leccion_13.md"""
from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import data, portfolio, universe
from .universe import is_member

ROOT = Path(__file__).resolve().parent.parent
MAKER, TAKER_SLIP, THROUGH = 0.0002, 0.0007, 0.0001


# ------------------------------------------------------------------ W1
def w1_candidates(sym, members, k_sigma=5.0, tp_frac=0.5, hold=24):
    b = data.load(sym, "1h")
    o, h, l, c = (b[x].to_numpy() for x in ("open", "high", "low", "close"))
    r = pd.Series(c).pct_change()
    sd = r.rolling(720, min_periods=360).std().shift(1).to_numpy()      # conocida al empezar la vela
    mem = is_member(members, sym, b.index)
    t, n = b.index, len(b)
    one = pd.Timedelta("1h")
    rows = []
    for i in range(361, n - 1):
        if not mem[i] or not (sd[i] > 0):
            continue
        L = c[i - 1] * (1 - k_sigma * sd[i])
        if l[i] > L * (1 - THROUGH):
            continue
        entry = min(L, o[i])
        D = c[i - 1] - L
        stop, tp = L - D, L + tp_frac * D
        R = entry - stop
        if R <= 0:
            continue
        px, why, j = None, "time", i
        if l[i] <= stop:
            px, why = stop, "sl"
        else:
            last = min(i + hold, n - 1)
            for j in range(i + 1, last + 1):
                if o[j] <= stop:
                    px, why = o[j], "sl"; break
                if l[j] <= stop:
                    px, why = stop, "sl"; break
                if h[j] >= tp * (1 + THROUGH):
                    px, why = max(tp, o[j]), "tp"; break
            if px is None:
                px, j = c[last], last
        fee = entry * MAKER + px * (MAKER if why == "tp" else TAKER_SLIP)
        rows.append((sym, t[i], t[j] + one, 1, entry, px, R, (px - entry - fee) / R, why, D / c[i - 1]))
    return pd.DataFrame(rows, columns=["symbol", "entry_time", "exit_time", "side", "entry", "exit", "R", "r_net", "reason", "dist"])


def w1(symbols, K=20, risk=0.005, max_pos=10):
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    cands = pd.concat([w1_candidates(s, members) for s in symbols], ignore_index=True)
    closes = {s: data.load(s, "1h")["close"] for s in cands.symbol.unique()}
    curve, tk, lev = portfolio.run(cands, closes, risk, K=max_pos)
    daily = curve.resample("1D").last().pct_change().dropna()
    daily = daily[daily.index >= tk.entry_time.min().floor("1D")]
    tk["entry_time"] = pd.to_datetime(tk["entry_time"], utc=True); tk["exit_time"] = pd.to_datetime(tk["exit_time"], utc=True)
    key = cands[["symbol", "entry_time", "reason", "dist"]].copy()
    key["entry_time"] = pd.to_datetime(key["entry_time"], utc=True).astype(tk["entry_time"].dtype)
    tk = tk.merge(key, on=["symbol", "entry_time"], how="left")
    tk = tk.rename(columns={"r_net": "ret"}).assign(entry=lambda x: x.entry_time)
    extra = {"candidatas": len(cands), "tomadas": len(tk), "salidas": tk.reason.value_counts(normalize=True).round(2).to_dict(),
             "distancia_media": float(tk.dist.mean()), "apal_max": float(lev.max()), "E_R": float(tk.ret.mean())}
    return daily, tk, extra
