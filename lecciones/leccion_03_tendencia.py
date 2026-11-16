"""Lección 3: seguimiento de tendencia (ruptura Donchian + stop chandelier). Reglas: docs/leccion_03.md

  python lecciones/leccion_03_tendencia.py diseno
  python lecciones/leccion_03_tendencia.py validacion   # una sola vez, con params congelados
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import swing, trend  # noqa: E402
from leccion_02_pullback import SYMBOLS, IS_END, BAR, prepare  # noqa: E402

GRID = {"N": [30, 60, 120, 180], "m": [2.0, 3.0, 4.0, 5.0]}
FROZEN = ROOT / "docs" / "l03_parametros_congelados.json"
st = lambda r: pd.Series(swing.stats(r))


def fmt(df, index=False):
    return df.to_string(index=index, float_format=lambda x: f"{x:.3f}")


def signals(df, N, d):
    if d == 1:
        s = (df["trend"] > 0) & (df["close"] > df["high"].rolling(N).max().shift(1))
    else:
        s = (df["trend"] < 0) & (df["close"] < df["low"].rolling(N).min().shift(1))
    return s.to_numpy().astype(int) * d


def run_all(prep, N, m, d, period, seed=None, partial=None):
    out = []
    for sym, (df, fund) in prep.items():
        sub = df[df.index < IS_END] if period == "IS" else df[df.index >= IS_END]
        side = signals(sub, N, d)
        if seed is not None:
            rng = np.random.default_rng(seed * 100 + SYMBOLS.index(sym))
            pool = np.flatnonzero(sub["trend"].to_numpy() * d > 0)
            k = int((side != 0).sum())
            side = np.zeros(len(sub), int)
            side[rng.choice(pool, size=min(k, len(pool)), replace=False)] = d
        t = trend.simulate(sub, side, m, fund, bar=BAR, partial=partial)
        t["symbol"] = sym
        out.append(t)
    return pd.concat(out, ignore_index=True)


def report(t, ctrl, part):
    print(fmt(pd.DataFrame([{"serie": "estrategia", **swing.stats(t.r_net)},
                            {"serie": "control (azar en tendencia)", **swing.stats(ctrl.r_net)},
                            {"serie": "variante 50% en +1R", **swing.stats(part.r_net)}])))
    t = t.assign(year=t.signal_time.dt.year)
    print("Por año:"); print(fmt(t.groupby("year").r_net.apply(st).unstack(), True))
    print("Por activo:"); print(fmt(t.groupby("symbol").r_net.apply(st).unstack(), True))
    q = t.r_net.quantile([.1, .5, .9]).round(2).to_dict()
    print(f"Duración mediana: {t.bars.median()*4/24:.1f} días | R percentiles 10/50/90: {q} | "
          f"mejor trade {t.r_net.max():.1f}R | peor {t.r_net.min():.1f}R")
    top = t.r_net.sort_values(ascending=False)
    print(f"Dependencia de los grandes: el 10 % mejor de trades aporta {top.head(len(t)//10).sum():.0f}R "
          f"de un total de {t.r_net.sum():.0f}R")


def diseno(prep):
    chosen = {}
    for d, name in [(1, "LARGOS"), (-1, "CORTOS")]:
        rows = []
        for N, m in itertools.product(*GRID.values()):
            rows.append({"N": N, "m": m, **swing.stats(run_all(prep, N, m, d, "IS").r_net)})
        g = pd.DataFrame(rows)
        def neigh(r):
            ok = np.ones(len(g), bool)
            for k, vals in GRID.items():
                p = vals.index(r[k]); ok &= g[k].isin(vals[max(0, p-1):p+2]).to_numpy()
            return g.loc[ok, "E_R"].mean()
        g["E_vecinas"] = g.apply(neigh, axis=1)
        g.to_csv(ROOT / f"docs/l03_rejilla_{name.lower()}.csv", index=False)
        print(f"\n=== {name} EN MUESTRA (2020-2023) ===")
        print(f"Combinaciones con E neta > 0: {(g.E_R > 0).sum()} / {len(g)}")
        print("E neta (filas N, columnas m):"); print(g.pivot(index="N", columns="m", values="E_R").round(3).to_string())
        print("PF:"); print(g.pivot(index="N", columns="m", values="PF").round(2).to_string())
        print("Win rate:"); print(g.pivot(index="N", columns="m", values="win_rate").round(2).to_string())
        print("Trades:"); print(g.pivot(index="N", columns="m", values="trades").to_string())
        b = g[g.trades >= 300].sort_values("E_vecinas", ascending=False).iloc[0]
        N, m = int(b.N), float(b.m)
        print(f"Elegida: N={N}, m={m}")
        t = run_all(prep, N, m, d, "IS")
        ctrl = pd.concat([run_all(prep, N, m, d, "IS", seed=s) for s in range(5)])
        part = run_all(prep, N, m, d, "IS", partial=(0.5, 1.0))
        report(t, ctrl, part)
        chosen[name] = {"N": N, "m": m}
    return chosen


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else "diseno"
    prep = {s: prepare(s) for s in SYMBOLS}
    if fase == "diseno":
        c = diseno(prep)
        print("\nCandidatos (aún NO congelados):", c)
        json.dump(c, open(ROOT / "docs/l03_parametros_candidatos.json", "w"), indent=1)
    else:
        for name, p in json.load(open(FROZEN)).items():
            d = 1 if name == "LARGOS" else -1
            t = run_all(prep, p["N"], p["m"], d, "OOS")
            ctrl = pd.concat([run_all(prep, p["N"], p["m"], d, "OOS", seed=s) for s in range(5)])
            part = run_all(prep, p["N"], p["m"], d, "OOS", partial=(0.5, 1.0))
            print(f"\n=== {name} FUERA DE MUESTRA (2024-01 → 2026-10) {p} ===")
            report(t, ctrl, part)
            t.to_csv(ROOT / f"docs/l03_oos_trades_{name.lower()}.csv", index=False)
