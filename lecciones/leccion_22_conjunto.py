"""Lección 22: series diarias de las 20 combinaciones de B (S1) y D (tendencia) para la cartera de conjunto."""
import itertools, json, sys, warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import pandas as pd
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]

def job(a):
    kind, (N, m) = a
    from sclab import lab15, portfolio, trend
    if kind == "B":
        d, _, _ = lab15.s1_relative_weakness(OLD + NEW, K=30, N=N, m=m)
    else:
        from leccion_02_pullback import BAR, prepare
        from leccion_03_tendencia import signals
        prep = {s: prepare(s) for s in ["BTCUSDT", "ETHUSDT"]}; c = []
        for s, (df, f) in prep.items():
            t = trend.simulate(df, signals(df, N, 1), m, f, bar=BAR); t["symbol"] = s; c.append(t)
        tc, _, _ = portfolio.run(pd.concat(c, ignore_index=True), {s: df["close"] for s, (df, _) in prep.items()}, 0.05)
        d = tc.resample("1D").last().pct_change()
    return f"{kind}_{N}_{m:g}", d

if __name__ == "__main__":
    g = list(itertools.product([60, 90, 120, 180, 240], [3.0, 4.0, 5.0, 6.0]))
    out = {}
    with ProcessPoolExecutor(4) as ex:
        for k, d in ex.map(job, [("D", p) for p in g] + [("B", p) for p in g]):
            out[k] = d; print(k, flush=True)
    pd.DataFrame(out).to_csv(ROOT / "docs/l22_combinaciones_diarias.csv")
