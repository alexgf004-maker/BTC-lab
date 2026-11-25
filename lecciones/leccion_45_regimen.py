"""Lección 45 — Asignación por régimen (R1) y control de caídas (R2). docs/leccion_45.md"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
import leccion_43_gestor as L  # noqa: E402
from sclab import data  # noqa: E402
from leccion_22_validacion import st  # noqa: E402

COLS = ["A carry", "E carry inverso", "B S1 corto alt/BTC", "D tendencia BTC/ETH", "G rafaga"]


def blocks():
    R = pd.read_csv(ROOT / "docs/l17_bloques_diarios.csv", index_col=0, parse_dates=True)
    a = R["A carry"]; R["A carry"] = a - a.mean() + (1.036 ** (1 / 365.25) - 1)
    R.index = pd.to_datetime(R.index, utc=True)
    R["G rafaga"] = L.g_series().reindex(R.index).fillna(0)
    return R[COLS].loc["2020-03-01":"2026-10-31"]


def regime_portfolio(R):
    bd = data.load("BTCUSDT", "1h").close.resample("1D").last()
    bull = (bd > bd.rolling(200).mean())
    vals, val = [], 1.0
    months = pd.Series(R.index.to_period("M"), index=R.index)
    for m in months.unique():
        days = R.index[months == m]
        prev = bull[bull.index < days[0]]
        up = bool(prev.iloc[-1]) if len(prev) else True
        w = np.array([1.5, 0.5, 0.5, 1.5, 1.5]) if up else np.array([0.5, 1.5, 1.5, 0.5, 0.5])
        w = w / w.sum()
        for d in days:
            val *= 1 + float(R.loc[d].to_numpy() @ w); vals.append((d, val))
    return pd.Series(dict(vals)).pct_change().fillna(0)


def dd_control(r):
    eq, peak, scale, out = 1.0, 1.0, 1.0, []
    for d, x in r.items():
        dd = 1 - eq / peak
        if dd > 0.05:
            scale = 0.5
        elif dd < 0.025:
            scale = 1.0
        eq *= 1 + scale * x; peak = max(peak, eq); out.append((d, scale * x))
    return pd.Series(dict(out))


if __name__ == "__main__":
    R = blocks()
    P0 = L.portfolio(R, lambda h: np.ones(h.shape[1]))
    P = {"P0 pesos iguales": P0, "R1 asignación por régimen": regime_portfolio(R), "R2 control de caídas": dd_control(P0)}
    for a_, b_ in (("2020-07-01", "2022-12-31"), ("2023-01-01", "2026-10-31"), ("2020-07-01", "2026-10-31")):
        print(f"--- {a_} → {b_}")
        for k, v in P.items():
            print(f"   {k:28s} {L.fmt(st(v.loc[a_:b_]))}")
