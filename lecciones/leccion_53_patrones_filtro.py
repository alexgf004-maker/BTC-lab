"""Lección 53 — Patrones chartistas como filtro de D, B y G (docs/leccion_53.md)."""
import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import data, lab15, universe  # noqa: E402
from leccion_22_validacion import st  # noqa: E402
from leccion_43_gestor import C, curve, fmt, prep  # noqa: E402
from leccion_44_bloque_b import BAR, COST, frame  # noqa: E402
from leccion_52_chartistas import AGG, setups, zigzag  # noqa: E402
from bot.strategies.momentum import backtest as g_backtest  # noqa: E402

BEAR, BULL = {"doble techo", "HCH"}, {"doble suelo", "HCH invertido", "triángulo ascendente"}
W4 = pd.Timedelta("4h"); RECENT = 30 * W4


def pattern_times(df):
    """Momentos (cierre de la vela de 4 h) en que se rompe cada figura (detector de la L52, sin placebos)."""
    c = df.close.to_numpy(); idx = df.index
    by_conf = {}
    for p in zigzag(df):
        by_conf.setdefault(p[3], []).append(p)
    confirmed, pending, out = [], [], {"bear": [], "bull": []}
    for i in range(len(df)):
        for p in by_conf.get(i, []):
            confirmed.append(p)
            pending = [(s, i) for s in setups(confirmed) if not s[0].startswith("placebo")]
        keep = []
        for s, born in pending:
            if i <= born:
                keep.append((s, born)); continue
            if i - born > 30:
                continue
            if s[2](i, c[i]):
                out["bear" if s[0] in BEAR else "bull" if s[0] in BULL else "otro"] = out.get(
                    "bear" if s[0] in BEAR else "bull" if s[0] in BULL else "otro", []) + [idx[i] + W4]
            else:
                keep.append((s, born))
        pending = keep
    return {k: pd.DatetimeIndex(sorted(set(v))) for k, v in out.items()}


def recent(times, t):
    """¿Hubo alguna ruptura en (t − 30 velas, t]?"""
    if not len(times):
        return False
    j = times.searchsorted(t, side="right")
    return j > 0 and times[j - 1] > t - RECENT


def usd4h(sym):
    return data.load(sym, "1h").resample("4h").agg(AGG).dropna()


# ------------------------------------------------------------------------------------------------ D (C1, C2)
def trades_D(b, f, pt, exit_on_bear=False, skip_recent_bear=False):
    """D actual (piramidación + euforia 0,03 %) con las variantes C1/C2. Resultado en R del riesgo total de 5 %."""
    o, h, l, c = b.open.to_numpy(), b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
    atr, reg, hi, f3, idx = b.atr.to_numpy(), b.reg.to_numpy(), b.hi.to_numpy(), b.f3.to_numpy(), b.index
    bear = set(pt["bear"])
    out, i, n = [], 121, len(b)
    while i < n - 1:
        ok = c[i] > hi[i] and reg[i] > 0 and not f3[i] > 0.0003
        if ok and skip_recent_bear and recent(pt["bear"], idx[i] + W4):
            ok = False
        if not ok:
            i += 1; continue
        e = i + 1; entry = o[e]; R = 5 * atr[i]; stop = entry - R; ext = entry
        units = [(entry, 0.5)]; adds = [entry + atr[i], entry + 2 * atr[i]]
        j = e
        while j < n:
            if l[j] <= stop:
                ex = min(stop, o[j]); break
            for a in list(adds):
                if h[j] >= a:
                    units.append((a, 0.25)); adds.remove(a)
            if exit_on_bear and (idx[j] + W4) in bear:
                ex = c[j]; break
            ext = max(ext, h[j]); stop = max(stop, ext - 5 * atr[j]); j += 1
        else:
            ex = c[-1]; j = n - 1
        fund = float(f[(f.index > idx[e]) & (f.index <= idx[j])].sum()) if len(f) else 0.0
        res = sum(w * ((ex - p) - (2 * C + fund) * p) / R for p, w in units)
        out.append({"t": idx[e], "exit": idx[j], "R": res})
        i = j + 1
    return pd.DataFrame(out)


def run_D():
    print("\n=== C1 / C2 sobre el bloque D (BTC y ETH)")
    P = {s: prep(s) for s in ("BTCUSDT", "ETHUSDT")}
    PT = {s: pattern_times(usd4h(s)) for s in P}
    for name, kw in (("D actual", {}), ("C1 sale con figura bajista", {"exit_on_bear": True}),
                     ("C2 no entra tras figura bajista", {"skip_recent_bear": True})):
        T = pd.concat([trades_D(*P[s], PT[s], **kw).assign(sym=s) for s in P])
        cv = (curve(T[T.sym == "BTCUSDT"]) + curve(T[T.sym == "ETHUSDT"])) / 2
        line = f"  {name:34s}"
        for lab, a_, b_ in (("desarrollo", "2020-03-01", "2023-06-30"), ("examen", "2023-07-01", "2026-10-31")):
            x = T[(T.t >= a_) & (T.t <= b_)]
            line += f" | {lab}: {fmt(st(cv.loc[a_:b_]))} | n {len(x)}"
        print(line, flush=True)


# ------------------------------------------------------------------------------------------------ B (C3, C4)
def trades_B(df, fund, pt, mode=None, m=5.0):
    o, h, l, c, a = (df[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    t, tns = df.index, df.index.as_unit("ns").asi8
    f_t = fund.index.as_unit("ns").asi8; f_cum = np.concatenate([[0.0], np.cumsum(fund.to_numpy())])
    n, rows, d = len(df), [], -1
    for i in np.flatnonzero(df["sig"].to_numpy()):
        if i + 1 >= n or not (a[i] > 0):
            continue
        size = 1.0
        if mode == "C3" and recent(pt["bull"], t[i] + BAR):
            continue
        if mode == "C4" and recent(pt["bear"], t[i] + BAR):
            size = 1.5
        j = i + 1; entry = o[j]; R = m * a[i]; stop = entry + R; ext = entry
        exit_px, k = None, j
        for k in range(j, n):
            if k > j and o[k] >= stop:
                exit_px = o[k]; break
            if h[k] >= stop:
                exit_px = stop; break
            ext = min(ext, l[k]); stop = min(stop, ext + m * a[k])
        if exit_px is None:
            exit_px, k = c[n - 1], n - 1
        fa_ = np.searchsorted(f_t, tns[j], side="right"); fb_ = np.searchsorted(f_t, tns[k] + BAR.value, side="right")
        fsum = f_cum[fb_] - f_cum[fa_]
        r = (d * (exit_px - entry) - (entry + exit_px) * COST - d * fsum * entry) / R
        rows.append((t[j], t[k] + BAR, d, entry, R, size * r))
    return pd.DataFrame(rows, columns=["entry_time", "exit_time", "side", "entry", "R", "r_net"])


def job_B(args):
    sym, months = args
    btc = data.load("BTCUSDT", "1h")["close"]; f_btc = lab15._funding("BTCUSDT")
    fr = frame(sym, btc, f_btc)
    if fr is None:
        return sym, None, {}
    df, fund = fr
    pt = pattern_times(usd4h(sym))
    out = {}
    for name, mode in (("B actual", None), ("C3 sin cortos tras figura alcista", "C3"), ("C4 riesgo ×1,5 tras figura bajista", "C4")):
        T = trades_B(df, fund, pt, mode)
        if len(T):
            T = T[universe.is_member(months, sym, pd.DatetimeIndex(T.entry_time))]
            T["symbol"] = sym
        out[name] = T
    return sym, df["close"], out


def run_B():
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    syms = sorted(set(OLD + NEW))
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    mem = universe.monthly_members(vol[[s for s in syms if s in vol]], 30)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_B, [(s, mem) for s in syms if s != "BTCUSDT"]))
    closes = {s: c for s, c, _ in res if c is not None}
    f2 = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+6.1f} % | caída {100 * d['DD']:5.1f} %"
    print("\n=== C3 / C4 sobre el bloque B (riesgo 1 %, máximo 10 posiciones, top 30)")
    for name in ("B actual", "C3 sin cortos tras figura alcista", "C4 riesgo ×1,5 tras figura bajista"):
        cands = pd.concat([o[name] for _, c, o in res if c is not None and name in o and len(o[name])], ignore_index=True)
        daily, tk, _ = lab15._run_portfolio(cands, closes, 0.01, 10)
        line = f"  {name:40s}"
        for lab, a_, b_ in (("2020–22", "2020-03-01", "2022-12-31"), ("2023–26", "2023-01-01", "2026-10-31")):
            line += f" | {lab}: {f2(st(daily.loc[a_:b_]))}"
        print(line + f" | operaciones {len(tk)}", flush=True)


# ------------------------------------------------------------------------------------------------ G (C5)
def run_G():
    print("\n=== C5 sobre el bloque G (BTC, ETH, SOL; con filtro de euforia)")
    rows = []
    for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        h = data.load(s, "1h")
        T = g_backtest(h[["open", "high", "low", "close", "count"]])
        f = lab15._funding(s)
        f3 = f.rolling("72h").sum().div(9)
        pt = pattern_times(usd4h(s))
        for _, r in T.iterrows():
            tdec = r.signal + pd.Timedelta("1h")
            v = f3.asof(tdec) if len(f3) and tdec >= f3.index[0] else 0.0
            if v == v and v > 0.0003:
                continue
            rows.append((tdec, r.R, recent(pt["bear"], tdec)))
    T = pd.DataFrame(rows, columns=["t", "R", "bear"])
    for name, X in (("G actual (con euforia)", T), ("C5 sin compras tras figura bajista", T[~T.bear])):
        line = f"  {name:36s}"
        for lab, a_, b_ in (("desarrollo", "2020-01-01", "2023-01-01"), ("examen", "2023-01-01", "2026-11-01")):
            Y = X[(X.t >= pd.Timestamp(a_, tz="UTC")) & (X.t < pd.Timestamp(b_, tz="UTC"))]
            Z = T[(T.t >= pd.Timestamp(a_, tz="UTC")) & (T.t < pd.Timestamp(b_, tz="UTC"))]
            line += f" | {lab}: n {len(Y)} ({100 * len(Y) / max(len(Z), 1):.0f} %), E {Y.R.mean():+.3f}R"
        print(line, flush=True)


if __name__ == "__main__":
    for x in (sys.argv[1:] or ["D", "G", "B"]):
        {"D": run_D, "B": run_B, "G": run_G}[x]()
