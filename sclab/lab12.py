"""Lección 12: N1 tendencia relativa, N2 cesta contra la volatilidad, N3 captura de funding, N4 purga de apalancamiento."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data, indicators as ind, portfolio, trend, universe
from .swing import SwingCosts
from .universe import is_member

ROOT = Path(__file__).resolve().parent.parent
BAR = pd.Timedelta("4h")


def _funding(s):
    try:
        return data.load_funding(s)
    except ValueError:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))


# ------------------------------------------------------------------ N1
def n1_relative_trend(symbols, K=20, N=120, m=5.0, risk=0.01, max_pos=10):
    btc = data.load("BTCUSDT", "1h")["close"]; f_btc = _funding("BTCUSDT")
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    cands, closes = [], {}
    for s in symbols:
        if s == "BTCUSDT":
            continue
        a = data.load(s, "1h")["close"]
        r1 = (a / btc.reindex(a.index)).dropna()
        if len(r1) < 24 * 120:
            continue
        df = r1.resample("4h").agg(["first", "max", "min", "last"]).dropna()
        df.columns = ["open", "high", "low", "close"]
        df["atr"] = ind.atr(df, 14)
        dd = df["close"].resample("1D").last().dropna()
        tr = ind.daily_on_intraday(np.sign(dd - ind.ema(dd, 50)), df.index, BAR)
        up = (tr > 0) & (df["close"] > df["high"].rolling(N).max().shift(1))
        dn = (tr < 0) & (df["close"] < df["low"].rolling(N).min().shift(1))
        side = up.to_numpy().astype(int) - dn.to_numpy().astype(int)
        fund = pd.concat([_funding(s), -f_btc]).sort_index()
        t = trend.simulate(df, side, m, fund, costs=SwingCosts(taker=0.0010, slip=0.0004), bar=BAR, one_at_a_time=False)
        if t.empty:
            continue
        t["symbol"] = s
        t = t[is_member(members, s, pd.DatetimeIndex(t.entry_time))]
        cands.append(t); closes[s] = df["close"]
    cands = pd.concat(cands, ignore_index=True)
    curve, tk, lev = portfolio.run(cands, closes, risk, K=max_pos)
    daily = curve.resample("1D").last().pct_change().dropna()
    tk = tk.rename(columns={"r_net": "ret"}).assign(entry=lambda x: x.entry_time)
    return daily, tk, {"apal_max": float(lev.max()) * 2}


# ------------------------------------------------------------------ N2
def n2_low_vol_basket(symbols, K=25, n_leg=8, cap=0.05, stop=0.5):
    btc = data.load("BTCUSDT", "1h")
    D, Hh, F = {}, {}, {}
    for s in symbols:
        h = data.load(s, "1h")
        D[s], Hh[s] = h["close"].resample("1D").last(), h["high"].resample("1D").max()
        f = _funding(s)
        F[s] = f.resample("1D").sum() if len(f) else pd.Series(dtype=float)
    D, Hh = pd.DataFrame(D), pd.DataFrame(Hh)
    F = pd.DataFrame(F).reindex(D.index).reindex(columns=D.columns).fillna(0)
    R = D.pct_change(fill_method=None)
    rb = btc["close"].resample("1D").last().pct_change().reindex(D.index)
    vol = R.rolling(30, min_periods=25).std()
    beta = R.rolling(90, min_periods=60).cov(rb).div(rb.rolling(90, min_periods=60).var(), axis=0)
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    Df = D.ffill()
    eq, out, months, w_prev = 1.0, [], [], pd.Series(dtype=float)
    starts = [m for m in sorted(members) if m >= pd.Timestamp("2020-07-01", tz="UTC") and m in D.index]
    for a, b in zip(starts, starts[1:] + [D.index[-1] + pd.Timedelta("1D")]):
        i0 = D.index.get_loc(a) - 1                       # datos hasta el día anterior al rebalanceo
        el = [s for s in members[a] if np.isfinite(vol.iloc[i0].get(s, np.nan)) and np.isfinite(beta.iloc[i0].get(s, np.nan))
              and np.isfinite(D.iloc[i0][s])]
        if len(el) < 2 * n_leg:
            continue
        v = vol.iloc[i0][el].sort_values()
        lo, hi = v.index[:n_leg], v.index[-n_leg:]
        wl = (1 / v[lo]) / (1 / v[lo]).sum(); ws = (1 / v[hi]) / (1 / v[hi]).sum()
        bl = max(float((wl * beta.iloc[i0][lo]).sum()), 0.3); bs = max(float((ws * beta.iloc[i0][hi]).sum()), 0.3)
        L, S = 1 / bl, 1 / bs
        L, S = L / (L + S), S / (L + S)
        ws = (ws * S).clip(upper=cap)
        bs_eff = float((ws * beta.iloc[i0][hi].clip(lower=0.3)).sum())      # beta en dólares del lado corto
        wl = wl * min(bs_eff / bl, 1.0)
        w = pd.concat([wl, -ws])
        allw = w.index.union(w_prev.index)
        turn = float((w.reindex(allw, fill_value=0) - w_prev.reindex(allw, fill_value=0)).abs().sum())
        seg = Df.loc[(Df.index >= a) & (Df.index < b)]
        p0 = Df.iloc[i0]
        rel = seg[w.index] / p0[w.index] - 1
        # stop individual de los cortos (máximo diario >= +50 %)
        hrel = Hh.reindex(seg.index)[hi] / p0[hi] - 1
        extra = 0.0
        for s in hi:
            hit = hrel[s] >= stop
            if hit.any():
                t_hit = hit.idxmax()
                rel.loc[rel.index >= t_hit, s] = stop
                extra += abs(w[s]) * 0.0007
        fund = (F.reindex(seg.index)[w.index] * w).sum(axis=1).cumsum()        # largos pagan, cortos cobran
        for s in hi:                                                           # tras el stop ya no se cobra funding
            pass
        path = (rel * w).sum(axis=1) - fund - turn * 0.0007 - extra
        e = eq * (1 + path)
        out.append(e); months.append((a, float(path.iloc[-1]), turn, float(wl.sum()), float(ws.sum())))
        eq = float(e.iloc[-1]); w_prev = w
    curve = pd.concat(out)
    daily = curve.pct_change().dropna()
    mm = pd.DataFrame(months, columns=["entry", "ret", "rotacion", "largo", "corto"])
    return daily, mm, {"rotacion_media": float(mm.rotacion.mean()), "largo_medio": float(mm.largo.mean()), "corto_medio": float(mm.corto.mean())}


# ------------------------------------------------------------------ N4
def n4_deleverage_rebound(symbols, K=20, k_sigma=3.0, oi_drop=0.10, hold=24, alloc=0.10):
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    rows, idx_all = [], None
    for s in symbols:
        p = ROOT / "data" / "metrics" / f"{s}.parquet"
        if not p.exists():
            continue
        c = data.load(s, "1h")["close"]
        oi = pd.read_parquet(p)["sum_open_interest"]
        oi = oi[~oi.index.duplicated(keep="last")].sort_index().replace(0, np.nan).reindex(c.index)
        r4 = c / c.shift(4) - 1
        sd = r4.rolling(720, min_periods=360).std().shift(1)
        o4 = oi / oi.shift(4) - 1
        cond = ((r4 <= -k_sigma * sd) & (o4 <= -oi_drop)).to_numpy() & is_member(members, s, c.index)
        cv, f = c.to_numpy(), _funding(s)
        busy = -1
        for i in np.flatnonzero(cond):
            if i <= busy or i + hold >= len(cv):
                continue
            t0, t1 = c.index[i], c.index[i + hold]
            fs = float(f[(f.index > t0) & (f.index <= t1 + pd.Timedelta("1min"))].sum()) if len(f) else 0.0
            rows.append((s, t0, t1, cv[i + hold] / cv[i] - 1 - 0.0014 - fs, float(r4.iloc[i]), float(o4.iloc[i])))
            busy = i + hold
    tr = pd.DataFrame(rows, columns=["symbol", "entry", "exit", "ret", "caida_4h", "oi_4h"])
    days = pd.date_range(tr.entry.min().floor("1D"), pd.Timestamp("2026-10-31", tz="UTC"), freq="1D")
    daily = (tr.set_index("exit").ret * alloc).resample("1D").sum().reindex(days, fill_value=0)
    conc = pd.concat([pd.Series(1, tr.entry), pd.Series(-1, tr.exit)]).sort_index().cumsum().max()
    return daily, tr, {"simultaneas_max": int(conc)}


# ------------------------------------------------------------------ métricas comunes
def summary(daily: pd.Series, tr: pd.DataFrame) -> dict:
    eq = (1 + daily).cumprod()
    yrs = (daily.index[-1] - daily.index[0]).days / 365.25
    mid = daily.index[0] + (daily.index[-1] - daily.index[0]) / 2
    h1, h2 = daily[daily.index < mid], daily[daily.index >= mid]
    x = tr.ret
    return {"sharpe": daily.mean() / daily.std() * np.sqrt(365), "CAGR": eq.iloc[-1] ** (1 / yrs) - 1,
            "maxDD": float((1 - eq / eq.cummax()).max()), "mitad1": float((1 + h1).prod() - 1), "mitad2": float((1 + h2).prod() - 1),
            "corte": mid.strftime("%Y-%m"), "n": len(x), "WR": float((x > 0).mean()),
            "PF": float(x[x > 0].sum() / -x[x <= 0].sum()), "por_año": (daily.groupby(daily.index.year).apply(lambda r: (1 + r).prod() - 1)).round(3).to_dict()}


# ------------------------------------------------------------------ N3
def n3_funding_capture(symbols, t_in=-2, t_out=15, cost=0.0020, alloc=0.20, max_pos=5, min_rate=0.001):
    E = pd.read_parquet(ROOT / "data/cache/eventos_funding.parquet")
    W = pd.read_parquet(ROOT / "data/cache/ventanas_funding.parquet")
    E = E[E.symbol.isin(symbols) & (E.rate.abs() >= min_rate)].rename(columns={"time": "T"})
    W = W[W.symbol.isin(symbols)]
    px = W.pivot_table(index=["symbol", "T"], columns="off", values="close")
    ev = E.set_index(["symbol", "T"]).join(px[[t_in, t_out]].dropna(), how="inner")
    d = -np.sign(ev.rate)
    ev["precio"] = d * (ev[t_out] / ev[t_in] - 1)
    ev["bruto"] = ev.rate.abs() + ev.precio
    ev["ret"] = ev.bruto - cost
    ev = ev.reset_index()
    ev["entry"] = ev["T"]
    # cartera: como mucho max_pos eventos por liquidación, los de mayor tasa
    sel = ev.assign(a=ev.rate.abs()).sort_values("a", ascending=False).groupby("T").head(max_pos)
    days = pd.date_range(ev.entry.min().floor("1D"), pd.Timestamp("2026-10-31", tz="UTC"), freq="1D")
    daily = (sel.set_index("T").ret * alloc).resample("1D").sum().reindex(days, fill_value=0)
    daily2 = (sel.set_index("T").eval("ret - @cost") * alloc).resample("1D").sum().reindex(days, fill_value=0)
    # perfil medio del precio (a favor de la posición) respecto al minuto de entrada
    offs = [-60, -30, -10, -2, 0, 1, 2, 5, 15, 30, 60]
    pp = px.reindex(pd.MultiIndex.from_frame(ev[["symbol", "T"]]))
    prof = {o: float((d.to_numpy() * (pp[o].to_numpy() / pp[t_in].to_numpy() - 1)).mean()) for o in offs if o in pp}
    tiers = {f">={k:.2%}": (int((ev.rate.abs() >= k).sum()), float(ev.ret[ev.rate.abs() >= k].mean()),
                            float((ev.ret[ev.rate.abs() >= k] > 0).mean())) for k in (0.001, 0.0025, 0.005, 0.01)}
    extra = {"eventos": len(ev), "tasa_media": float(ev.rate.abs().mean()), "precio_medio": float(ev.precio.mean()),
             "bruto_medio": float(ev.bruto.mean()), "neto_medio": float(ev.ret.mean()),
             "t_neto": float(ev.ret.mean() / ev.ret.std() * np.sqrt(len(ev))),
             "sharpe_costes_dobles": float(daily2.mean() / daily2.std() * np.sqrt(365)),
             "positivas": float(ev.ret[ev.rate > 0].mean()), "negativas": float(ev.ret[ev.rate < 0].mean()),
             "perfil": {k: round(v, 5) for k, v in prof.items()}, "tramos(n, neto, WR)": tiers}
    return daily, sel[["symbol", "entry", "rate", "precio", "ret"]], extra


# ------------------------------------------------------------------ N3b: rebote tras la liquidación, a escala de segundos
def n3b_events(symbols, delay_ms=500, entry_win=500, exits=(10_000, 30_000, 60_000), fee=0.0010):
    """Para cada evento: entrada a mercado `delay_ms` después de T en el sentido del funding, al PEOR precio pagado por
    los agresores de ese lado en la ventana; salida a mercado al PEOR precio del lado contrario en [h, h+2s]."""
    E = pd.read_parquet(ROOT / "data/cache/eventos_funding.parquet").rename(columns={"time": "T"})
    X = pd.read_parquet(ROOT / "data/cache/trades_tras_funding.parquet")
    X = X[X.symbol.isin(symbols)]
    rate = E.set_index(["symbol", "T"]).rate
    rows = []
    for (sym, T), g in X.groupby(["symbol", "T"], sort=False):
        r = rate.get((sym, T))
        if r is None or np.ndim(r):
            continue
        s = 1 if r > 0 else -1
        dt, px, bm, q = g.dt.to_numpy(), g.price.to_numpy(), g.bm.to_numpy(), g.qty.to_numpy()
        mine = (~bm) if s == 1 else bm                 # operaciones en las que el agresor va en nuestro sentido
        w = mine & (dt >= delay_ms) & (dt < delay_ms + entry_win)
        if w.any():
            entry = px[w].max() if s == 1 else px[w].min()
            usd = float((px[w] * q[w]).sum())
        else:
            nxt = np.flatnonzero(mine & (dt >= delay_ms))
            if not len(nxt):
                continue
            entry, usd = px[nxt[0]], float(px[nxt[0]] * q[nxt[0]])
        row = {"symbol": sym, "entry": T, "rate": r, "p0": px[0], "usd_ventana": usd, "mov_entrada": s * (entry / px[0] - 1)}
        for h in exits:
            o = (~mine) & (dt >= h) & (dt < h + 2000)
            if o.any():
                ex = px[o].min() if s == 1 else px[o].max()
            else:
                prev = np.flatnonzero((~mine) & (dt < h + 2000))
                ex = px[prev[-1]] if len(prev) else np.nan
            row[f"ret_{h // 1000}s"] = s * (ex / entry - 1) - fee
        for tms in (100, 250, 500, 1000, 2000, 5000, 10_000, 30_000, 60_000, 89_000):
            k = np.searchsorted(dt, tms, side="right") - 1
            row[f"p_{tms}"] = s * (px[max(k, 0)] / px[0] - 1)
        rows.append(row)
    return pd.DataFrame(rows)
