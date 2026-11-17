"""Lección 22: cartera de conjunto, descuento por degradación y remuestreo por bloques. Reglas: docs/leccion_22.md"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent

def st(r):
    eq = (1 + r).cumprod(); yrs = len(r) / 365.25; m = (1 + r).resample("ME").prod() - 1
    return {"Sharpe": r.mean() / r.std() * np.sqrt(365), "CAGR": eq.iloc[-1] ** (1 / yrs) - 1, "DD": (1 - eq / eq.cummax()).max(),
            "peor_mes": m.min(), "meses+": (m > 0).mean()}

def monthly_rebalanced(R):
    vals, val, month, sub = [], 1.0, None, None
    for t, row in R.iterrows():
        if t.month != month:
            month = t.month; sub = {k: val / R.shape[1] for k in R}
        for k in R: sub[k] *= 1 + row[k]
        val = sum(sub.values()); vals.append((t, val))
    e = pd.Series(dict(vals)); return e.pct_change().fillna(e.iloc[0] - 1)

def haircut(r):
    """Resta un rendimiento constante que deja el Sharpe en la mitad."""
    return r - r.mean() / 2

def bootstrap(r, years, lev, n=10000, block=90, seed=0):
    rng = np.random.default_rng(seed); x = r.to_numpy() * lev; L = int(365 * years)
    nb = int(np.ceil(L / block)); starts = rng.integers(0, len(x) - block, size=(n, nb))
    paths = np.stack([np.concatenate([x[s:s + block] for s in row])[:L] for row in starts])
    eq = np.cumprod(1 + paths, axis=1); dd = (1 - eq / np.maximum.accumulate(eq, axis=1)).max(axis=1); fin = eq[:, -1] - 1
    return {"mediana": np.median(fin), "p5": np.percentile(fin, 5), "p95": np.percentile(fin, 95), "P(perder)": (fin < 0).mean(),
            "P(DD>20%)": (dd > 0.2).mean(), "P(DD>30%)": (dd > 0.3).mean(), "DD_mediana": np.median(dd)}

if __name__ == "__main__":
    pc = lambda v: f"{v:+.1%}"
    R = pd.read_csv(ROOT / "docs/l17_bloques_diarios.csv", index_col=0, parse_dates=True)
    C = pd.read_csv(ROOT / "docs/l22_combinaciones_diarias.csv", index_col=0, parse_dates=True).reindex(R.index).fillna(0)
    R["B S1 (conjunto de 20)"] = C[[c for c in C if c.startswith("B_")]].mean(axis=1)
    R["D tendencia (conjunto de 20)"] = C[[c for c in C if c.startswith("D_")]].mean(axis=1)
    print("BLOQUES (sobre su propio capital):")
    print(pd.DataFrame({k: st(R[k]) for k in R}).T.to_string(formatters={"CAGR": pc, "DD": pc, "peor_mes": pc, "meses+": "{:.0%}".format, "Sharpe": "{:.2f}".format}))
    P_orig = monthly_rebalanced(R[["A carry", "E carry inverso", "B S1 corto alt/BTC", "D tendencia BTC/ETH"]])
    P_ens = monthly_rebalanced(R[["A carry", "E carry inverso", "B S1 (conjunto de 20)", "D tendencia (conjunto de 20)"]])
    blocks = ["A carry", "E carry inverso", "B S1 (conjunto de 20)", "D tendencia (conjunto de 20)"]
    P_hc = monthly_rebalanced(pd.DataFrame({k: haircut(R[k]) for k in blocks}))
    carteras = {"Cartera original (parámetros elegidos)": P_orig, "Cartera de conjunto": P_ens, "Cartera de conjunto CON DESCUENTO (Sharpe de cada bloque / 2)": P_hc}
    print("\nCARTERAS (1/4 por bloque, reequilibrio mensual):")
    print(pd.DataFrame({k: st(v) for k, v in carteras.items()}).T.to_string(formatters={"CAGR": pc, "DD": pc, "peor_mes": pc, "meses+": "{:.0%}".format, "Sharpe": "{:.2f}".format}))
    print("\nPor año:"); print(pd.DataFrame({k[:28]: (1 + v).groupby(v.index.year).prod() - 1 for k, v in carteras.items()}).map(pc).to_string())
    print("\nREMUESTREO POR BLOQUES DE 3 MESES (10 000 caminos)")
    rows = []
    for nm, r in [("conjunto", P_ens), ("conjunto con descuento", P_hc)]:
        for lev in [1.0, 1.5, 2.0, 3.0]:
            for yrs in [1, 3]:
                b = bootstrap(r, yrs, lev); rows.append({"escenario": nm, "apal.": f"{lev:g}x", "años": yrs, **b})
    B = pd.DataFrame(rows)
    print(B.to_string(index=False, formatters={k: pc for k in ["mediana", "p5", "p95"]} | {k: "{:.1%}".format for k in ["P(perder)", "P(DD>20%)", "P(DD>30%)", "DD_mediana"]}))
    ok = B[(B.escenario == "conjunto con descuento") & (B.años == 3) & (B["P(DD>30%)"] <= 0.05)]
    print("\nRECOMENDACIÓN (mayor apalancamiento con P(caída > 30 % en 3 años) ≤ 5 % en el escenario con descuento):",
          ok["apal."].iloc[-1] if len(ok) else "ninguno")
    pd.DataFrame(carteras).to_csv(ROOT / "docs/l22_carteras_diarias.csv")
