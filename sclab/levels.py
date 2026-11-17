"""Lección 26: soportes y resistencias frente a niveles placebo. Reglas: docs/leccion_26.md"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data

MAKER, TAKER_SLIP = 0.0002, 0.0007
MAXH = 168


def _atr(h, l, c, n=14):
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    return pd.Series(tr).ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


def _pivots(x, k, mode):
    s = pd.Series(x)
    w = s.rolling(2 * k + 1, center=True)
    ext = w.max() if mode == "max" else w.min()
    return np.flatnonzero((s == ext).to_numpy() & s.notna().to_numpy())


def level_list(b: pd.DataFrame, fam: str):
    """Devuelve lista de (desde_idx, hasta_idx, nivel) en índices de velas de 1h."""
    h, l = b["high"].to_numpy(), b["low"].to_numpy()
    n, out = len(b), []
    if fam == "giro_1h":
        for mode, arr in (("max", h), ("min", l)):
            for i in _pivots(arr, 24, mode):
                out.append((i + 24, min(i + 24 + 720, n - 1), arr[i]))
    elif fam == "giro_1d":
        d = b.resample("1D").agg({"high": "max", "low": "min"}).dropna()
        dpos = b.index.searchsorted(d.index)
        for mode, col in (("max", "high"), ("min", "low")):
            arr = d[col].to_numpy()
            for i in _pivots(arr, 5, mode):
                if i + 6 < len(d):
                    s = dpos[i + 6]
                    out.append((s, min(s + 24 * 60, n - 1), arr[i]))
    elif fam in ("dia_anterior", "semana_anterior"):
        rule = "1D" if fam == "dia_anterior" else "W-SUN"
        d = b.resample(rule).agg({"high": "max", "low": "min"}).dropna()
        starts = b.index.searchsorted(d.index + (pd.Timedelta("1D") if fam == "dia_anterior" else pd.Timedelta("0D")))
        span = 24 if fam == "dia_anterior" else 24 * 7
        if fam == "semana_anterior":
            starts = b.index.searchsorted(d.index + pd.Timedelta("1D"))       # la semana termina el domingo: activo desde el lunes
        for i in range(len(d)):
            s = starts[i]
            if s < n - 1:
                for v in (d["high"].iloc[i], d["low"].iloc[i]):
                    out.append((s, min(s + span, n - 1), v))
    return out


def touches(b, levels, member):
    """Primer toque de cada nivel viniendo del lado correcto → (idx, nivel, lado: +1 soporte / −1 resistencia)."""
    h, l, c = b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy()
    ev = []
    for s, e, v in levels:
        if s < 1 or s >= e:
            continue
        seg = (l[s:e] <= v) & (h[s:e] >= v)
        if not seg.any():
            continue
        j = s + int(np.argmax(seg))
        if not member[j]:
            continue
        side = 1 if c[j - 1] > v else (-1 if c[j - 1] < v else 0)
        if side:
            ev.append((j, v, side))
    return ev


def round_touches(b, member, step_mult, offset_frac=0.0, rearm=24):
    h, l, c = b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy()
    ev, last = [], {}
    for j in range(1, len(b)):
        if not member[j] or not (c[j - 1] > 0):
            continue
        step = 10.0 ** (np.floor(np.log10(c[j - 1])) - 1) * step_mult
        off = offset_frac * step
        k0, k1 = int(np.ceil((l[j] - off) / step)), int(np.floor((h[j] - off) / step))
        for k in range(k0, k1 + 1):
            v = k * step + off
            key = round(v, 12)
            if j - last.get(key, -10 ** 9) <= rearm:
                last[key] = j; continue
            last[key] = j
            side = 1 if c[j - 1] > v else (-1 if c[j - 1] < v else 0)
            if side:
                ev.append((j, v, side))
    return ev


def outcomes(b, ev, atr):
    """Para cada toque: rebote (+d en el sentido del rebote antes de −d) y continuación tras el primer cierre al otro lado."""
    h, l, c = b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy()
    n, rows = len(b), []
    for j, v, side in ev:
        d = 2 * atr[j - 1]
        if not (d > 0):
            continue
        up, dn = v + side * d, v - side * d          # objetivo de rebote / ruptura
        bounce = np.nan
        if ((l[j] <= dn) if side == 1 else (h[j] >= dn)):
            bounce = 0.0
        else:
            hi, lo = h[j + 1:j + 1 + MAXH], l[j + 1:j + 1 + MAXH]
            a = np.flatnonzero((hi >= up) if side == 1 else (lo <= up)); z = np.flatnonzero((lo <= dn) if side == 1 else (hi >= dn))
            fa, fz = (a[0] if len(a) else 10 ** 9), (z[0] if len(z) else 10 ** 9)
            if fa < 10 ** 9 or fz < 10 ** 9:
                bounce = 1.0 if fa < fz else 0.0
        # continuación: primer cierre al otro lado del nivel tras el toque
        cont = np.nan
        cl = c[j:j + MAXH]
        k = np.flatnonzero((cl < v) if side == 1 else (cl > v))
        if len(k):
            q = j + k[0]
            go, back = c[q] - side * d, c[q] + side * d
            hi, lo = h[q + 1:q + 1 + MAXH], l[q + 1:q + 1 + MAXH]
            a = np.flatnonzero((lo <= go) if side == 1 else (hi >= go)); z = np.flatnonzero((hi >= back) if side == 1 else (lo <= back))
            fa, fz = (a[0] if len(a) else 10 ** 9), (z[0] if len(z) else 10 ** 9)
            if fa < 10 ** 9 or fz < 10 ** 9:
                cont = 1.0 if fa < fz else 0.0
        # operación de rebote: limit en el nivel, stop −d, objetivo +d
        r = np.nan
        if bounce == bounce:
            fee = (MAKER + MAKER) if bounce == 1 else (MAKER + TAKER_SLIP)
            r = (1.0 if bounce == 1 else -1.0) - fee * v / d
        rows.append((b.index[j], v, side, d / v, bounce, cont, r))
    return pd.DataFrame(rows, columns=["t", "nivel", "lado", "d_rel", "rebote", "continua", "r"])


def run_coin(args):
    sym, member_months, seed = args
    b = data.load(sym, "1h")[["open", "high", "low", "close"]]
    if len(b) < 24 * 90:
        return []
    months = pd.DatetimeIndex(b.index.tz_localize(None).to_period("M").to_timestamp()).tz_localize("UTC")
    member = np.array([m in member_months for m in months])
    if not member.any():
        return []
    atr = _atr(b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy())
    rng = np.random.default_rng(seed)
    out = []
    for fam in ("giro_1h", "giro_1d", "dia_anterior", "semana_anterior"):
        lv = level_list(b, fam)
        pl = []
        for s, e, v in lv:
            a = atr[max(s - 1, 0)]
            u = rng.uniform(0.5, 2.0) * rng.choice([-1, 1])
            pl.append((s, e, v + u * a if np.isfinite(a) else np.nan))
        for kind, L in (("real", lv), ("placebo", [x for x in pl if np.isfinite(x[2])])):
            o = outcomes(b, touches(b, L, member), atr)
            o["familia"], o["tipo"], o["symbol"] = fam, kind, sym
            out.append(o)
    for fam, mult in (("redondo_fino", 1.0), ("redondo_grueso", 5.0)):
        for kind, off in (("real", 0.0), ("placebo", rng.uniform(0.2, 0.8))):
            o = outcomes(b, round_touches(b, member, mult, off), atr)
            o["familia"], o["tipo"], o["symbol"] = fam, kind, sym
            out.append(o)
    return out
