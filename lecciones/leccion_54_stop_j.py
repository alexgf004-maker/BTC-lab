"""Lección 54 — Variantes de stop del bloque J (docs/leccion_54.md)."""
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import lab15, universe  # noqa: E402
from leccion_46_redondos import COST, daily, signals  # noqa: E402

VARS = ["S0 siguiente redondo (actual)", "S1 2 ATR", "S2 3 ATR", "S3 extremo de la ruptura + 1 ATR", "S4 sin stop"]


def job(args):
    sym, mem = args
    try:
        d = daily(sym)
    except Exception:
        return []
    if len(d) < 60:
        return []
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.r_[c[0], c[:-1]]), np.abs(l - np.r_[c[0], c[:-1]])))
    atr = pd.Series(tr).rolling(14).mean().to_numpy()
    fund = lab15._funding(sym)
    t = d.index
    rows = []
    for brk in (-1, 1):
        sigs = signals(d, brk, 0.0)
        for v, name in enumerate(VARS):
            busy = -1
            for i, L, step in sigs:
                if i <= busy or i + 1 >= len(d) or not (atr[i] > 0):
                    continue
                if not universe.is_member(mem, sym, pd.DatetimeIndex([t[i] + pd.Timedelta("1D")]))[0]:
                    continue
                fd = -brk; j = i + 1; e = o[j]
                stop = {0: L + fd * -step, 1: e - fd * 2 * atr[i], 2: e - fd * 3 * atr[i],
                        3: (h[i] + atr[i]) if fd < 0 else (l[i] - atr[i]), 4: None}[v]
                x, k = None, j
                if stop is not None and ((fd > 0 and e <= stop) or (fd < 0 and e >= stop)):
                    x = e                                               # el stop ya quedó atrás al abrir: salida inmediata
                else:
                    for k in range(j, min(j + 20, len(d))):
                        if stop is not None and fd > 0 and l[k] <= stop:
                            x = min(o[k], stop); break
                        if stop is not None and fd < 0 and h[k] >= stop:
                            x = max(o[k], stop); break
                        if (fd > 0 and c[k] > L) or (fd < 0 and c[k] < L):
                            x = c[k]; break
                    if x is None:
                        x = c[k]
                f = float(fund[(fund.index > t[j]) & (fund.index <= t[k] + pd.Timedelta("1D"))].sum()) if len(fund) else 0.0
                r = fd * (x / e - 1) - 2 * COST - fd * f
                dist = abs(e - stop) / e if stop is not None else np.nan
                rows.append((name, t[j], r, dist))
                busy = k
    return rows


def tcl(r, tt):
    u = r - r.mean()
    g = u.groupby(pd.DatetimeIndex(tt).tz_localize(None).to_period("W").values).sum()
    return r.mean() / (np.sqrt((g ** 2).sum()) / len(r))


if __name__ == "__main__":
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    mem = universe.monthly_members(vol, 30)
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem) for s in syms]))
    T = pd.DataFrame([r for rr in res for r in rr], columns=["v", "t", "r", "dist"])
    print("Bloque J (apostar a que la ruptura de un redondo falla), top 30, 2020 → 2026-10. Neto por operación.")
    for name in VARS:
        X = T[T.v == name]
        line = f"  {name:34s}"
        for lab, a, b in (("desarrollo", "2020-01-01", "2023-01-01"), ("examen", "2023-01-01", "2026-11-01")):
            Y = X[(X.t >= pd.Timestamp(a, tz="UTC")) & (X.t < pd.Timestamp(b, tz="UTC"))]
            line += f" | {lab}: n {len(Y)}, {100 * Y.r.mean():+.2f} %, t {tcl(Y.r, Y.t):+.2f}, acierto {100 * (Y.r > 0).mean():.0f} %"
        line += f" | peor {100 * X.r.min():+.1f} % | stop mediano {100 * X.dist.median():.1f} % (p10 {100 * X.dist.quantile(.1):.1f} %, p90 {100 * X.dist.quantile(.9):.1f} %)"
        print(line, flush=True)
