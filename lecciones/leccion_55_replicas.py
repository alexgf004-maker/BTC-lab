"""Lección 55 — Réplicas en los puestos 31–100 (R1 capitulación spot, R2 bloque J, R3 doble techo) y momentum intradía (R4).
Reglas en docs/leccion_55.md. Uso: python3 lecciones/leccion_55_replicas.py [R1|R2|R3|R4]..."""
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones")); sys.path.insert(0, str(ROOT / "sclab"))
from sclab import data, lab15, universe  # noqa: E402
from rangos import monthly_rank_members  # noqa: E402

UTC = lambda s: pd.Timestamp(s, tz="UTC")
H1 = pd.Timedelta("1h")
EXTRA = 2 * (0.0010 - 0.0007)                                            # coste adicional por operación en R1–R3
PER = (("desarrollo", ("2020-01-01", "2023-01-01")), ("examen", ("2023-01-01", "2026-11-01")))


def tcl(r, t):
    if len(r) < 3:
        return float("nan")
    u = r - r.mean()
    g = u.groupby(pd.DatetimeIndex(t).tz_localize(None).to_period("W").values).sum()
    se = np.sqrt((g ** 2).sum()) / len(r)
    return r.mean() / se if se > 0 else float("nan")


def report(name, rows):
    T = pd.DataFrame(rows, columns=["t", "r"])
    line = f"  {name:44s}"
    for lab, (a, b) in PER:
        X = T[(T.t >= UTC(a)) & (T.t < UTC(b))]
        line += f" | {lab}: n {len(X):5d}, {100 * X.r.mean():+.3f} %, t {tcl(X.r, X.t):+.2f}, acierto {100 * (X.r > 0).mean():.0f} %"
    print(line + f" | total t {tcl(T.r, T.t):+.2f}", flush=True)


def mem31():
    return monthly_rank_members(pd.read_parquet(ROOT / "data" / "vol_diario.parquet"), 30, 100)


def funding(sym):
    try:
        return lab15._funding(sym)
    except Exception:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))


def fsum(f, a, b):
    return float(f[(f.index > a) & (f.index <= b)].sum()) if len(f) else 0.0


# ------------------------------------------------------------------------------------------------ R1
def job_R1(args):
    sym, mem = args
    from l50_dl import base
    sp = ROOT / "data" / "spot1h" / f"{base(sym)}USDT.parquet"
    if not sp.exists():
        return []
    h = data.load(sym, "1h")
    tr = np.maximum(h.high - h.low, np.maximum((h.high - h.close.shift()).abs(), (h.low - h.close.shift()).abs()))
    h = h.assign(atr=tr.rolling(24).mean()); h.index = h.index + H1
    s = pd.read_parquet(sp)["quote_volume"]; s.index = s.index + H1
    sv = s[~s.index.duplicated()].reindex(h.index).fillna(0)
    S = sv.rolling(24).sum() / (sv.rolling(24).sum() + h.quote_volume.rolling(24).sum())
    z = ((S - S.rolling(1440, min_periods=720).mean().shift(1)) / S.rolling(1440, min_periods=720).std().shift(1)).to_numpy()
    lo7 = h.low.shift(1).rolling(168).min().to_numpy()
    o, hi, lo, c, atr = (h[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    fu = funding(sym)
    inmem = universe.is_member(mem, sym, h.index - H1)
    cand = (z >= 1.5) & (c < lo7) & inmem
    rows, i, n = [], 0, len(h)
    while i < n - 1:
        if not cand[i] or not (atr[i] > 0):
            i += 1; continue
        e, A = c[i], atr[i]; stop = e - 3 * A; hmax = e; run = 0; x = None
        for k in range(i + 1, min(i + 121, n)):
            if lo[k] <= stop:
                x = min(o[k], stop); break
            hmax = max(hmax, hi[k]); stop = max(stop, hmax - 2.5 * A)
            run = run + 1 if z[k] <= 0 else 0
            if run >= 12:
                x = c[k]; break
        if x is None:
            k = min(i + 120, n - 1); x = c[k]
        rows.append((h.index[i], x / e - 1 - 2 * 0.0007 - EXTRA - fsum(fu, h.index[i], h.index[k])))
        i = k + 1
    return rows


def run_R1():
    mem = mem31()
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_R1, [(s, mem) for s in syms]))
    print(f"\n=== R1 — Capitulación con volumen spot → largo (puestos 31–100; {sum(1 for r in res if r)} monedas con señales)")
    report("R1 capitulación spot (largo)", [x for r in res for x in r])


# ------------------------------------------------------------------------------------------------ R2
def job_R2(args):
    import leccion_54_stop_j as L54
    rows = L54.job(args)
    return [(t, r - EXTRA) for v, t, r, d in rows if v == L54.VARS[1]]


def run_R2():
    mem = mem31()
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_R2, [(s, mem) for s in syms]))
    print("\n=== R2 — Bloque J actual (ruptura falsa de redondos, stop 2 ATR) en los puestos 31–100")
    report("R2 bloque J", [x for r in res for x in r])


# ------------------------------------------------------------------------------------------------ R3
def job_R3(args):
    from leccion_52_chartistas import AGG, trades
    sym, mem = args
    try:
        df = data.load(sym, "1h").resample("4h").agg(AGG).dropna()
    except Exception:
        return []
    member = universe.is_member(mem, sym, df.index)
    if not member.any():
        return []
    return [(t, net - EXTRA + 2 * 0.0007 - 2 * 0.0007) for name, t, net, R in trades(df, 0.0007, funding(sym), member) if name == "doble techo"]


def run_R3():
    mem = mem31()
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_R3, [(s, mem) for s in syms]))
    print("\n=== R3 — Doble techo (corto) en los puestos 31–100")
    report("R3 doble techo", [x for r in res for x in r])


# ------------------------------------------------------------------------------------------------ R4
def run_R4():
    print("\n=== R4 — Momentum intradía en BTC y ETH (la primera hora marca la dirección de la última)")
    for lab, h0, h1 in (("R4 día UTC (00–01 → 23–24)", 0, 23), ("R4b sesión EE. UU. (14–15 → 20–21)", 14, 20),
                        ("placebo (12–13 → 23–24)", 12, 23)):
        rows = []
        for s in ("BTCUSDT", "ETHUSDT"):
            h = data.load(s, "1h")
            fu = funding(s)
            r = h.close / h.open - 1
            first = r[r.index.hour == h0]; last = r[r.index.hour == h1]
            first.index = first.index.floor("1D"); last.index = last.index.floor("1D")
            j = pd.concat([first, last], axis=1, keys=["a", "b"]).dropna()
            for d, (a, b) in j.iterrows():
                if a == 0:
                    continue
                side = np.sign(a); t0 = d + h1 * H1
                rows.append((t0, side * b - 2 * 0.0007 - side * fsum(fu, t0, t0 + H1)))
        report(lab, rows)


if __name__ == "__main__":
    for x in (sys.argv[1:] or ["R4", "R2", "R3", "R1"]):
        {"R1": run_R1, "R2": run_R2, "R3": run_R3, "R4": run_R4}[x]()
