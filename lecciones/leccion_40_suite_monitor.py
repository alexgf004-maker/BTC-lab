"""Lección 40 — Suite del BTC-Strategy-Monitor: ventaja fuera de BTC y complemento a la cartera (docs/leccion_40.md).

Usa el código del propio monitor sin modificar (repositorio alexgf004-maker/BTC-Strategy-Monitor clonado en MONITOR).
"""
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MONITOR = Path("/home/user/alexgf004-maker/btc-strategy-monitor")
sys.path.insert(0, str(MONITOR)); sys.path.insert(0, str(ROOT / "lecciones"))
from monitor.market import _parse_archive, resample  # noqa: E402
from monitor.portfolio import allocate_portfolio  # noqa: E402
from monitor.strategies import _r_multiple, generate_candidates  # noqa: E402
from leccion_22_validacion import monthly_rebalanced, st  # noqa: E402


def candles(sym):
    rows = []
    for f in sorted((ROOT / "data/k15").glob(f"{sym}-15m-*.zip")):
        rows += _parse_archive(f.read_bytes())
    rows.sort(key=lambda c: c.open_time)
    out, seen = [], set()
    for c in rows:
        if c.open_time not in seen:
            seen.add(c.open_time); out.append(c)
    return out


def run(sym):
    c15 = candles(sym); c1 = resample(c15, 1); c4 = resample(c15, 4)
    cands = generate_candidates(c15, c1, c4, min_entry_dt=0)
    series = {"A": c1, "B": c4, "C": c15, "D": c1}
    closed = []
    for t in cands:                                   # mismas convenciones que tools/validate_historical.py
        if t.exit_i is not None:
            closed.append(replace(t, exit_dt=t.exit_dt + 1)); continue
        s = series[t.strategy]; px = s[-1].close
        closed.append(replace(t, exit_i=len(s) - 1, exit_dt=s[-1].close_time + 1, exit=px,
                              r_multiple=_r_multiple(t.side, t.entry, px, t.risk_distance), reason="cutoff_mark"))
    trades = pd.DataFrame([{"sym": sym, "eng": t.strategy, "t": pd.Timestamp(t.entry_dt, unit="ms", tz="UTC"), "R": t.r_multiple}
                           for t in closed])
    res = allocate_portfolio(closed)
    ev = [e for e in res.events if e["event_type"] == "EXIT"]
    eq = pd.Series({pd.Timestamp(e["event_dt"]): e["equity_after"] for e in ev}).sort_index()
    return trades, eq, res.realized_equity


def tstat(x):
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


if __name__ == "__main__":
    T, EQ = [], {}
    for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        tr, eq, fin = run(s)
        T.append(tr); EQ[s] = eq
        print(f"{s}: {len(tr)} operaciones | {dict(tr.eng.value_counts().sort_index())} | 800 $ → {fin:,.0f} $ con su gestor de riesgo")
    T = pd.concat(T)
    print("\n=== C1 por motor (resultado medio por operación en R, neto del 0,24 %)")
    for eng in "ABCD":
        x = T[T.eng == eng]
        b, o = x[x.sym == "BTCUSDT"].R, x[x.sym != "BTCUSDT"].R
        e_, s_ = x[x.sym == "ETHUSDT"].R, x[x.sym == "SOLUSDT"].R
        print(f"{eng}: BTC n {len(b)} E {b.mean():+.3f}R (t {tstat(b):+.2f}) | FUERA DE BTC n {len(o)} E {o.mean():+.3f}R (t {tstat(o):+.2f}) "
              f"| ETH {e_.mean():+.3f}R ({len(e_)}) · SOL {s_.mean():+.3f}R ({len(s_)})")
    # C2: serie diaria de la suite y cartera
    def daily(eq):
        d = eq.copy(); d.index = d.index.floor("1D")
        d = d.groupby(level=0).last()
        idx = pd.date_range("2020-01-01", "2026-10-31", tz="UTC")
        d = d.reindex(idx).ffill().fillna(800.0)
        return d.pct_change().fillna(0)
    sb = daily(EQ["BTCUSDT"])
    s3 = (daily(EQ["BTCUSDT"]) + daily(EQ["ETHUSDT"]) + daily(EQ["SOLUSDT"])) / 3
    R = pd.read_csv(ROOT / "docs/l17_bloques_diarios.csv", index_col=0, parse_dates=True)
    a = R["A carry"]; R["A carry"] = a - a.mean() + (1.036 ** (1 / 365.25) - 1)
    R.index = pd.to_datetime(R.index, utc=True)
    R["Suite BTC"] = sb.reindex(R.index).fillna(0)
    R["Suite BTC+ETH+SOL"] = s3.reindex(R.index).fillna(0)
    base = ["A carry", "E carry inverso", "B S1 corto alt/BTC", "D tendencia BTC/ETH"]
    print("\n=== C2 correlación mensual con cada bloque y con la cartera")
    M = (1 + R).resample("ME").prod() - 1
    P = monthly_rebalanced(R[base]); Pm = (1 + P).resample("ME").prod() - 1
    for k in ("Suite BTC", "Suite BTC+ETH+SOL"):
        print(f"{k}: " + " | ".join(f"{b[:12]} {M[k].corr(M[b]):+.2f}" for b in base) + f" | cartera {M[k].corr(Pm):+.2f}")
    P5a = monthly_rebalanced(R[base + ["Suite BTC"]]); P5b = monthly_rebalanced(R[base + ["Suite BTC+ETH+SOL"]])
    fmt = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+.1f} % | caída {100 * d['DD']:.1f} %"
    for a_, b_ in (("2020-03-01", "2022-12-31"), ("2023-01-01", "2026-10-31"), ("2020-03-01", "2026-10-31")):
        print(f"--- {a_} → {b_}")
        for name, s in (("cartera actual", P), ("+ suite BTC (1/5)", P5a), ("+ suite 3 monedas (1/5)", P5b),
                        ("suite BTC sola", R["Suite BTC"]), ("suite 3 monedas sola", R["Suite BTC+ETH+SOL"])):
            print(f"   {name:24s} {fmt(st(s.loc[a_:b_]))}")
    T.to_csv(ROOT / "docs/l40_operaciones.csv", index=False)
