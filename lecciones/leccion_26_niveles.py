"""Lección 26: soportes y resistencias. Reglas: docs/leccion_26.md   (python … desarrollo | examen)"""
import json, sys, warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import levels, universe

def analyse(E, label):
    print(f"\n=== {label}: {E.symbol.nunique()} monedas ===")
    rows = []
    for fam, g in E.groupby("familia"):
        r, p = g[g.tipo == "real"], g[g.tipo == "placebo"]
        res = {"familia": fam, "toques reales": int(r.rebote.notna().sum()), "toques placebo": int(p.rebote.notna().sum())}
        for m in ["rebote", "continua"]:
            # pareado por moneda y mes (clúster) para no exagerar la significación
            cr = r.groupby([r.symbol, r.t.dt.to_period("M")])[m].mean(); cp = p.groupby([p.symbol, p.t.dt.to_period("M")])[m].mean()
            j = pd.concat([cr, cp], axis=1, keys=["r", "p"]).dropna()
            diff = j.r - j.p
            res[f"{m} real"] = r[m].mean(); res[f"{m} placebo"] = p[m].mean()
            res[f"{m} dif."] = diff.mean(); res[f"{m} z"] = diff.mean() / diff.std() * np.sqrt(len(diff))
        rr = r.r.dropna(); res["E rebote (R)"] = rr.mean(); res["t operación"] = rr.mean() / rr.std() * np.sqrt(len(rr))
        g2 = r.dropna(subset=["r"]).groupby(r.t.dt.floor("1D")).r.mean(); res["t por día"] = g2.mean() / g2.std() * np.sqrt(len(g2))
        res["d medio"] = r.d_rel.mean()
        rows.append(res)
    T = pd.DataFrame(rows).set_index("familia")
    pct = lambda x: f"{x:.1%}"
    print(T.to_string(formatters={**{c: pct for c in T if c.startswith(("rebote r", "rebote p", "continua r", "continua p", "d medio"))},
                                  **{c: "{:+.1%}".format for c in T if c.endswith("dif.")}, **{c: "{:+.1f}".format for c in T if c.endswith((" z", "operación", "día"))},
                                  "E rebote (R)": "{:+.3f}".format}))
    return T

if __name__ == "__main__":
    fase = sys.argv[1]
    syms = json.load(open(ROOT / "docs/l11_universo.json"))["todos"] if fase == "desarrollo" else json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    K = 20 if fase == "desarrollo" else 30
    mem = universe.monthly_members(universe.daily_volume(syms), K)
    by = {}
    for m, ss in mem.items():
        for s in ss: by.setdefault(s, set()).add(m)
    jobs = [(s, by[s], i) for i, s in enumerate(sorted(by))]
    with ProcessPoolExecutor(4) as ex:
        parts = [o for r in ex.map(levels.run_coin, jobs) for o in r]
    E = pd.concat(parts, ignore_index=True)
    E["t"] = pd.to_datetime(E.t, utc=True)
    E.to_parquet(ROOT / f"data/cache/l26_{fase}.parquet")
    T = analyse(E, fase.upper())
    T.to_csv(ROOT / f"docs/l26_{fase}.csv")
