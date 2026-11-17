"""Lección 7: cartera combinada carry (80 %) + tendencia BTC/ETH (20 %). Reglas: docs/leccion_07.md"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import carry, data, portfolio, swing, trend, universe  # noqa: E402
from leccion_02_pullback import BAR, prepare  # noqa: E402
from leccion_03_tendencia import signals  # noqa: E402
from leccion_06_universo import spot_close, curve_metrics  # noqa: E402

W_CARRY, W_TREND = 0.8, 0.2
ALL = [s for l in open(ROOT / "data/universo.txt") if not l.startswith("#") for s in l.split()]


def combine(c_carry: pd.Series, c_trend: pd.Series) -> pd.Series:
    """Dos bloques con pesos 80/20, reequilibrados el día 1 de cada mes."""
    df = pd.concat([c_carry, c_trend], axis=1, keys=["c", "t"]).ffill().dropna()
    r = df.pct_change().fillna(0)
    val, out = 1.0, []
    month = None
    for t, row in r.iterrows():
        if t.month != month:
            vc, vt, month = val * W_CARRY, val * W_TREND, t.month
        vc *= 1 + row.c; vt *= 1 + row.t
        val = vc + vt
        out.append((t, val))
    return pd.Series(dict(out))


def yearly(curve):
    y = curve.resample("YE").last()
    return (y / y.shift(1).fillna(curve.iloc[0]) - 1)


if __name__ == "__main__":
    # ---- Bloque A: carry (100 % del bloque = 4 huecos del 25 %), pata corta a 2x
    vol = universe.daily_volume(ALL)
    members = universe.monthly_members(vol, 20)
    perp = {s: data.load(s, "1h")["close"] for s in ALL}
    highs = {s: data.load(s, "1h")["high"] for s in ALL}
    spot = {s: v for s in ALL if (v := spot_close(s)) is not None}
    fund = {s: data.load_funding(s) for s in ALL}
    cv, ep = carry.simulate(perp, spot, fund, members, max_pos=4, slot=0.25, notional_frac=2 / 3,
                            highs=highs, liq_move=0.45)
    c_carry = cv.equity.resample("1D").last()
    print("BLOQUE A carry:", {k: round(v, 3) for k, v in curve_metrics(c_carry, 365).items()},
          f"| episodios {len(ep)} | WR {(ep.pnl > 0).mean():.0%} | PF {ep.pnl[ep.pnl>0].sum()/-ep.pnl[ep.pnl<=0].sum():.1f}"
          f" | liquidaciones {int(ep.liq.sum())} | ocupación {cv.n_pos.mean()/4:.0%}")

    # ---- Bloque B: tendencia BTC + ETH
    prep = {s: prepare(s) for s in ["BTCUSDT", "ETHUSDT"]}
    cands = []
    for s, (df, f) in prep.items():
        t = trend.simulate(df, signals(df, 120, 1), 5.0, f, bar=BAR); t["symbol"] = s; cands.append(t)
    cands = pd.concat(cands, ignore_index=True)
    closes = {s: df["close"] for s, (df, _) in prep.items()}
    rows, curves = [], {"carry (bloque)": c_carry}
    for r_total in [0.005, 0.01, 0.02]:
        tc, tk, lev = portfolio.run(cands, closes, r_total / W_TREND)
        c_trend = tc.resample("1D").last()
        if r_total == 0.01:
            print("BLOQUE B tendencia BTC/ETH (riesgo 5 % del bloque):", {k: round(v, 3) for k, v in curve_metrics(c_trend, 365).items()},
                  f"| trades {len(tk)} | WR {(tk.r_net>0).mean():.0%} | PF {swing.stats(tk.r_net)['PF']:.2f} | apal. máx. del bloque {lev.max():.1f}x")
            m = pd.concat([c_carry, c_trend], axis=1).ffill().resample("ME").last().pct_change().dropna()
            print(f"Correlación mensual carry-tendencia: {m.corr().iloc[0,1]:.2f}")
        comb = combine(c_carry, c_trend)
        curves[f"combinada {r_total:.1%}"] = comb
        mm = comb.resample("ME").last().pct_change().dropna()
        rows.append({"riesgo tendencia": f"{r_total:.1%}", **curve_metrics(comb, 365),
                     "meses_pos": (mm > 0).mean(), "peor_mes": mm.min()})
    res = pd.DataFrame(rows)
    pc = lambda x: f"{x:.1%}"
    print("\nCARTERA COMBINADA (80 % carry / 20 % tendencia):")
    print(res.to_string(index=False, formatters={"CAGR": pc, "maxDD": pc, "meses_pos": pc, "peor_mes": pc,
                                                  "sharpe": "{:.2f}".format, "MAR": "{:.2f}".format}))
    ok = res[res.maxDD <= 0.20]
    pick = ok.sort_values("CAGR", ascending=False).iloc[0] if len(ok) else None
    print("\nElección (mayor CAGR con DD ≤ 20 %):", None if pick is None else pick["riesgo tendencia"])
    print("\nRentabilidad por año:")
    print(pd.DataFrame({k: yearly(v) for k, v in curves.items()}).map(pc).to_string())
    pd.DataFrame(curves).to_csv(ROOT / "docs/l07_curvas.csv")
    ep.to_csv(ROOT / "docs/l07_carry_episodios.csv", index=False)
