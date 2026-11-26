"""Lección 51 — Barridos de liquidez en el oro (XAUUSD). Reglas en docs/leccion_51.md."""
import io
import sys
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
H = pd.Timedelta("1h")


def load_m1():
    parts = []
    for f in sorted((ROOT / "data" / "histdata").glob("XAUUSD_*.zip")):
        with zipfile.ZipFile(f) as z:
            name = [n for n in z.namelist() if n.endswith(".csv")][0]
            parts.append(pd.read_csv(io.BytesIO(z.read(name)), sep=";", header=None, names=["t", "open", "high", "low", "close", "v"]))
    d = pd.concat(parts)
    t = pd.to_datetime(d.t, format="%Y%m%d %H%M%S") + pd.Timedelta("5h")              # EST fija → UTC
    df = d[["open", "high", "low", "close"]].set_index(pd.DatetimeIndex(t).tz_localize("UTC")).sort_index()
    return df[~df.index.duplicated()]


def bars(m1, rule):
    return m1.resample(rule, label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def run_trade(b, j, side, e, stop, tgt, t_exit):
    """Recorre las velas posteriores a j hasta t_exit. Stop primero si en la misma vela se tocan ambos."""
    hi, lo, c, idx = b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy(), b.index
    k = j
    for k in range(j + 1, len(b)):
        if idx[k] >= t_exit:
            return c[k - 1]
        if (side < 0 and hi[k] >= stop) or (side > 0 and lo[k] <= stop):
            return stop
        if (side < 0 and lo[k] <= tgt) or (side > 0 and hi[k] >= tgt):
            return tgt
    return c[k]


def session_sweep(b5, r0, r1, w0, w1, xh):
    """O1/O2: rango [r0, r1) h, barrido en [w0, w1) h, salida a xh h (horas desde las 00:00 UTC del día)."""
    rows = []
    idx = b5.index
    days = idx.floor("1D").unique()
    pos = pd.Series(np.arange(len(b5)), index=idx)
    for d in days:
        R = b5[(idx >= d + r0 * H) & (idx < d + r1 * H)]
        W = b5[(idx >= d + w0 * H) & (idx < d + w1 * H)]
        if len(R) < 0.5 * (r1 - r0) * 12 or len(W) < 6:
            continue
        RH, RL = R.high.max(), R.low.min()
        ext_hi, ext_lo = -np.inf, np.inf
        for t, bar in W.iterrows():
            ext_hi, ext_lo = max(ext_hi, bar.high), min(ext_lo, bar.low)
            side = 0
            if bar.high > RH and bar.close < RH:
                side, stop, tgt = -1, ext_hi, RL
            elif bar.low < RL and bar.close > RL:
                side, stop, tgt = 1, ext_lo, RH
            if side:
                e = bar.close
                risk = (stop - e) * -side
                if risk <= 0:
                    break
                x = run_trade(b5, pos[t], side, e, stop, tgt, d + xh * H)
                rows.append((t, side * (x / e - 1), risk / e))
                break
    return pd.DataFrame(rows, columns=["t", "g", "risk"])


def pdhl_sweep(b1, shift):
    """O3: barrido del máximo/mínimo del 'día' anterior (día que empieza a las `shift` h UTC); objetivo 2R; salida a las 21 h del día."""
    rows = []
    idx = b1.index
    day = (idx - shift * H).floor("1D") + shift * H
    g = b1.groupby(day)
    keys = list(g.groups.keys())
    pos = pd.Series(np.arange(len(b1)), index=idx)
    for a, b in zip(keys[:-1], keys[1:]):
        if b - a != pd.Timedelta("1D"):
            continue
        P, Dd = g.get_group(a), g.get_group(b)
        if len(P) < 12:
            continue
        PH, PL = P.high.max(), P.low.min()
        for t, bar in Dd.iterrows():
            if t >= b + 21 * H:
                break
            side = 0
            if bar.high > PH and bar.close < PH:
                side, stop = -1, bar.high
            elif bar.low < PL and bar.close > PL:
                side, stop = 1, bar.low
            if side:
                e = bar.close; risk = abs(e - stop)
                if risk <= 0:
                    break
                x = run_trade(b1, pos[t], side, e, stop, e - side * 2 * risk * -1 if False else e + side * 2 * risk, b + 21 * H)
                rows.append((t, side * (x / e - 1), risk / e))
                break
    return pd.DataFrame(rows, columns=["t", "g", "risk"])


def tcl(r, t):
    if len(r) < 3:
        return float("nan")
    u = r - r.mean()
    gr = u.groupby(pd.DatetimeIndex(t).tz_localize(None).to_period("W").values).sum()
    se = np.sqrt((gr ** 2).sum()) / len(r)
    return r.mean() / se if se > 0 else float("nan")


def report(name, T):
    for cost in (0.0002, 0.0005):
        X = T.assign(net=T.g - 2 * cost); X["R"] = X.net / X.risk
        line = f"  {name:38s} coste {100 * cost:.2f} %/lado"
        for lab, a, b in (("desarrollo 2012–18", "2012-01-01", "2019-01-01"), ("examen 2019–26", "2019-01-01", "2027-01-01")):
            Y = X[(X.t >= pd.Timestamp(a, tz="UTC")) & (X.t < pd.Timestamp(b, tz="UTC"))]
            line += f" | {lab}: n {len(Y)}, {100 * Y.net.mean():+.3f} % ({Y.R.mean():+.3f}R), t {tcl(Y.net, Y.t):+.2f}"
        line += f" | total t {tcl(X.net, X.t):+.2f}"
        print(line, flush=True)


if __name__ == "__main__":
    m1 = load_m1()
    print(f"XAUUSD M1: {len(m1):,} minutos, {m1.index[0]} → {m1.index[-1]}")
    b5, b1 = bars(m1, "5min"), bars(m1, "1h")
    print("\n=== O1 — Barrido del rango de Asia en la apertura de Londres")
    report("señal (Asia 00–06, barrido 07–10)", session_sweep(b5, 0, 6, 7, 10, 16))
    report("placebo (+3 h)", session_sweep(b5, 3, 9, 10, 13, 19))
    print("\n=== O2 — Barrido del rango de Londres en la apertura de Nueva York")
    report("señal (Londres 07–12, barrido 13–16)", session_sweep(b5, 7, 12, 13, 16, 20))
    report("placebo (+3 h)", session_sweep(b5, 10, 15, 16, 19, 23))
    print("\n=== O3 — Barrido del máximo/mínimo del día anterior (velas de 1 h, objetivo 2R)")
    report("señal (día UTC)", pdhl_sweep(b1, 0))
    report("placebo (día de 12:00 a 12:00)", pdhl_sweep(b1, 12))
