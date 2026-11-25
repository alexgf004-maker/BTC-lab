"""Lección 42 — Motor A en altcoins (H1), espejo bajista (H2) y filtro anticapitulación para B (H3). docs/leccion_42.md"""
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
from bot.strategies.momentum import Z_TH, backtest, features  # noqa: E402
from sclab import data, lab15, universe  # noqa: E402
from leccion_22_validacion import st  # noqa: E402

EXA0 = pd.Timestamp("2023-07-01", tz="UTC")
FEE = 0.0024


def short_backtest(df):
    f = features(df)
    out, i, n = [], 72, len(f)
    while i < n - 1:
        r = f.iloc[i]
        sig = (r.ret3 < -0.015 and np.isfinite(r.z) and r.z > Z_TH and r.close < r.ema200 and r.close < r.open
               and np.isfinite(r.atr) and r.atr > 0)
        if not sig:
            i += 1; continue
        e = i + 1; entry = f.open.iloc[e]; stop = entry + 1.5 * r.atr; res = None
        for k in range(60):
            if e + k >= n:
                break
            b = f.iloc[e + k]
            if b.open >= stop: res = (b.open, e + k); break
            if b.high >= stop: res = (stop, e + k); break
            if k == 5 and b.close > entry: res = (b.close, e + k); break
            if k == 59: res = (b.close, e + k); break
        if not res:
            break
        px, x = res
        out.append({"entry_t": f.index[e], "R": ((entry - px) - FEE * entry) / (stop - entry)})
        i = x + 1
    return pd.DataFrame(out)


def job(args):
    sym, months = args
    h = data.load(sym, "1h")[["open", "high", "low", "close", "count"]].dropna()
    if len(h) < 24 * 30:
        return sym, pd.DataFrame(), pd.DataFrame()
    keep = lambda T: T[[pd.Timestamp(t.year, t.month, 1, tz="UTC") in months for t in T.entry_t]] if len(T) else T
    lg = backtest(h); sh = short_backtest(h)
    return sym, keep(lg), keep(sh)


def stats(T, label):
    if T.empty:
        print(f"   {label:34s} sin operaciones"); return
    d = T.groupby(T.entry_t.dt.floor("1D")).R.mean()
    t = d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan
    print(f"   {label:34s} n {len(T):5d} | E {T.R.mean():+.3f}R (t {t:+5.2f}) | aciertos {100 * (T.R > 0).mean():4.1f} %")


if __name__ == "__main__":
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    mem = universe.monthly_members(universe.daily_volume(sorted(set(OLD + NEW))), 23)
    alts, all_months = {}, set(mem)
    for mth, ss in mem.items():
        for s in [x for x in ss if x not in ("BTCUSDT", "ETHUSDT", "SOLUSDT")][:20]:
            alts.setdefault(s, set()).add(mth)
    jobs = [(s, m) for s, m in alts.items()] + [(s, all_months) for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")]
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, jobs))
    L = pd.concat([lg.assign(sym=s) for s, lg, _ in res if len(lg)])
    S = pd.concat([sh.assign(sym=s) for s, _, sh in res if len(sh)])
    big3 = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    print("=== H1 motor A (largos) en las 20 altcoins más líquidas (sin BTC, ETH ni SOL)")
    la = L[~L.sym.isin(big3)]
    stats(la[la.entry_t < EXA0], "desarrollo 2020-03 → 2023-06"); stats(la[la.entry_t >= EXA0], "EXAMEN 2023-07 → 2026-10")
    print("   (referencia BTC/ETH/SOL:)"); lb = L[L.sym.isin(big3)]
    stats(lb[lb.entry_t < EXA0], "  BTC/ETH/SOL desarrollo"); stats(lb[lb.entry_t >= EXA0], "  BTC/ETH/SOL examen")
    print("\n=== H2 espejo bajista (cortos)")
    for lab, x in (("BTC/ETH/SOL", S[S.sym.isin(big3)]), ("altcoins", S[~S.sym.isin(big3)]), ("todo", S)):
        stats(x[x.entry_t < EXA0], f"{lab} desarrollo"); stats(x[x.entry_t >= EXA0], f"{lab} EXAMEN")
    L.to_csv(ROOT / "docs/l42_H1.csv", index=False); S.to_csv(ROOT / "docs/l42_H2.csv", index=False)
    print("\n=== H3 bloque B con filtro anticapitulación (BTC −10 % en 72 h → no abrir cortos)")
    btc = data.load("BTCUSDT", "1h")["close"]
    r72 = btc / btc.shift(72) - 1
    ok = lambda times: ~(r72.reindex(times.floor("1h"), method="ffill").fillna(0).to_numpy() < -0.10)
    base, tk0, _ = lab15.s1_relative_weakness(OLD + NEW, K=30)
    filt, tk1, _ = lab15.s1_relative_weakness(OLD + NEW, K=30, entry_ok=ok)
    fmt = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+.1f} % | caída {100 * d['DD']:.1f} %"
    for a, b in (("2020-03-01", "2022-12-31"), ("2023-01-01", "2026-10-31")):
        print(f"--- {a} → {b}")
        print(f"   B sin filtro  {fmt(st(base.loc[a:b]))} | operaciones {((tk0.entry >= a) & (tk0.entry <= b)).sum()}")
        print(f"   B con filtro  {fmt(st(filt.loc[a:b]))} | operaciones {((tk1.entry >= a) & (tk1.entry <= b)).sum()}")
