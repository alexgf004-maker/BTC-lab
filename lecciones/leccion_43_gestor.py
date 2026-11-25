"""Lección 43 — Construcción de cartera (P0–P2) y mejoras del bloque D (P3–P5). docs/leccion_43.md"""
import json
import sys
import warnings
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones")); sys.path.insert(0, "/home/user/alexgf004-maker/btc-strategy-monitor")
from sclab import data, universe  # noqa: E402
from leccion_22_validacion import st  # noqa: E402

EXA0 = pd.Timestamp("2023-07-01", tz="UTC")
C = 0.0007
fmt = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+6.1f} % | caída {100 * d['DD']:5.1f} % | MAR {d['CAGR'] / d['DD']:.2f}"


# ------------------------------------------------------------------ nivel cartera
def g_series():
    import leccion_40_suite_monitor as L
    from monitor.market import resample
    from monitor.portfolio import allocate_portfolio
    from monitor.strategies import _r_multiple, generate_a
    out = []
    for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        c1 = resample(L.candles(s), 1)
        cands = [replace(t, exit_dt=t.exit_dt + 1) if t.exit_i is not None else
                 replace(t, exit_i=len(c1) - 1, exit_dt=c1[-1].close_time + 1, exit=c1[-1].close,
                         r_multiple=_r_multiple(t.side, t.entry, c1[-1].close, t.risk_distance)) for t in generate_a(c1, 0)]
        res = allocate_portfolio(cands)
        eq = pd.Series({pd.Timestamp(e["event_dt"]).floor("1D"): e["equity_after"] for e in res.events if e["event_type"] == "EXIT"})
        eq = eq.groupby(level=0).last().reindex(pd.date_range("2020-01-01", "2026-10-31", tz="UTC")).ffill().fillna(800.0)
        out.append(eq.pct_change().fillna(0))
    return sum(out) / 3


def portfolio(R, weight_fn, target_vol=None):
    vals, val = [], 1.0
    months = pd.Series(R.index.to_period("M"), index=R.index)
    for m in months.unique():
        days = R.index[months == m]
        hist = R[R.index < days[0]].tail(180)
        w = weight_fn(hist) if len(hist) >= 90 else np.full(R.shape[1], 1 / R.shape[1])
        w = np.asarray(w, float); w = w / w.sum() if w.sum() > 0 else np.full(R.shape[1], 1 / R.shape[1])
        lev = 1.0
        if target_vol and len(hist) >= 90:
            pv = (hist.tail(90) @ w).std() * np.sqrt(365)
            lev = min(2.0, target_vol / pv) if pv > 0 else 1.0
        for d in days:
            val *= 1 + lev * float(R.loc[d].to_numpy() @ w)
            vals.append((d, val))
    e = pd.Series(dict(vals))
    return e.pct_change().fillna(0)


def cartera():
    R = pd.read_csv(ROOT / "docs/l17_bloques_diarios.csv", index_col=0, parse_dates=True)
    a = R["A carry"]; R["A carry"] = a - a.mean() + (1.036 ** (1 / 365.25) - 1)
    R.index = pd.to_datetime(R.index, utc=True)
    R["G rafaga"] = g_series().reindex(R.index).fillna(0)
    R = R[["A carry", "E carry inverso", "B S1 corto alt/BTC", "D tendencia BTC/ETH", "G rafaga"]].loc["2020-03-01":"2026-10-31"]
    eqw = lambda h: np.ones(h.shape[1])
    invv = lambda h: 1 / h.tail(90).std().replace(0, np.nan).fillna(1e9).to_numpy()
    def mom(h):
        s = (h.mean() / h.std().replace(0, np.nan)).fillna(0).clip(lower=0).to_numpy()
        return 0.5 * np.ones(h.shape[1]) / h.shape[1] + (0.5 * s / s.sum() if s.sum() > 0 else 0.5 * np.ones(h.shape[1]) / h.shape[1])
    P = {"P0 pesos iguales": portfolio(R, eqw), "P1a inversa de la volatilidad": portfolio(R, invv),
         "P1b volatilidad objetivo 12 %": portfolio(R, eqw, 0.12), "P1c inversa vol. + objetivo 12 %": portfolio(R, invv, 0.12),
         "P2 momentum de estrategias": portfolio(R, mom)}
    print("=== NIVEL CARTERA (bloques A, E, B, D, G)")
    for a_, b_ in (("2020-07-01", "2022-12-31"), ("2023-01-01", "2026-10-31"), ("2020-07-01", "2026-10-31")):
        print(f"--- {a_} → {b_}")
        for k, v in P.items():
            print(f"   {k:32s} {fmt(st(v.loc[a_:b_]))}")


# ------------------------------------------------------------------ nivel operativo: simulador del bloque D
def prep(sym):
    h = data.load(sym, "1h")
    b = h.resample("4h", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    tr = pd.concat([b.high - b.low, (b.high - b.close.shift()).abs(), (b.low - b.close.shift()).abs()], axis=1).max(axis=1)
    b["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    dd = b.close.resample("1D").last().dropna()
    b["reg"] = np.sign(dd - dd.ewm(span=50, adjust=False).mean()).shift(1).reindex(b.index, method="ffill")
    b["hi"] = b.high.rolling(120).max().shift(1)
    try:
        f = data.load_funding(sym)
    except Exception:
        f = pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
    b["f3"] = f.rolling("72h").sum().div(9).reindex(b.index, method="ffill").fillna(0)
    return b, f


def trades_D(b, f, pyramid=False, euphoria=None, regime=None, months=None):
    """Lista de operaciones con su resultado en múltiplos del riesgo TOTAL asignado (5 %) y fechas."""
    o, h, l, c = b.open.to_numpy(), b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
    atr, reg, hi, f3, idx = b.atr.to_numpy(), b.reg.to_numpy(), b.hi.to_numpy(), b.f3.to_numpy(), b.index
    out, i, n = [], 121, len(b)
    while i < n - 1:
        ok = c[i] > hi[i] and reg[i] > 0
        if ok and euphoria is not None and f3[i] > euphoria:
            ok = False
        if ok and regime is not None and not regime(idx[i]):
            ok = False
        if ok and months is not None and pd.Timestamp(idx[i].year, idx[i].month, 1, tz="UTC") not in months:
            ok = False
        if not ok:
            i += 1; continue
        e = i + 1; entry = o[e]; R = 5 * atr[i]; stop = entry - R; ext = entry
        units = [(entry, 0.5 if pyramid else 1.0)]          # (precio, fracción del riesgo total de 5 %)
        adds = [entry + atr[i], entry + 2 * atr[i]] if pyramid else []
        j = e
        while j < n:
            if l[j] <= stop:
                ex = min(stop, o[j]); break
            for a in list(adds):
                if h[j] >= a:
                    units.append((a, 0.25)); adds.remove(a)
            ext = max(ext, h[j]); stop = max(stop, ext - 5 * atr[j]); j += 1
        else:
            ex = c[-1]; j = n - 1
        fund = float(f[(f.index > idx[e]) & (f.index <= idx[j])].sum()) if len(f) else 0.0
        # cada unidad arriesga su fracción con distancia R (5 ATR) desde su precio; resultado en R del riesgo total
        res = sum(w * ((ex - p) - (2 * C + fund) * p) / R for p, w in units)
        out.append({"t": idx[e], "exit": idx[j], "R": res})
        i = j + 1
    return pd.DataFrame(out)


def curve(T, risk=0.05):
    if T.empty:
        return pd.Series(dtype=float)
    s = T.groupby(T.exit.dt.floor("1D")).R.sum() * risk
    eq = (1 + s).cumprod()
    return eq.reindex(pd.date_range("2020-03-01", "2026-10-31", tz="UTC")).ffill().fillna(1.0).pct_change().fillna(0)


def tstat(x):
    d = x.groupby(x.t.dt.floor("1D")).R.mean()
    return d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan


def operativo():
    print("\n=== NIVEL OPERATIVO (bloque D)")
    P = {s: prep(s) for s in ("BTCUSDT", "ETHUSDT")}
    variants = {"D actual (5 % de una vez)": {}, "P3 piramidación 2,5 % + 2,5 % + 2,5 %": {"pyramid": True},
                "P5 filtro de euforia (funding 3d > 0,03 %)": {"euphoria": 0.0003}}
    for name, kw in variants.items():
        T = pd.concat([trades_D(*P[s], **kw).assign(sym=s) for s in P])
        cv = (curve(T[T.sym == "BTCUSDT"]) + curve(T[T.sym == "ETHUSDT"])) / 2
        print(f"  {name}")
        for lab, a_, b_ in (("desarrollo", "2020-03-01", "2023-06-30"), ("EXAMEN", "2023-07-01", "2026-10-31")):
            x = T[(T.t >= a_) & (T.t <= b_)]
            print(f"     {lab:10s} {fmt(st(cv.loc[a_:b_]))} | operaciones {len(x)} | E {x.R.mean():+.3f}R")
    # P4: D en altcoins con BTC en tendencia
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    mem = universe.monthly_members(universe.daily_volume(sorted(set(OLD + NEW))), 12)
    alts = {}
    for mth, ss in mem.items():
        for s in [x for x in ss if x not in ("BTCUSDT", "ETHUSDT")][:10]:
            alts.setdefault(s, set()).add(mth)
    bd = data.load("BTCUSDT", "1h").close.resample("1D").last()
    btc_up = (bd > bd.ewm(span=50, adjust=False).mean()).shift(1)
    reg = lambda t: bool(btc_up.asof(t.floor("1D"))) if t.floor("1D") >= btc_up.index[0] else False
    rows = []
    for s, months in alts.items():
        try:
            b, f = prep(s)
        except Exception:
            continue
        T = trades_D(b, f, regime=reg, months=months)
        if len(T):
            rows.append(T.assign(sym=s))
    T = pd.concat(rows)
    print("  P4 D en las 10 altcoins más líquidas (solo con BTC sobre su EMA50)")
    for lab, x in (("desarrollo", T[T.t < EXA0]), ("EXAMEN", T[T.t >= EXA0])):
        print(f"     {lab:10s} operaciones {len(x)} | E {x.R.mean():+.3f}R (t {tstat(x):+.2f}) | aciertos {100 * (x.R > 0).mean():.1f} %")


if __name__ == "__main__":
    cartera()
    operativo()
