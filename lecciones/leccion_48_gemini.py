"""Lección 48 — Ideas de Gemini, primera tanda: U (bombas coreanas), M (estrés de crédito), C (monedas moribundas),
X (prima de lotería). Reglas en docs/leccion_48.md. Uso: python3 lecciones/leccion_48_gemini.py [U|M|C|X]..."""
import io
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data, lab15, universe  # noqa: E402

DEV, EXAM = ("2020-01-01", "2022-12-31"), ("2023-01-01", "2026-10-31")
UTC = lambda s: pd.Timestamp(s, tz="UTC")


# ------------------------------------------------------------------------------------------------ utilidades
def tcl(r: pd.Series, t: pd.Series):
    """t de la media con errores agrupados por semana."""
    if len(r) < 3:
        return float("nan")
    u = r - r.mean()
    g = u.groupby(pd.DatetimeIndex(t).tz_localize(None).to_period("W").values).sum()
    se = np.sqrt((g ** 2).sum()) / len(r)
    return r.mean() / se if se > 0 else float("nan")


def report(name, T, col="r", tcol="t"):
    line = f"  {name:44s}"
    for lab, (a, b) in (("desarrollo", DEV), ("examen", EXAM)):
        X = T[(T[tcol] >= UTC(a)) & (T[tcol] <= UTC(b) + pd.Timedelta("1D"))]
        line += f" | {lab}: n {len(X):4d}, media {100 * X[col].mean():+.2f} %, t {tcl(X[col], X[tcol]):+.2f}"
    line += f" | total t {tcl(T[col], T[tcol]):+.2f}"
    print(line, flush=True)


def members():
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    return vol, universe.monthly_members(vol, 30)


def month(t):
    return pd.Timestamp(t.year, t.month, 1, tz="UTC")


_FUND = {}


def fund(sym):
    if sym not in _FUND:
        try:
            _FUND[sym] = lab15._funding(sym)
        except Exception:
            _FUND[sym] = pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
    return _FUND[sym]


def fsum(sym, a, b):
    f = fund(sym)
    return float(f[(f.index > a) & (f.index <= b)].sum()) if len(f) else 0.0


def daily_closes(syms):
    out = {}
    for s in syms:
        try:
            h = data.load(s, "1h")
        except Exception:
            continue
        out[s] = h["close"].resample("1D").last()
    return pd.DataFrame(out)


# ------------------------------------------------------------------------------------------------ M · estrés de crédito
def fred(id_):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": id_}, timeout=60)
    d = pd.read_csv(io.StringIO(r.text)); d.columns = ["date", "v"]
    d["v"] = pd.to_numeric(d["v"], errors="coerce"); d = d.dropna()
    return pd.Series(d["v"].to_numpy(), index=pd.to_datetime(d["date"]).dt.tz_localize("UTC"))


def m_series(shift_days=0):
    z = 0
    for id_ in ("BAA10Y", "DFII10"):
        s = fred(id_)
        d5 = s.diff(5)
        z = z + (d5 - d5.rolling(252, min_periods=200).mean().shift(1)) / d5.rolling(252, min_periods=200).std().shift(1)
    z = z.dropna()
    z.index = z.index + pd.Timedelta(days=2 + shift_days)                   # disponible 2 días después (± placebo)
    cal = pd.date_range(UTC("2019-06-01"), UTC("2026-11-01"), freq="1D")
    return z.reindex(cal.union(z.index)).ffill().reindex(cal)


def run_M():
    vol, mem = members()
    syms = sorted(set().union(*mem.values()) | {"BTCUSDT"})
    C = daily_closes(syms)                                                   # cierre del día d = precio a las 00:00 de d+1
    P = C.copy(); P.index = P.index + pd.Timedelta("1D")                     # P[t] = precio a las 00:00 de t
    R = P.pct_change()
    print("\n=== M — Estrés de crédito y tipos reales → corto en altcoins de beta alta")
    for lab, sh in (("señal real", 0), ("placebo +15 días", 15), ("placebo −15 días", -15)):
        M = m_series(sh)
        rows, t = [], UTC("2020-03-01")
        end = UTC("2026-10-31")
        while t < end:
            if not (M.get(t, np.nan) >= 2):
                t += pd.Timedelta("1D"); continue
            uni = [s for s in mem.get(month(t), set()) if s != "BTCUSDT" and s in P]
            hist = R.loc[t - pd.Timedelta("30D"):t - pd.Timedelta("1D")]
            b = hist["BTCUSDT"]
            stats = []
            for s in uni:
                x = hist[s]
                ok = x.notna() & b.notna()
                if ok.sum() < 20 or not P[s].get(t) > 0:
                    continue
                beta = np.cov(x[ok], b[ok])[0, 1] / b[ok].var()
                stats.append((beta, s, x[ok].std()))
            stats = sorted(stats, reverse=True)[:15]
            if not stats:
                t += pd.Timedelta("1D"); continue
            w = pd.Series({s: 1 / v for _, s, v in stats}); w /= w.sum()
            e = P.loc[t, w.index]
            k, out = t, None
            while k < end:
                k += pd.Timedelta("1D")
                px = P.loc[k, w.index].fillna(e)
                pnl = -(w * (px / e - 1)).sum()
                if pnl <= -0.06:
                    out = (k, pnl, "stop"); break
                if M.get(k, np.nan) <= 0.5:
                    out = (k, pnl, "señal"); break
                if k - t >= pd.Timedelta("14D"):
                    out = (k, pnl, "tiempo"); break
            if out is None:
                break
            k, pnl, why = out
            f = sum(w[s] * fsum(s, t, k) for s in w.index)
            rows.append((t, pnl + f - 2 * 0.0007, why))
            t = k + pd.Timedelta("1D")
        T = pd.DataFrame(rows, columns=["t", "r", "why"])
        report(lab, T)


# ------------------------------------------------------------------------------------------------ X · prima de lotería
def run_X():
    vol, mem = members()
    syms = sorted(set().union(*mem.values()))
    H = {}
    for s in syms:
        try:
            H[s] = data.load(s, "1h")["close"]
        except Exception:
            pass
    H = pd.DataFrame(H)
    HR = H.pct_change(fill_method=None)
    P = H.resample("1D").last(); P.index = P.index + pd.Timedelta("1D")    # precio a las 00:00
    DR = P.pct_change(fill_method=None)
    print("\n=== X — Prima de lotería: corto en las 6 de mayor residuo, largo en las 6 de menor (neutral en dólares)")
    rows, prev = [], pd.Series(dtype=float)
    for t in pd.date_range(UTC("2020-03-03"), UTC("2026-10-28"), freq="3D"):
        uni = [s for s in mem.get(month(t), set()) if s in H]
        win = HR.loc[t - pd.Timedelta("14D"):t - pd.Timedelta("1h"), uni]
        win = win.loc[:, win.notna().sum() >= 300]
        if win.shape[1] < 20:
            continue
        mx = win.apply(lambda c: c.dropna().nlargest(3).mean())
        sd = win.std()
        r14 = P.loc[t, win.columns] / P.loc[t - pd.Timedelta("14D"), win.columns] - 1
        df = pd.DataFrame({"L": mx / sd, "r14": r14, "sd": sd}).dropna()
        if len(df) < 20:
            continue
        Xm = np.column_stack([np.ones(len(df)), df.r14, df.sd])
        beta, *_ = np.linalg.lstsq(Xm, df.L.to_numpy(), rcond=None)
        res = pd.Series(df.L.to_numpy() - Xm @ beta, index=df.index).sort_values()
        f24 = {s: fund(s)[(fund(s).index > t - pd.Timedelta("24h")) & (fund(s).index <= t)].mean() if len(fund(s)) else 0.0
               for s in res.index}
        shorts = [s for s in res.index[::-1] if not (f24.get(s, 0) < -0.0005)][:6]
        longs = [s for s in res.index if s not in shorts][:6]
        v30 = DR.loc[t - pd.Timedelta("30D"):t, shorts + longs].std()
        wl = (1 / v30[longs]); wl = 0.5 * wl / wl.sum()
        ws = (1 / v30[shorts]); ws = -0.5 * ws / ws.sum()
        w = pd.concat([wl, ws]).fillna(0)
        t2 = t + pd.Timedelta("3D")
        ret = (P.loc[t2, w.index] / P.loc[t, w.index] - 1).fillna(0)
        f = pd.Series({s: fsum(s, t, t2) for s in w.index})
        turn = (w.reindex(w.index.union(prev.index), fill_value=0) - prev.reindex(w.index.union(prev.index), fill_value=0)).abs().sum()
        rows.append((t, float((w * ret).sum() - (w * f).sum() - 0.0007 * turn)))
        prev = w
    T = pd.DataFrame(rows, columns=["t", "r"])
    for lab, (a, b) in (("desarrollo", DEV), ("examen", EXAM)):
        x = T[(T.t >= UTC(a)) & (T.t <= UTC(b))].r
        print(f"  {lab}: periodos {len(x)}, media {100 * x.mean():+.3f} % cada 3 días, Sharpe {x.mean() / x.std() * np.sqrt(365 / 3):+.2f}")
    print(f"  total: t {T.r.mean() / T.r.std() * np.sqrt(len(T)):+.2f}")


# ------------------------------------------------------------------------------------------------ C · monedas moribundas
def run_C():
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    syms = [s for s in vol.columns if s != "BTCUSDT"]
    C = daily_closes(syms)
    Hh = {}
    for s in syms:
        try:
            Hh[s] = data.load(s, "1h")["high"].resample("1D").max()
        except Exception:
            pass
    HI = pd.DataFrame(Hh)
    P = C.copy(); P.index = P.index + pd.Timedelta("1D")
    v30 = vol.rolling(30, min_periods=25).mean()
    v7 = vol.rolling(7, min_periods=6).mean()
    v90 = vol.rolling(90, min_periods=80).mean()
    vmax = v30.rolling(365, min_periods=120).max()
    hi365 = C.rolling(365, min_periods=120).max()
    sma50 = C.rolling(50, min_periods=45).mean()
    print("\n=== C — Monedas moribundas fuera del top 50 (corto, semanal)")
    out = {"señal": [], "placebo (todas las elegibles)": []}
    prev = {k: set() for k in out}
    for t in pd.date_range(UTC("2020-06-01"), UTC("2026-10-26"), freq="W-MON"):
        d = t - pd.Timedelta("1D")                                          # último día cerrado
        if d not in v30.index:
            continue
        rank = v30.loc[d].dropna().sort_values(ascending=False)
        tail = [s for s in rank.index[50:] if v7.loc[d, s] > 3e6 and s in P and P[s].get(t) > 0]
        cond = []
        for s in tail:
            fw = fund(s); f7 = fw[(fw.index > t - pd.Timedelta("7D")) & (fw.index <= t)].mean() if len(fw) else 0.0
            if (v90.loc[d, s] <= 0.3 * vmax.loc[d, s] and C.loc[d, s] <= 0.4 * hi365.loc[d, s] and C.loc[d, s] < sma50.loc[d, s]
                    and not (f7 <= -0.0001)):
                cond.append((v90.loc[d, s] / vmax.loc[d, s], s))
        picks = {"señal": [s for _, s in sorted(cond)[:15]], "placebo (todas las elegibles)": tail}
        t2 = t + pd.Timedelta("7D")
        for k, ps in picks.items():
            if not ps:
                prev[k] = set(); continue
            rs = []
            for s in ps:
                e = P.loc[t, s]
                hi = HI.loc[t:t2 - pd.Timedelta("1D"), s].max()
                x = P.loc[t2, s] if t2 in P.index and P.loc[t2, s] > 0 else P[s].loc[t:t2].dropna().iloc[-1]
                r = -(x / e - 1)
                if hi >= 1.25 * e:
                    r = -0.25
                r += fsum(s, t, t2)
                cost = 0.0015 * ((s not in prev[k]) + 1)                     # entrada si es nueva; la salida se cobra siempre (conservador)
                rs.append(r - cost)
            out[k].append((t, float(np.mean(rs)), len(ps)))
            prev[k] = set(ps)
    for k, rows in out.items():
        T = pd.DataFrame(rows, columns=["t", "r", "n"])
        report(f"{k} (media {T.n.mean():.1f} monedas/semana)", T)


# ------------------------------------------------------------------------------------------------ U · bombas coreanas
def run_U():
    vol, mem = members()
    sys.path.insert(0, str(ROOT / "sclab"))
    from upbit_dl import base
    up = {f.stem: pd.read_parquet(f) for f in (ROOT / "data" / "upbit").glob("*.parquet")}
    btc = data.load("BTCUSDT", "1h")["close"].resample("4h").last()
    rate = (up["BTC"]["close"] / btc.reindex(up["BTC"].index)).dropna()         # wones por dólar (implícito)
    syms = sorted(s for s in set().union(*mem.values()) if base(s) in up and s != "BTCUSDT")
    print(f"\n=== U — Agotamiento de bombas coreanas ({len(syms)} monedas con mercado KRW)")
    res = {"señal": [], "placebo (bombas sin dominancia coreana)": []}
    for s in syms:
        h = data.load(s, "1h")
        b = h.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
                                  "quote_volume": "sum"}).dropna()
        u = up[base(s)].reindex(b.index)
        uv = (u["krw_vol"] / rate.reindex(b.index)).fillna(0)
        U = uv.rolling(6).sum() / (uv.rolling(6).sum() + b.quote_volume.rolling(6).sum())
        med = U.rolling(540, min_periods=270).median().shift(1)
        r24 = b.close / b.close.shift(6) - 1
        vw8 = (b.quote_volume + b.quote_volume.shift(1)) / (b.volume + b.volume.shift(1))
        inmem = universe.is_member(mem, s, b.index)
        o, hi, lo, c = (b[k].to_numpy() for k in ("open", "high", "low", "close"))
        for key, cond in (("señal", (U >= 3 * med)), ("placebo (bombas sin dominancia coreana)", (U <= med))):
            ph1 = (cond & (r24 > 0.15) & (uv > 0)).to_numpy() & inmem
            i, n = 0, len(b)
            while i < n - 1:
                if not ph1[i]:
                    i += 1; continue
                j_ent = None
                for j in range(i + 1, min(i + 7, n)):
                    mx = uv.iloc[i:j + 1].max()
                    if uv.iloc[j] <= 0.6 * mx and c[j] < vw8.iloc[j]:
                        j_ent = j; break
                if j_ent is None:
                    i += 1; continue
                e = c[j_ent]; stop, tgt = 1.10 * e, 0.85 * e
                x, k = None, j_ent
                for k in range(j_ent + 1, min(j_ent + 19, n)):
                    if o[k] >= stop or hi[k] >= stop:
                        x = max(o[k], stop); break
                    if lo[k] <= tgt:
                        x = min(o[k], tgt); break
                if x is None:
                    x = c[k]
                r = -(x / e - 1) - 2 * 0.0007 + fsum(s, b.index[j_ent] + pd.Timedelta("4h"), b.index[k] + pd.Timedelta("4h"))
                res[key].append((b.index[j_ent] + pd.Timedelta("4h"), r, s))
                i = k + 1
    for k, rows in res.items():
        T = pd.DataFrame(rows, columns=["t", "r", "sym"])
        report(k, T)


if __name__ == "__main__":
    for h in (sys.argv[1:] or ["M", "X", "C", "U"]):
        {"M": run_M, "X": run_X, "C": run_C, "U": run_U}[h]()
