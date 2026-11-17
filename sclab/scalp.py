"""Scalping: simulador de ejecución en velas de 1m y las cuatro hipótesis de la Lección 10 (docs/leccion_10.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data

MAKER, TAKER, SLIP, THROUGH = 0.0002, 0.0005, 0.0003, 0.0001


def execute(m1: pd.DataFrame, orders: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """orders: pos (índice 1m en que la orden queda activa), side, kind ('limit'|'market'), limit, stop, tp,
    valid (velas 1m), exit_pos (índice 1m de salida por tiempo). Una posición a la vez. Devuelve (trades, órdenes enviadas)."""
    o, h, l, c = (m1[k].to_numpy() for k in ("open", "high", "low", "close"))
    t, n = m1.index, len(m1)
    rows, busy, sent = [], -1, 0
    for r in orders.sort_values("pos").itertuples():
        p = int(r.pos)
        if p <= busy or p >= n - 1:
            continue
        sent += 1
        d = int(r.side)
        if r.kind == "market":
            k, entry, fee_in = p, o[p], TAKER + SLIP
        else:
            k = -1
            for q in range(p, min(p + int(r.valid), n)):
                if (l[q] <= r.limit * (1 - THROUGH)) if d == 1 else (h[q] >= r.limit * (1 + THROUGH)):
                    k = q; break
            if k < 0:
                continue
            entry, fee_in = r.limit, MAKER
        R = abs(entry - r.stop)
        tp = r.tp if r.kind == "limit" else entry + d * r.tp        # en 'market', tp es la distancia al objetivo
        last = min(int(r.exit_pos), n - 1)
        px, why, j = None, "time", k
        for j in range(k, last + 1):
            if j > k and (o[j] - r.stop) * d <= 0:
                px, why = o[j], "sl"; break
            if ((l[j] if d == 1 else h[j]) - r.stop) * d <= 0:
                px, why = r.stop, "sl"; break
            if j > k and (((h[j] >= tp * (1 + THROUGH)) if d == 1 else (l[j] <= tp * (1 - THROUGH)))):
                px, why = tp, "tp"; break
        if px is None:
            px, j = c[last], last
        fee_out = MAKER if why == "tp" else TAKER + SLIP
        gross = d * (px - entry)
        rows.append((t[k], t[j], d, entry, px, why, R / entry, gross / R, (gross - entry * fee_in - px * fee_out) / R))
        busy = j
    cols = ["entry_time", "exit_time", "side", "entry", "exit", "reason", "stop_pct", "r_gross", "r_net"]
    return pd.DataFrame(rows, columns=cols), sent


def bars5(m1: pd.DataFrame) -> pd.DataFrame:
    b = m1.resample("5min").agg({"open": "first", "high": "max", "low": "min", "close": "last",
                                 "quote_volume": "sum", "volume": "sum", "taker_buy_volume": "sum"}).dropna()
    pc = b["close"].shift()
    tr = pd.concat([b["high"] - b["low"], (b["high"] - pc).abs(), (b["low"] - pc).abs()], axis=1).max(axis=1)
    b["atr"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    b["vavg"] = b["quote_volume"].rolling(288).mean().shift(1)
    # posición 1m de la primera vela posterior al cierre de cada vela de 5m
    b["pos"] = m1.index.searchsorted(b.index + pd.Timedelta("5min"))
    return b


def _orders(b, long, short, limit, stop_l, stop_s, tp_l, tp_s, valid, hold):
    out = []
    for mask, d, st, tp in [(long, 1, stop_l, tp_l), (short, -1, stop_s, tp_s)]:
        x = b[mask]
        out.append(pd.DataFrame({"pos": x["pos"].to_numpy(), "side": d, "kind": "limit", "limit": limit[mask].to_numpy(),
                                 "stop": st[mask].to_numpy(), "tp": tp[mask].to_numpy(), "valid": valid,
                                 "exit_pos": x["pos"].to_numpy() + hold}))
    return pd.concat(out, ignore_index=True)


def c1_vwap(m1, b):
    tp_ = (m1["high"] + m1["low"] + m1["close"]) / 3
    day = m1.index.floor("1D")
    vwap1 = (tp_ * m1["volume"]).groupby(day).cumsum() / m1["volume"].groupby(day).cumsum()
    vwap = vwap1.resample("5min").last().reindex(b.index)
    dev = b["close"] - vwap
    sd = dev.rolling(288).std().shift(1)
    okh = (b.index + pd.Timedelta("5min")).hour >= 2
    big = dev.abs() / b["close"] >= 0.004
    long, short = (dev < -2.5 * sd) & big & okh, (dev > 2.5 * sd) & big & okh
    c = b["close"]
    return _orders(b, long, short, c, c - dev.abs(), c + dev.abs(), vwap, vwap, 10, 60)


def c2_orb(m1, b=None):
    rows = []
    idx = m1.index
    days = pd.date_range(idx[0].floor("1D"), idx[-1].floor("1D"), freq="1D")
    h, l, c, o = (m1[k].to_numpy() for k in ("high", "low", "close", "open"))
    for dday in days:
        a = idx.searchsorted(dday + pd.Timedelta("13h30min")); z = idx.searchsorted(dday + pd.Timedelta("14h"))
        e = idx.searchsorted(dday + pd.Timedelta("16h")); x = idx.searchsorted(dday + pd.Timedelta("20h"))
        if z - a != 30 or e - z != 120 or x >= len(idx):
            continue
        rh, rl = h[a:z].max(), l[a:z].min()
        if not (0.003 <= (rh - rl) / rl <= 0.02):
            continue
        up, dn = np.flatnonzero(c[z:e] > rh), np.flatnonzero(c[z:e] < rl)
        fu, fd = (up[0] if len(up) else 10**9), (dn[0] if len(dn) else 10**9)
        if min(fu, fd) == 10**9:
            continue
        d = 1 if fu < fd else -1
        p = z + min(fu, fd) + 1
        entry = o[p]; stop = rl if d == 1 else rh
        R = abs(entry - stop)
        rows.append({"pos": p, "side": d, "kind": "market", "limit": np.nan, "stop": stop, "tp": 1.5 * R, "valid": 1, "exit_pos": x})
    return pd.DataFrame(rows)


def c3_flow(m1, b):
    tbr = b["taker_buy_volume"] / b["volume"]
    volok = b["quote_volume"] >= 3 * b["vavg"]
    long = (tbr >= 0.65) & volok & (b["close"] > b["open"])
    short = (tbr <= 0.35) & volok & (b["close"] < b["open"])
    c = b["close"]; R = np.maximum(1.5 * b["atr"], 0.0035 * c)
    return _orders(b, long, short, c, c - R, c + R, c + R, c - R, 10, 60)


def c4_sweep(m1, b):
    pl, ph = b["low"].rolling(48).min().shift(1), b["high"].rolling(48).max().shift(1)
    volok = b["quote_volume"] >= 2 * b["vavg"]
    c = b["close"]
    sl_, ss_ = b["low"] - 0.1 * b["atr"], b["high"] + 0.1 * b["atr"]
    long = (b["low"] < pl) & (c > pl) & volok & ((c - sl_) / c >= 0.003)
    short = (b["high"] > ph) & (c < ph) & volok & ((ss_ - c) / c >= 0.003)
    return _orders(b, long, short, c, sl_, ss_, c + 1.5 * (c - sl_), c - 1.5 * (ss_ - c), 10, 120)


HYP = {"C1 reversión al VWAP": c1_vwap, "C2 ruptura apertura EE. UU.": c2_orb,
       "C3 continuación de flujo": c3_flow, "C4 barrido de liquidez": c4_sweep}


def run_symbol(sym: str) -> dict:
    m1 = data.load(sym, "1m")
    m1 = m1[m1.index >= pd.Timestamp("2024-01-01", tz="UTC")]
    b = bars5(m1)
    out = {}
    for name, fn in HYP.items():
        orders = fn(m1, b).dropna(subset=["stop", "tp"])
        tr, sent = execute(m1, orders)
        tr["symbol"] = sym
        out[name] = (tr, sent)
    return out
