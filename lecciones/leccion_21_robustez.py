"""Lección 21: rejillas de robustez (en paralelo). Reglas: docs/leccion_21.md"""
import itertools, json, sys, warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))

OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
NEW30 = json.load(open(ROOT / "docs/l17_nuevas_top30.json"))

def st(d):
    d = d.dropna(); eq = (1 + d).cumprod(); yrs = len(d) / 365.25
    y = (1 + d).groupby(d.index.year).prod() - 1
    return {"sharpe": d.mean() / d.std() * np.sqrt(365), "CAGR": eq.iloc[-1] ** (1 / yrs) - 1, "DD": (1 - eq / eq.cummax()).max(),
            "años_pos": float((y > 0).mean()), "2026": float(y.get(2026, np.nan))}

def job(args):
    kind, p = args
    from sclab import carry, data, lab15, portfolio, trend, universe
    if kind == "A":
        from leccion_16_cartera import OLD as O
        from leccion_06_universo import spot_close
        syms = [s for s in O if list((ROOT / "data/spot").glob(f"{s}-1h-*.zip"))]
        mem = universe.monthly_members(universe.daily_volume(syms), 20)
        cv, ep = carry.simulate({s: data.load(s, "1h")["close"] for s in syms}, {s: v for s in syms if (v := spot_close(s)) is not None},
                                {s: data.load_funding(s) for s in syms}, mem, enter=p[0], exit_=p[1], max_pos=4, slot=0.25,
                                notional_frac=2 / 3, highs={s: data.load(s, "1h")["high"] for s in syms}, liq_move=0.45)
        d = cv.equity.resample("1D").last().pct_change()
    elif kind == "E":
        import leccion_17_caidas as L
        src = open(ROOT / "lecciones/leccion_17_caidas.py").read()
        d, ep, cv = L.r1_reverse_carry(OLD + NEW30, 30, 0.30, realista=True) if p == (0.00015, 0.00005) else _r1(L, p)
    elif kind == "B":
        d, tk, _ = lab15.s1_relative_weakness(OLD + NEW, K=30, N=p[0], m=p[1])
    elif kind == "D":
        from leccion_02_pullback import BAR, prepare
        from leccion_03_tendencia import signals
        prep = {s: prepare(s) for s in ["BTCUSDT", "ETHUSDT"]}
        c = []
        for s, (df, f) in prep.items():
            t = trend.simulate(df, signals(df, p[0], 1), p[1], f, bar=BAR); t["symbol"] = s; c.append(t)
        tc, tk, _ = portfolio.run(pd.concat(c, ignore_index=True), {s: df["close"] for s, (df, _) in prep.items()}, 0.05)
        d = tc.resample("1D").last().pct_change()
    return kind, p, st(d[d.index >= "2020-03-01"])

def _r1(L, p):
    import types
    from sclab import carry
    orig = carry.simulate
    def patched(*a, **k):
        k["enter"], k["exit_"] = p
        return orig(*a, **k)
    carry.simulate = patched
    try:
        return L.r1_reverse_carry(OLD + NEW30, 30, 0.30, realista=True)
    finally:
        carry.simulate = orig

if __name__ == "__main__":
    cg = list(itertools.product([0.0001, 0.00015, 0.0002, 0.0003], [0.0, 0.00005, 0.0001]))
    tg = list(itertools.product([60, 90, 120, 180, 240], [3.0, 4.0, 5.0, 6.0]))
    jobs = [("D", p) for p in tg] + [("A", p) for p in cg] + [("B", p) for p in tg] + [("E", p) for p in cg]
    rows = []
    with ProcessPoolExecutor(4) as ex:
        for kind, p, s in ex.map(job, jobs):
            rows.append({"pieza": kind, "p1": p[0], "p2": p[1], **s})
            print(kind, p, {k: round(v, 3) for k, v in s.items()}, flush=True)
            pd.DataFrame(rows).to_csv(ROOT / "docs/l21_rejillas.csv", index=False)
