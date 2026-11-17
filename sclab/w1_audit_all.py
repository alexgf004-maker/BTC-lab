"""Repite cada trade de W1 (simulación de 1h) minuto a minuto, con las velas de 1m de sus días."""
import concurrent.futures as cf
from pathlib import Path

import numpy as np
import pandas as pd

from sclab.funding_windows import day_file
from sclab.lab13 import MAKER, TAKER_SLIP, THROUGH

ROOT = Path(__file__).resolve().parent.parent


def replay(item):
    (sym, day), g = item
    days = sorted({day, day + pd.Timedelta("1D"), day + pd.Timedelta("2D")} if (g.entry_time.dt.hour >= 0).any() else {day})
    parts = [p for p in (day_file(sym, d) for d in days[:2]) if p is not None]
    if not parts:
        return []
    m = pd.concat(parts).sort_index(); m = m[~m.index.duplicated()]
    out = []
    for r in g.itertuples():
        w = m[(m.index >= r.entry_time) & (m.index < r.entry_time + pd.Timedelta("25h"))]
        if len(w) < 30:
            continue
        o, h, l, c = (w[x].to_numpy() for x in ("open", "high", "low", "close"))
        R = r.R
        entry = R / r.dist - R            # L = cierre previo − D, con D = R y cierre previo = R / dist
        stop, tp = entry - R, entry + 0.5 * R
        f = np.flatnonzero(l[:60] <= entry * (1 - THROUGH))
        if not len(f):
            continue
        q = f[0]; end = min(q + 24 * 60, len(c) - 1)
        ideal = worst = None; why = "time"
        for j in range(q, end + 1):
            if l[j] <= stop:
                ideal, worst, why = (min(stop, o[j]) if j > q else stop), l[j], "sl"; break
            if j > q and h[j] >= tp * (1 + THROUGH):
                ideal = worst = max(tp, o[j]); why = "tp"; break
        if ideal is None:
            ideal = worst = c[end]
        fee = lambda px: entry * MAKER + px * (MAKER if why == "tp" else TAKER_SLIP)
        out.append((r.conjunto, sym, r.entry_time, r.ret, why, (ideal - entry - fee(ideal)) / R, (worst - entry - fee(worst)) / R))
    return out


if __name__ == "__main__":
    T = pd.concat([pd.read_csv(ROOT / "docs/l13_criba_W1.csv").assign(conjunto="diseño"),
                   pd.read_csv(ROOT / "docs/l13_examen_W1.csv").assign(conjunto="examen")], ignore_index=True)
    T["entry_time"] = pd.to_datetime(T.entry_time, utc=True)
    groups = list(T.groupby(["symbol", T.entry_time.dt.floor("1D")]))
    res = []
    with cf.ThreadPoolExecutor(24) as ex:
        for i, r in enumerate(ex.map(replay, groups)):
            res += r
            if (i + 1) % 1000 == 0:
                print(i + 1, len(groups), len(res), flush=True)
    A = pd.DataFrame(res, columns=["conjunto", "symbol", "entry", "r_1h", "reason", "r_ideal", "r_pesimista"])
    A.to_csv(ROOT / "docs/l13_auditoria_W1_completa.csv", index=False)
    print("trades repetidos:", len(A), "de", len(T), flush=True)
