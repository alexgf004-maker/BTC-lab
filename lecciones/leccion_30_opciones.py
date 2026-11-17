"""Lección 30 — Prima de volatilidad con iron condor semanal (Deribit). Pre-registro en docs/leccion_30.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sclab import data  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/deribit"
DEV, EXA = ("2019-01-01", "2022-12-31"), ("2023-01-01", "2026-11-30")


def parse(name):
    cur, exp, k, typ = name.split("-")
    return pd.Timestamp(pd.to_datetime(exp, format="%d%b%y")).tz_localize("UTC") + pd.Timedelta("8h"), float(k), typ


def rv30(cur):
    c = data.load(f"{cur}USDT", "1h")["close"]
    r = np.log(c).diff()
    return (r.rolling(24 * 30).std() * np.sqrt(24 * 365))


def week(cur, day, deliv, k1, k2, days=7, puts_only=False):
    f = D / f"trades_{cur}_{day.date()}.json"
    tr = json.loads(f.read_text()) if f.exists() else []
    expiry = day + pd.Timedelta(f"{days}D") + pd.Timedelta("8h")
    rows = []
    for x in tr:
        try:
            e, K, typ = parse(x["instrument_name"])
        except Exception:
            continue
        if e == expiry:
            rows.append((K, typ, x["mark_price"], x["index_price"], x["iv"]))
    if len(rows) < 5:
        return None, "sin operaciones"
    df = pd.DataFrame(rows, columns=["K", "typ", "mark", "S", "iv"])
    S = df["S"].median()
    atm = df[(df.K / S - 1).abs() < 0.03]
    if atm.empty:
        return None, "sin ATM"
    sig = atm["iv"].median() / 100
    sd = sig * np.sqrt(days / 365)
    marks = df.assign(usd=df.mark * df.S).groupby(["typ", "K"]).agg(mark=("mark", "median"), usd=("usd", "median")).reset_index()
    def pick(typ, target):
        m = marks[marks.typ == typ]
        if m.empty:
            return None
        return m.iloc[(m.K - target).abs().argmin()]
    sc, lc = pick("C", S * np.exp(k1 * sd)), pick("C", S * np.exp(k2 * sd))
    sp, lp = pick("P", S * np.exp(-k1 * sd)), pick("P", S * np.exp(-k2 * sd))
    if any(v is None for v in (sc, lc, sp, lp)) or not (lc.K > sc.K > S > sp.K > lp.K):
        return None, "strikes no válidos"
    if puts_only:
        sc = lc = None
    def fill(leg, side):                                   # side +1 compra, −1 venta (en USD)
        hs = max(0.00025, 0.04 * leg.mark) * S
        fee = min(0.0003, 0.125 * leg.mark) * S
        return -side * leg.usd - hs - fee                      # flujo de caja: vender cobra, comprar paga
    credit = fill(sp, -1) + fill(lp, +1) + (0 if sc is None else fill(sc, -1) + fill(lc, +1))
    ST = deliv.get(str(expiry.date()))
    if ST is None:
        return None, "sin precio de entrega"
    callpay = [] if sc is None else [max(ST - sc.K, 0), max(ST - lc.K, 0)]
    pay = -(max(sp.K - ST, 0) - max(lp.K - ST, 0)) - (0 if sc is None else callpay[0] - callpay[1])
    sfee = sum(min(0.00015 * ST, 0.125 * v) for v in callpay + [max(sp.K - ST, 0), max(lp.K - ST, 0)] if v > 0)
    maxloss = max(0 if sc is None else lc.K - sc.K, sp.K - lp.K) - credit
    if credit <= 0 or maxloss <= 0:
        return None, "crédito no positivo"
    return dict(day=day, S=S, sig=sig, credit=credit, maxloss=maxloss, ST=ST, R=(credit + pay - sfee) / maxloss,
                gross_R=(credit + pay) / maxloss), "ok"


def run(cur, k1=1.0, k2=2.0):
    deliv = pd.read_csv(D / f"delivery_{cur.lower()}_usd.csv").set_index("date")["delivery_price"].to_dict()
    days = pd.date_range("2019-01-04", "2026-11-06", freq="W-FRI", tz="UTC")
    out, why = [], {}
    for d in days:
        r, w = week(cur, d, deliv, k1, k2)
        why[w] = why.get(w, 0) + 1
        if r:
            out.append(r)
    return pd.DataFrame(out).set_index("day"), why


def stats(df, label):
    if df.empty:
        print(f"{label}: sin operaciones"); return
    R = df["R"]
    t = R.mean() / R.std() * np.sqrt(len(R))
    eq = (1 + 0.10 * R).cumprod()
    yr = (1 + 0.10 * R).groupby(R.index.year).prod() - 1
    dd = (1 - eq / eq.cummax()).max()
    print(f"{label}: n {len(R)} | E[R] {R.mean():+.3f} (t {t:+.2f}) | ganadoras {100 * (R > 0).mean():.0f} % | peor {R.min():+.2f} | "
          f"anual (10 % en riesgo) {100 * (eq.iloc[-1] ** (52 / len(R)) - 1):+.1f} % | DD {100 * dd:.1f} % | "
          f"años {' '.join(f'{y}:{100 * v:+.0f}%' for y, v in yr.items())}")


def o1():
    print("\n=== O1 prima de volatilidad (DVOL frente a la realizada de los 30 días siguientes)")
    for cur in ("BTC", "ETH"):
        dv = pd.read_csv(D / f"dvol_{cur}.csv"); dv.index = pd.to_datetime(dv.t, unit="ms", utc=True)
        iv = dv["c"].resample("1D").last() / 100
        c = data.load(f"{cur}USDT", "1h")["close"]; r = np.log(c).diff()
        fwd = r.rolling(24 * 30).std().shift(-24 * 30) * np.sqrt(24 * 365)
        j = pd.concat([iv, fwd.resample("1D").last()], axis=1, keys=["iv", "rv"]).dropna()
        p = j.iv - j.rv
        for per, (a, b) in (("2021-03→2022", ("2021-03-01", "2022-12-31")), ("2023→2026", ("2023-01-01", "2026-10-31"))):
            q = p.loc[a:b]
            print(f"{cur} {per}: implícita media {100 * j.iv.loc[a:b].mean():.1f} % | realizada {100 * j.rv.loc[a:b].mean():.1f} % | "
                  f"prima media {100 * q.mean():+.1f} pts, mediana {100 * q.median():+.1f} | implícita > realizada {100 * (q > 0).mean():.0f} % de los días")


def run_monthly(cur, puts_only):
    deliv = pd.read_csv(D / f"delivery_{cur.lower()}_usd.csv").set_index("date")["delivery_price"].to_dict()
    out, why = [], {}
    for m in pd.date_range("2019-01-01", "2026-10-01", freq="MS", tz="UTC"):
        lastfri = (m + pd.offsets.MonthEnd(0)).normalize()
        while lastfri.dayofweek != 4:
            lastfri -= pd.Timedelta("1D")
        r, w = week(cur, lastfri - pd.Timedelta("28D"), deliv, 1.0, 2.0, days=28, puts_only=puts_only)
        why[w] = why.get(w, 0) + 1
        if r:
            out.append(r)
    return pd.DataFrame(out).set_index("day"), why


def stats_m(df, label):
    if df.empty:
        print(f"{label}: sin operaciones"); return
    R = df["R"]; t = R.mean() / R.std() * np.sqrt(len(R))
    eq = (1 + 0.10 * R).cumprod(); yr = (1 + 0.10 * R).groupby(R.index.year).prod() - 1
    print(f"{label}: n {len(R)} | E[R] {R.mean():+.3f} (t {t:+.2f}) | ganadoras {100 * (R > 0).mean():.0f} % | peor {R.min():+.2f} | "
          f"anual (10 % en riesgo por mes) {100 * (eq.iloc[-1] ** (12 / len(R)) - 1):+.1f} % | años {' '.join(f'{y}:{100 * v:+.0f}%' for y, v in yr.items())}")


if __name__ == "__main__" and "--mensual" in sys.argv:
    for cur in ("BTC", "ETH"):
        for po, nm in ((False, "O4 iron condor mensual"), (True, "O5 spread de put mensual")):
            df, why = run_monthly(cur, po)
            print(f"\n=== {nm} {cur} — {why}")
            stats_m(df.loc[DEV[0]:DEV[1]], f"{cur} desarrollo"); stats_m(df.loc[EXA[0]:EXA[1]], f"{cur} EXAMEN")


if __name__ == "__main__" and "--mensual" not in sys.argv:
    o1()
    for cur in ("BTC", "ETH"):
        df, why = run(cur)
        print(f"\n=== O2 {cur} iron condor (1σ / 2σ) — semanas: {why}")
        stats(df.loc[DEV[0]:DEV[1]], f"{cur} desarrollo"); stats(df.loc[EXA[0]:EXA[1]], f"{cur} EXAMEN")
        g = df.assign(gR=df.gross_R)
        print(f"   sin costes de ejecución: E[R] desarrollo {g.loc[DEV[0]:DEV[1], 'gR'].mean():+.3f} | examen {g.loc[EXA[0]:EXA[1], 'gR'].mean():+.3f}"
              f" | crédito medio / pérdida máx. {(df.credit / df.maxloss).mean():.3f}")
        rv = rv30(cur)
        f = df[df.sig > rv.reindex(df.index, method="ffill").values]
        print(f"--- O3 {cur} solo si implícita > realizada 30 d ({len(f)} de {len(df)} semanas)")
        stats(f.loc[DEV[0]:DEV[1]], f"{cur} O3 desarrollo"); stats(f.loc[EXA[0]:EXA[1]], f"{cur} O3 EXAMEN")
        for k1, k2 in ((0.75, 1.5), (1.25, 2.5)):
            dfr, _ = run(cur, k1, k2)
            stats(dfr.loc[DEV[0]:DEV[1]], f"   robustez {k1}σ/{k2}σ desarrollo"); stats(dfr.loc[EXA[0]:EXA[1]], f"   robustez {k1}σ/{k2}σ examen")
