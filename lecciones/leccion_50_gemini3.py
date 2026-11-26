"""Lección 50 — Tercera tanda de Gemini: P (PAXG fin de semana), T (fuga de TVL real), W (líderes congestionados),
S (ruptura liderada por spot). Reglas en docs/leccion_50.md. Uso: python3 lecciones/leccion_50_gemini3.py [P|T|W|S]..."""
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "sclab"))
from sclab import data, lab15, universe  # noqa: E402
from l50_dl import CHAINS, PROTOS, base  # noqa: E402

UTC = lambda s: pd.Timestamp(s, tz="UTC")
H1 = pd.Timedelta("1h")
PERP, SPOT_COST = 0.0007, 0.0012


def tcl(r, t):
    if len(r) < 3:
        return float("nan")
    u = r - r.mean()
    g = u.groupby(pd.DatetimeIndex(t).tz_localize(None).to_period("W").values).sum()
    se = np.sqrt((g ** 2).sum()) / len(r)
    return r.mean() / se if se > 0 else float("nan")


def report(name, rows, periods):
    T = pd.DataFrame(rows, columns=["t", "r"])
    line = f"  {name:42s}"
    for lab, (a, b) in periods:
        X = T[(T.t >= UTC(a)) & (T.t < UTC(b))]
        line += f" | {lab}: n {len(X):4d}, media {100 * X.r.mean():+.3f} %, t {tcl(X.r, X.t):+.2f}"
    print(line + f" | total t {tcl(T.r, T.t):+.2f}", flush=True)


def members():
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    return universe.monthly_members(vol, 30)


def fsum(f, a, b):
    return float(f[(f.index > a) & (f.index <= b)].sum()) if len(f) else 0.0


def funding(sym):
    try:
        return lab15._funding(sym)
    except Exception:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))


# ------------------------------------------------------------------------------------------------ P · PAXG
def run_P():
    s = pd.read_parquet(ROOT / "data" / "spot1h" / "PAXGUSDT.parquet")["close"]
    px = s.copy(); px.index = px.index + H1                              # índice = hora de cierre
    print("\n=== P — Reversión del fin de semana en PAXG (spot)")
    for lab, d0, d1, dx in (("señal (vie 20:00 → dom 20:00)", 4, 6, 18), ("placebo (mar 20:00 → jue 20:00)", 1, 3, 18)):
        anchors = [t for t in px.index if t.dayofweek == d0 and t.hour == 20]
        hist, rows = [], []
        for t0 in anchors:
            t1 = t0 + pd.Timedelta(days=d1 - d0)
            if t1 not in px.index:
                continue
            R = px[t1] / px[t0] - 1
            sig = np.std(hist[-20:], ddof=1) if len(hist) >= 20 else np.nan
            hist.append(R)
            if not (sig == sig) or abs(R) < max(0.008, 1.5 * sig):
                continue
            side = -np.sign(R); e = px[t1]; stp = min(1.5 * abs(R), 0.025)
            path = px[(px.index > t1) & (px.index <= t1 + pd.Timedelta(hours=dx))]
            x, tx = (path.iloc[-1], path.index[-1]) if len(path) else (e, t1)
            for t, p in path.items():
                if side * (p / e - 1) <= -stp:
                    x, tx = p, t; break
                if (side > 0 and p >= px[t0]) or (side < 0 and p <= px[t0]):
                    x, tx = px[t0], t; break
            hrs = (tx - t1) / H1
            r = side * (x / e - 1) - 2 * SPOT_COST - (0.10 * hrs / 8760 if side < 0 else 0)
            rows.append((t1, r))
        report(lab, rows, (("desarrollo", ("2020-09-01", "2023-01-01")), ("examen", ("2023-01-01", "2026-11-01"))))


# ------------------------------------------------------------------------------------------------ T · fuga de TVL real
def perp_sym(tok, vol_cols):
    for c in (f"{tok}USDT", f"1000{tok}USDT"):
        if c in vol_cols:
            return c
    return None


def job_T(args):
    tok, mem, cols = args
    sym = perp_sym(tok, cols)
    f = ROOT / "data" / "tvl" / f"{tok}.parquet"
    if sym is None or not f.exists():
        return {}
    tv = pd.read_parquet(f)["tvl"]; tv.index = tv.index.floor("1D")
    tv = tv[~tv.index.duplicated(keep="last")]
    h = data.load(sym, "1h")
    d = h.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    tvd = tv.reindex(d.index).ffill(limit=3)
    real = np.log(tvd / d.close)
    dR = real - real.shift(14)
    sma = d.close.rolling(30).mean()
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    fu = funding(sym)
    o, hi, lo, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    out = {"señal (TVL real −10 % en 14 días)": [], "placebo (TVL real ≥ 0)": []}
    for key, cond in (("señal (TVL real −10 % en 14 días)", dR <= -0.10), ("placebo (TVL real ≥ 0)", dR >= 0)):
        cand = (cond & (d.close < sma)).to_numpy()
        i, n = 0, len(d)
        while i < n - 1:
            t = d.index[i] + pd.Timedelta("1D")                          # 00:00 del día siguiente (datos del día i)
            if not cand[i] or not universe.is_member(mem, sym, pd.DatetimeIndex([t]))[0] or not (atr.iloc[i] > 0):
                i += 1; continue
            f7 = fu[(fu.index > t - pd.Timedelta("7D")) & (fu.index <= t)].mean() if len(fu) else 0.0
            if f7 == f7 and f7 <= -0.0005:
                i += 1; continue
            e = c[i]; A = atr.iloc[i]; stop = min(e + 3 * A, 1.12 * e); low_min = e
            x, k = None, i
            for k in range(i + 1, n):
                if hi[k] >= stop:
                    x = max(o[k], stop); break
                low_min = min(low_min, lo[k]); stop = min(stop, low_min + 3 * A)
                if (dR.iloc[k] >= 0) or (c[k] > sma.iloc[k]) or (k - i >= 21):
                    x = c[k]; break
            if x is None:
                x, k = c[n - 1], n - 1
            r = -(x / e - 1) - 2 * PERP + fsum(fu, t, d.index[k] + pd.Timedelta("1D"))
            out[key].append((t, r))
            i = k + 1
    return out


def run_T():
    mem = members()
    cols = set(pd.read_parquet(ROOT / "data" / "vol_diario.parquet").columns)
    toks = sorted(set(CHAINS) | set(PROTOS))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_T, [(t, mem, cols) for t in toks]))
    print("\n=== T — Fuga de TVL real → corto")
    for key in ("señal (TVL real −10 % en 14 días)", "placebo (TVL real ≥ 0)"):
        report(key, [x for r in res for x in r.get(key, [])], (("desarrollo", ("2020-01-01", "2023-01-01")), ("examen", ("2023-01-01", "2026-11-01"))))


# ------------------------------------------------------------------------------------------------ simulador horario de cortos (W y S)
def short_sim(h, i, A, exit_fn, max_bars):
    o, hi, lo, c = (h[k].to_numpy() for k in ("open", "high", "low", "close"))
    e = c[i]; stop = e + 3 * A; low_min = e
    n = len(h)
    for k in range(i + 1, min(i + max_bars + 1, n)):
        if hi[k] >= stop:
            return k, max(o[k], stop)
        low_min = min(low_min, lo[k]); stop = min(stop, low_min + 2.5 * A)
        if exit_fn(k):
            return k, c[k]
    k = min(i + max_bars, n - 1)
    return k, c[k]


def hourly(sym):
    h = data.load(sym, "1h")
    tr = np.maximum(h.high - h.low, np.maximum((h.high - h.close.shift()).abs(), (h.low - h.close.shift()).abs()))
    h = h.assign(atr=tr.rolling(24).mean())
    h.index = h.index + H1                                              # índice = cierre de la vela (momento de decisión)
    return h


# ------------------------------------------------------------------------------------------------ W · líderes congestionados
def run_W():
    mem = members()
    syms = sorted(set().union(*mem.values()))
    C, OI, FU = {}, {}, {}
    for s in syms:
        fm = ROOT / "data" / "metrics" / f"{s}.parquet"
        if not fm.exists():
            continue
        try:
            C[s] = data.load(s, "1h")["close"]
        except Exception:
            continue
        oi = pd.read_parquet(fm, columns=["sum_open_interest"])["sum_open_interest"]; oi.index = oi.index + H1
        OI[s] = oi[~oi.index.duplicated(keep="last")].sort_index(); FU[s] = funding(s)
    Cd = pd.DataFrame(C); Cd.index = Cd.index + H1
    days = pd.date_range(UTC("2021-01-01"), UTC("2026-10-31"), freq="1D")
    watch = {"señal (largos congestionados)": {}, "placebo (sin congestión)": {}}
    for t in days:
        uni = [s for s in mem.get(pd.Timestamp(t.year, t.month, 1, tz="UTC"), set()) if s in Cd]
        if t not in Cd.index or t - pd.Timedelta("14D") not in Cd.index:
            continue
        r14 = (Cd.loc[t, uni] / Cd.loc[t - pd.Timedelta("14D"), uni] - 1).dropna()
        if len(r14) < 15:
            continue
        top = r14[r14 >= r14.quantile(2 / 3)]
        for s in top.index:
            oi = OI[s]
            a, b = oi.asof(t - pd.Timedelta("14D")), oi.asof(t)
            if not (a and b and a > 0):
                continue
            doi = b / a - 1
            f = FU[s]; f7 = f[(f.index > t - pd.Timedelta("7D")) & (f.index <= t)].mean() if len(f) else np.nan
            if top[s] > 0.10 and doi > 0.25 and f7 > 0.00015:
                watch["señal (largos congestionados)"].setdefault(s, set()).add(t)
            if doi <= 0 and f7 <= 0.0001:
                watch["placebo (sin congestión)"].setdefault(s, set()).add(t)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_W, [(s, {k: v.get(s, set()) for k, v in watch.items()}) for s in syms if s in OI]))
    print("\n=== W — Líderes congestionados que pierden soporte → corto")
    for key in watch:
        report(key, [x for r in res for x in r.get(key, [])], (("desarrollo", ("2020-01-01", "2024-01-01")), ("examen", ("2024-01-01", "2026-11-01"))))


def job_W(args):
    sym, wl = args
    h = hourly(sym)
    oi = pd.read_parquet(ROOT / "data" / "metrics" / f"{sym}.parquet", columns=["sum_open_interest"])["sum_open_interest"]
    oi.index = oi.index + H1; oi = oi[~oi.index.duplicated(keep="last")].sort_index()
    oi = oi.reindex(h.index, method="ffill").to_numpy()
    vw = (h.quote_volume.rolling(168).sum() / h.volume.rolling(168).sum()).to_numpy()
    lo48 = h.low.shift(1).rolling(48).min().to_numpy()
    c, atr = h.close.to_numpy(), h.atr.to_numpy()
    fu = funding(sym)
    day = h.index.floor("1D") - pd.Timedelta(0)
    out = {}
    for key, days in wl.items():
        rows, i, n = [], 0, len(h)
        if not days:
            out[key] = rows; continue
        on = np.array([(t - H1).floor("1D") in days for t in h.index])  # vigilancia fijada a las 00:00 de ese día
        cand = on & (c < vw) & (c < lo48)
        while i < n - 1:
            if not cand[i] or not (atr[i] > 0):
                i += 1; continue
            oi0 = oi[i]
            k, x = short_sim(h, i, atr[i], lambda k: oi0 == oi0 and oi[k] <= 0.8 * oi0, 168)
            rows.append((h.index[i], -(x / c[i] - 1) - 2 * PERP + fsum(fu, h.index[i], h.index[k])))
            i = k + 1
        out[key] = rows
    return out


# ------------------------------------------------------------------------------------------------ S · ruptura liderada por spot
def job_S(args):
    sym, mem = args
    sp = ROOT / "data" / "spot1h" / f"{base(sym)}USDT.parquet"
    if not sp.exists():
        return {}
    h = hourly(sym)
    s = pd.read_parquet(sp)["quote_volume"]; s.index = s.index + H1
    sv = s.reindex(h.index).fillna(0)
    S = sv.rolling(24).sum() / (sv.rolling(24).sum() + h.quote_volume.rolling(24).sum())
    z = ((S - S.rolling(1440, min_periods=720).mean().shift(1)) / S.rolling(1440, min_periods=720).std().shift(1)).to_numpy()
    lo7 = h.low.shift(1).rolling(168).min().to_numpy()
    c, atr = h.close.to_numpy(), h.atr.to_numpy()
    fu = funding(sym)
    f24 = fu.rolling("24h").mean().reindex(h.index, method="ffill").to_numpy() if len(fu) else np.zeros(len(h))
    inmem = universe.is_member(mem, sym, h.index - H1)
    bad = np.zeros(len(h), bool)
    if sym == "BTCUSDT":
        bad = (h.index >= UTC("2022-07-01")) & (h.index < UTC("2023-04-01"))
    out = {}
    for key, zc in (("señal (z cuota spot ≥ 1,5)", z >= 1.5), ("placebo (z ≤ −1, liderada por perpetuos)", z <= -1.0)):
        cand = zc & (c < lo7) & inmem & ~bad & ~(f24 <= -0.0005)
        rows, i, n = [], 0, len(h)
        while i < n - 1:
            if not cand[i] or not (atr[i] > 0):
                i += 1; continue
            run = {"k": 0}

            def ex(k, run=run):
                run["k"] = run["k"] + 1 if z[k] <= 0 else 0
                return run["k"] >= 12
            k, x = short_sim(h, i, atr[i], ex, 120)
            rows.append((h.index[i], -(x / c[i] - 1) - 2 * PERP + fsum(fu, h.index[i], h.index[k])))
            i = k + 1
        out[key] = rows
    return out


def run_S():
    mem = members()
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_S, [(s, mem) for s in syms]))
    print(f"\n=== S — Ruptura bajista liderada por spot → corto ({sum(1 for r in res if r)} monedas con spot)")
    for key in ("señal (z cuota spot ≥ 1,5)", "placebo (z ≤ −1, liderada por perpetuos)"):
        report(key, [x for r in res for x in r.get(key, [])], (("desarrollo", ("2020-01-01", "2023-01-01")), ("examen", ("2023-01-01", "2026-11-01"))))


if __name__ == "__main__":
    for x in (sys.argv[1:] or ["P", "T", "W", "S"]):
        {"P": run_P, "T": run_T, "W": run_W, "S": run_S}[x]()
