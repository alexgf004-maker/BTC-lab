"""Lección 4: cartera, límites de riesgo y walk-forward. Reglas: docs/leccion_04.md"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import portfolio, swing, trend  # noqa: E402
from leccion_02_pullback import SYMBOLS, IS_END, BAR, prepare  # noqa: E402
from leccion_03_tendencia import GRID, signals  # noqa: E402

N, M = 120, 5.0
pct = lambda x: f"{x:.0%}"


def candidates(prep, N, m, end=None):
    out = []
    for s, (df, fund) in prep.items():
        sub = df if end is None else df[df.index < end]
        t = trend.simulate(sub, signals(sub, N, 1), m, fund, bar=BAR, one_at_a_time=False)
        t["symbol"] = s
        out.append(t)
    return pd.concat(out, ignore_index=True)


def table(rows):
    df = pd.DataFrame(rows)
    f = {c: pct for c in ["CAGR", "maxDD", "peor_mes", "meses_pos", "CAGR_p50", "CAGR_p5", "DD_p50", "DD_p95", "P(perder 3a)"]}
    f.update({"final_x": lambda x: f"{x:.1f}x", "lev_max": lambda x: f"{x:.1f}x"})
    return df.to_string(index=False, formatters=f)


if __name__ == "__main__":
    prep = {s: prepare(s) for s in SYMBOLS}
    closes = {s: df["close"] for s, (df, _) in prep.items()}
    cands = candidates(prep, N, M)
    print(f"Señales candidatas: {len(cands)}")

    # 0) cordura: con K ilimitado y sin corta-circuitos, la cartera debe tomar los trades de la Lección 3
    _, tk, _ = portfolio.run(cands, closes, 0.01, K=99)
    print(f"Cordura: trades tomados {len(tk)}, E {tk.r_net.mean():.3f}R, PF {swing.stats(tk.r_net)['PF']:.2f}")

    for label, start in [("PERIODO COMPLETO 2020-2026 (2020-23 en muestra)", None), ("SOLO FUERA DE MUESTRA 2024-2026", IS_END)]:
        c = cands if start is None else cands[cands.entry_time >= start]
        cl = closes if start is None else {s: v[v.index >= start] for s, v in closes.items()}
        rows = []
        for risk, K, br in itertools.product([0.01, 0.02, 0.03], [10, 5, 3], [False, True]):
            curve, tk, lev = portfolio.run(c, cl, risk, K, br)
            rows.append({"riesgo": pct(risk), "K": K, "frenos": "sí" if br else "no", "trades": len(tk),
                         **portfolio.metrics(curve, lev), **portfolio.block_bootstrap(curve, n=4000)})
        print(f"\n=== {label} ===")
        print(table(rows))
        pd.DataFrame(rows).to_csv(ROOT / f"docs/l04_cartera_{'oos' if start else 'todo'}.csv", index=False)

    # Walk-forward con ventana creciente
    print("\n=== WALK-FORWARD (ventana creciente; elección con la regla de vecinas) ===")
    wf = []
    for Y in range(2022, 2027):
        cut = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        years = (cut - pd.Timestamp("2020-01-01", tz="UTC")).days / 365.25
        g = []
        for n_, m_ in itertools.product(*GRID.values()):
            t = candidates(prep, n_, m_, end=cut)
            _, tk, _ = portfolio.run(t, {s: v[v.index < cut] for s, v in closes.items()}, 0.01, K=99)
            g.append({"N": n_, "m": m_, **swing.stats(tk.r_net)})
        g = pd.DataFrame(g)
        def neigh(r):
            ok = np.ones(len(g), bool)
            for k, vals in GRID.items():
                p = vals.index(r[k]); ok &= g[k].isin(vals[max(0, p-1):p+2]).to_numpy()
            return g.loc[ok, "E_R"].mean()
        g["Ev"] = g.apply(neigh, axis=1)
        b = g[g.trades >= 30 * years].sort_values("Ev", ascending=False).iloc[0]
        t = candidates(prep, int(b.N), float(b.m))
        _, tk, _ = portfolio.run(t, closes, 0.01, K=99)
        tk = tk[(tk.entry_time >= cut) & (tk.entry_time < pd.Timestamp(f"{Y+1}-01-01", tz="UTC"))]
        wf.append(tk.assign(year=Y))
        print(f"{Y}: elegidos N={int(b.N)}, m={b.m} con datos hasta {Y-1} -> {swing.stats(tk.r_net)}")
    wf = pd.concat(wf)
    print("Encadenado 2022-2026:", swing.stats(wf.r_net))
