"""Lección 29 — M1/M2: creador de mercado con cola conservadora (docs/leccion_29.md)."""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab.mm_sim import run_day  # noqa: E402

SYMS = ["XRPUSDT", "LTCUSDT", "STXUSDT"]
DEV = ["2023-07-08", "2023-08-19", "2023-08-26", "2023-10-01", "2023-10-23", "2023-11-30"]
EXA = ["2024-02-12", "2024-02-22", "2024-02-26", "2024-03-05", "2024-03-17", "2024-03-25"]


IMB = (0.30, 0.70) if "--m3" in sys.argv else (-1.0, 2.0)


def job(a):
    try:
        return run_day(*a, imb_lo=IMB[0], imb_hi=IMB[1])
    except Exception as e:
        return dict(sym=a[0], day=a[1], error=str(e)[:100])


if __name__ == "__main__":
    jobs = [(s, d) for s in SYMS for d in DEV + EXA]
    with ProcessPoolExecutor(3) as ex:
        rows = list(ex.map(job, jobs))
    df = pd.DataFrame(rows)
    df["fase"] = np.where(df.day.isin(EXA), "examen", "desarrollo")
    df.to_csv(ROOT / ("docs/l29_m3_dias.csv" if "--m3" in sys.argv else "docs/l29_mm_dias.csv"), index=False)
    pd.set_option("display.width", 250)
    print(df.drop(columns=[c for c in ("error",) if c in df and df[c].isna().all()]).round(2).to_string())
    for (f, s), g in df.groupby(["fase", "sym"]):
        n = g.net_002 / g.notional * 1e4
        print(f"{f:10s} {s:8s} diferencial mediano {g.spread_bps.median():.2f} pb | medio diferencial cobrado {g.half_spread_bps.mean():+.2f} pb | "
              f"selección adversa a 1 s/10 s/60 s {g.mk1_bps.mean():+.2f}/{g.mk10_bps.mean():+.2f}/{g.mk60_bps.mean():+.2f} pb | "
              f"bruto {1e4 * (g.gross / g.notional).mean():+.2f} pb | neto (maker 0,02 %) {n.mean():+.2f} pb | "
              f"neto $/día {g.net_002.mean():+.0f} (t {g.net_002.mean() / g.net_002.std() * np.sqrt(len(g)):+.1f}) | bruto $/día {g.gross.mean():+.0f}")
