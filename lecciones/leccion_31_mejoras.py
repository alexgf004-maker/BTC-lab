"""Lección 31 — I1 hold inteligente en la cartera; I2 filtro de temporada de altcoins para B (docs/leccion_31.md)."""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import data, lab15, universe  # noqa: E402
from leccion_22_validacion import monthly_rebalanced, st  # noqa: E402
import leccion_27_hold as L27  # noqa: E402

HALVES = (("2020-03-01", "2022-12-31"), ("2023-01-01", "2026-10-31"))
OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]


def fmt(d):
    return f"Sharpe {d['Sharpe']:5.2f} | anual {100 * d['CAGR']:+6.1f} % | DD {100 * d['DD']:5.1f} % | peor mes {100 * d['peor_mes']:+5.1f} %"


def blocks():
    R = pd.read_csv(ROOT / "docs/l17_bloques_diarios.csv", index_col=0, parse_dates=True)
    a = R["A carry"]
    yrs = len(a) / 365.25
    target = 1.036 ** (1 / 365.25) - 1
    R["A carry"] = a - a.mean() + target                       # aproximación declarada: nivel del carry ejecutable
    print(f"A escalado: anual {100 * ((1 + R['A carry']).prod() ** (1 / yrs) - 1):.1f} %")
    btc = L27.spot_daily("BTCUSDT")
    c, _ = L27.simulate(btc, L27.weights_rule(btc, "vol+ma200"))
    R["H3 hold inteligente"] = c.pct_change().reindex(R.index).fillna(0)
    return R


def i1(R):
    base = ["A carry", "E carry inverso", "B S1 corto alt/BTC", "D tendencia BTC/ETH"]
    P = {"(a) base 1/4": monthly_rebalanced(R[base]),
         "(b) base + H3, 1/5": monthly_rebalanced(R[base + ["H3 hold inteligente"]]),
         "(c) H3 en lugar de D": monthly_rebalanced(R[base[:3] + ["H3 hold inteligente"]])}
    print("\n=== I1  correlación diaria H3–D:", round(R["H3 hold inteligente"].corr(R["D tendencia BTC/ETH"]), 2),
          "| mensual:", round(((1 + R["H3 hold inteligente"]).resample("ME").prod()).corr((1 + R["D tendencia BTC/ETH"]).resample("ME").prod()), 2))
    for a, b in HALVES + (("2020-03-01", "2026-10-31"),):
        print(f"--- {a} → {b}")
        for k, v in P.items():
            print(f"{k:24s} {fmt(st(v.loc[a:b]))}")
    return P


def altseason_index():
    syms = sorted(set(OLD + NEW))
    vol = universe.daily_volume(syms)
    mem = universe.monthly_members(vol, 31)
    closes = {s: data.load(s, "1h")["close"].resample("1D").last() for s in set().union(*mem.values())}
    btc = closes.get("BTCUSDT", data.load("BTCUSDT", "1h")["close"].resample("1D").last())
    r90 = {s: c.pct_change(90) for s, c in closes.items()}
    b90 = btc.pct_change(90)
    out = {}
    for d in pd.date_range("2020-06-01", "2026-10-31", tz="UTC"):
        m = pd.Timestamp(d.year, d.month, 1, tz="UTC")
        ss = [s for s in mem.get(m, set()) if s != "BTCUSDT"][:30]
        prev = d - pd.Timedelta("1D")
        vals = [r90[s].get(prev, np.nan) for s in ss]
        vals = [v for v in vals if v == v]
        if len(vals) >= 10 and b90.get(prev, np.nan) == b90.get(prev, np.nan):
            out[d] = np.mean([v > b90[prev] for v in vals])
    return pd.Series(out)


def i2():
    idx = altseason_index()
    print("\n=== I2  índice de temporada de altcoins: % de días > 0,75:", f"{100 * (idx > 0.75).mean():.1f} %",
          "| por año:", {y: f"{100 * (g > 0.75).mean():.0f}%" for y, g in idx.groupby(idx.index.year)})
    ok = lambda times: ~(idx.reindex(times.floor("1D")).fillna(0).to_numpy() > 0.75)
    base, tk0, _ = lab15.s1_relative_weakness(OLD + NEW, K=30)
    filt, tk1, _ = lab15.s1_relative_weakness(OLD + NEW, K=30, entry_ok=ok)
    for a, b in HALVES + (("2020-03-01", "2026-10-31"),):
        print(f"--- {a} → {b}")
        print(f"B sin filtro   {fmt(st(base.loc[a:b]))} | trades {((tk0.entry >= a) & (tk0.entry <= b)).sum()}")
        print(f"B con filtro   {fmt(st(filt.loc[a:b]))} | trades {((tk1.entry >= a) & (tk1.entry <= b)).sum()}")
    print("por año sin/con:", {y: f"{100 * ((1 + base[base.index.year == y]).prod() - 1):+.0f}/{100 * ((1 + filt[filt.index.year == y]).prod() - 1):+.0f}%"
                               for y in sorted(set(base.index.year))})
    return base, filt


if __name__ == "__main__":
    R = blocks()
    i1(R)
    i2()
