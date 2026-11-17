"""Lección 16: cartera combinada (carry + S1 + tendencia BTC/ETH). Reglas: docs/leccion_16.md"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import carry, data, lab15, portfolio, trend, universe  # noqa: E402
from leccion_02_pullback import BAR, prepare  # noqa: E402
from leccion_03_tendencia import signals  # noqa: E402
from leccion_06_universo import spot_close  # noqa: E402

OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
START = pd.Timestamp("2020-03-01", tz="UTC")


def sleeve_carry():
    syms = [s for s in OLD if list((ROOT / "data/spot").glob(f"{s}-1h-*.zip"))]
    members = universe.monthly_members(universe.daily_volume(syms), 20)
    perp = {s: data.load(s, "1h")["close"] for s in syms}
    highs = {s: data.load(s, "1h")["high"] for s in syms}
    spot = {s: v for s in syms if (v := spot_close(s)) is not None}
    fund = {s: data.load_funding(s) for s in syms}
    cv, ep = carry.simulate(perp, spot, fund, members, enter=0.00015, exit_=0.00005, max_pos=4, slot=0.25,
                            notional_frac=2 / 3, highs=highs, liq_move=0.45)
    return cv.equity.resample("1D").last().pct_change().dropna(), len(ep), len(syms)


def sleeve_s1():
    d, tk, extra = lab15.s1_relative_weakness(OLD + NEW, K=30)
    return d, len(tk)


def sleeve_trend():
    prep = {s: prepare(s) for s in ["BTCUSDT", "ETHUSDT"]}
    cands = []
    for s, (df, f) in prep.items():
        t = trend.simulate(df, signals(df, 120, 1), 5.0, f, bar=BAR); t["symbol"] = s; cands.append(t)
    tc, tk, _ = portfolio.run(pd.concat(cands, ignore_index=True), {s: df["close"] for s, (df, _) in prep.items()}, 0.05)
    return tc.resample("1D").last().pct_change().dropna(), len(tk)


def stats(r):
    eq = (1 + r).cumprod(); yrs = len(r) / 365.25
    mes = (1 + r).resample("ME").prod() - 1
    return {"Sharpe": r.mean() / r.std() * np.sqrt(365), "CAGR": eq.iloc[-1] ** (1 / yrs) - 1, "DD": (1 - eq / eq.cummax()).max(),
            "peor_mes": mes.min(), "meses+": (mes > 0).mean()}


def combine(R: pd.DataFrame, mode: str):
    vals, val, w = [], 1.0, None
    sub = {k: 1.0 for k in R}
    month = None
    for i, (t, row) in enumerate(R.iterrows()):
        if t.month != month:
            month = t.month
            if mode == "riesgo" and i >= 365:
                vol = R.iloc[i - 365:i].std()
                w = (1 / vol) / (1 / vol).sum()
            else:
                w = pd.Series(1 / R.shape[1], index=R.columns)
            sub = {k: val * w[k] for k in R}
        for k in R:
            sub[k] *= 1 + row[k]
        val = sum(sub.values())
        vals.append((t, val))
    eq = pd.Series(dict(vals))
    return eq.pct_change().fillna(eq.iloc[0] - 1)


if __name__ == "__main__":
    a, n_ep, n_syms = sleeve_carry(); b, n_b = sleeve_s1(); dd, n_d = sleeve_trend()
    R = pd.concat({"A carry": a, "B S1 corto alt/BTC": b, "D tendencia BTC/ETH": dd}, axis=1)
    R = R[R.index >= START].fillna(0.0)
    R.to_csv(ROOT / "docs/l16_bloques_diarios.csv")
    print(f"Bloques: A carry ({n_syms} monedas con spot, {n_ep} episodios) | B S1 ({len(OLD) + len(NEW)} criptos, {n_b} trades) | D tendencia ({n_d} trades)\n")
    pc = lambda x: f"{x:.1%}"
    T = pd.DataFrame({k: stats(R[k]) for k in R}).T
    print("Cada bloque sobre su propio capital:"); print(T.to_string(formatters={"CAGR": pc, "DD": pc, "peor_mes": pc, "meses+": pc, "Sharpe": "{:.2f}".format}))
    print("\nCorrelación de rentabilidades mensuales:"); print(((1 + R).resample("ME").prod() - 1).corr().round(2).to_string())
    rows = {}
    for mode in ["iguales", "riesgo"]:
        rows[f"cartera, pesos {mode}"] = combine(R, mode)
    C = pd.DataFrame(rows)
    print("\nCartera combinada:")
    print(pd.DataFrame({k: stats(C[k]) for k in C}).T.to_string(formatters={"CAGR": pc, "DD": pc, "peor_mes": pc, "meses+": pc, "Sharpe": "{:.2f}".format}))
    best = C["cartera, pesos riesgo"]
    dd0 = stats(best)["DD"]
    lev = 0.20 / dd0
    for L in [lev]:
        s = stats(best * L)
        print(f"\nEscalada a caída máxima histórica del 20 % (factor {L:.2f}x): Sharpe {s['Sharpe']:.2f} | CAGR {s['CAGR']:.1%} | DD {s['DD']:.1%} | peor mes {s['peor_mes']:.1%} | meses + {s['meses+']:.0%}")
        y = (1 + best * L).groupby(best.index.year).prod() - 1
        print("   por año:", {k: f"{v:+.1%}" for k, v in y.items()})
    yb = (1 + R).groupby(R.index.year).prod() - 1
    print("\nPor año y bloque:"); print(yb.map(pc).to_string())
    # pesos medios de la versión de igual riesgo
    vol = R.rolling(365).std(); w = (1 / vol).div((1 / vol).sum(axis=1), axis=0).dropna()
    print("\nPesos medios (igual riesgo):", w.mean().round(2).to_dict(), "| pesos en 2026-10:", w.iloc[-1].round(2).to_dict())
    C.assign(escalada=best * lev).to_csv(ROOT / "docs/l16_cartera_diaria.csv")
