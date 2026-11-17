"""Lección 15: estrategias en corto. Reglas: docs/leccion_15.md"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data, indicators as ind, portfolio, trend, universe
from .swing import SwingCosts
from .universe import is_member

ROOT = Path(__file__).resolve().parent.parent
BAR = pd.Timedelta("4h")
LEG = 0.0014
NON_CRYPTO = {"BTCDOMUSDT", "DEFIUSDT", "USDCUSDT", "USDEXUSDT", "USDBRLUSDT", "PAXGUSDT", "XAUTUSDT", "XAUUSDT",
              "XAGUSDT", "XPTUSDT", "XPDUSDT"}


def _funding(s):
    try:
        return data.load_funding(s)
    except Exception:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))


def is_crypto(sym) -> tuple[bool, float]:
    if sym in NON_CRYPTO:
        return False, np.nan
    h = data.load(sym, "1h")
    a = h["close"].pct_change().abs()
    wk = a.index.dayofweek >= 5
    ratio = a[wk].mean() / a[~wk].mean()
    return bool(ratio >= 0.5), float(ratio)


def _fund_sum(f, t0, t1):
    return float(f[(f.index > t0) & (f.index <= t1 + pd.Timedelta("1min"))].sum()) if len(f) else 0.0


def _run_portfolio(cands, closes, risk, max_pos=10):
    cands = cands.copy()
    for c in ("entry_time", "exit_time"):
        cands[c] = pd.to_datetime(cands[c], utc=True)
    curve, tk, lev = portfolio.run(cands, closes, risk, K=max_pos)
    daily = curve.resample("1D").last().pct_change().dropna()
    tk["entry_time"] = pd.to_datetime(tk["entry_time"], utc=True)
    daily = daily[daily.index >= tk.entry_time.min().floor("1D")]
    tk = tk.rename(columns={"r_net": "ret"}).assign(entry=lambda x: x.entry_time)
    return daily, tk, {"apal_max": float(lev.max())}


# ------------------------------------------------------------------ S1 debilidad relativa (lado corto de N1)
def s1_relative_weakness(symbols, K=20, N=120, m=5.0, risk=0.01, max_pos=10, cost_mult=1.0, min_vol=0.0, no_funding=False,
                         entry_ok=None):
    btc = data.load("BTCUSDT", "1h")["close"]; f_btc = _funding("BTCUSDT")
    vol = universe.daily_volume(symbols)
    members = universe.monthly_members(vol, K)
    if min_vol > 0:                                   # exige volumen medio de 30 días >= min_vol en el mes de entrada
        v30 = vol.rolling(30, min_periods=20).mean()
        members = {m: {x for x in ss if v30[x].asof(m - pd.Timedelta("1D")) >= min_vol} for m, ss in members.items()}
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
        dn = (tr < 0) & (df["close"] < df["low"].rolling(N).min().shift(1))
        side = -dn.to_numpy().astype(int)
        fund = None if no_funding else pd.concat([_funding(s), -f_btc]).sort_index()
        t = trend.simulate(df, side, m, fund, costs=SwingCosts(taker=0.0010 * cost_mult, slip=0.0004 * cost_mult), bar=BAR, one_at_a_time=False)
        if t.empty:
            continue
        t["symbol"] = s
        t = t[is_member(members, s, pd.DatetimeIndex(t.entry_time))]
        if entry_ok is not None:                      # filtro opcional de entrada (Lección 31)
            t = t[entry_ok(pd.DatetimeIndex(t.entry_time))]
        cands.append(t); closes[s] = df["close"]
    return _run_portfolio(pd.concat(cands, ignore_index=True), closes, risk, max_pos)


# ------------------------------------------------------------------ S2 tendencia bajista en mercado bajista
def s2_bear_trend(symbols, K=20, N=120, m=5.0, risk=0.01, max_pos=10):
    bd = data.load("BTCUSDT", "1h")["close"].resample("1D").last()
    bear = (bd < bd.rolling(200).mean()).astype(float)
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    cands, closes = [], {}
    for s in symbols:
        h = data.load(s, "1h")
        df = h.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        if len(df) < 400:
            continue
        df["atr"] = ind.atr(df, 14)
        dd = df["close"].resample("1D").last().dropna()
        below = ind.daily_on_intraday((dd < ind.ema(dd, 50)).astype(float), df.index, BAR)
        regime = ind.daily_on_intraday(bear, df.index, BAR)
        sig = (below > 0) & (regime > 0) & (df["close"] < df["low"].rolling(N).min().shift(1))
        t = trend.simulate(df, -sig.to_numpy().astype(int), m, _funding(s), bar=BAR, one_at_a_time=False)
        if t.empty:
            continue
        t["symbol"] = s
        t = t[is_member(members, s, pd.DatetimeIndex(t.entry_time))]
        if entry_ok is not None:                      # filtro opcional de entrada (Lección 31)
            t = t[entry_ok(pd.DatetimeIndex(t.entry_time))]
        cands.append(t); closes[s] = df["close"]
    return _run_portfolio(pd.concat(cands, ignore_index=True), closes, risk, max_pos)


def _daily_bars(s):
    h = data.load(s, "1h")
    return h.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def _short_daily_trades(s, d, sig, stop_px, hold_days, f):
    """Corto al cierre del día de señal; stop (máximos diarios; gaps a la apertura); salida al cierre tras hold_days."""
    o, h, c = d["open"].to_numpy(), d["high"].to_numpy(), d["close"].to_numpy()
    t, n, rows, busy = d.index, len(d), [], -1
    for i in np.flatnonzero(sig):
        if i <= busy or i + 1 >= n:
            continue
        entry, stop = c[i], stop_px[i]
        R = stop - entry
        if not (R > 0):
            continue
        last = min(i + hold_days, n - 1)
        px, j = None, last
        for j in range(i + 1, last + 1):
            if o[j] >= stop:
                px = o[j]; break
            if h[j] >= stop:
                px = stop; break
        if px is None:
            px, j = c[last], last
        t0, t1 = t[i] + pd.Timedelta("1D"), t[j] + pd.Timedelta("1D")
        net = (entry - px) - entry * LEG + entry * _fund_sum(f, t0, t1)
        rows.append((s, t0, t1, -1, entry, px, R, net / R))
        busy = j
    return rows


COLS = ["symbol", "entry_time", "exit_time", "side", "entry", "exit", "R", "r_net"]


# ------------------------------------------------------------------ S3 pump fallido
def s3_failed_pump(symbols, K=20, risk=0.005, max_pos=10):
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    rows, closes = [], {}
    for s in symbols:
        d = _daily_bars(s)
        if len(d) < 30:
            continue
        up3 = d["close"].shift(1) / d["close"].shift(4) - 1
        sig = (up3 >= 0.25) & (d["close"] < d["low"].shift(1))
        sig = sig.to_numpy() & is_member(members, s, d.index)
        stop = (d["high"].rolling(4).max() * 1.02).to_numpy()
        rows += _short_daily_trades(s, d, sig, stop, 7, _funding(s))
        closes[s] = d["close"]
    return _run_portfolio(pd.DataFrame(rows, columns=COLS), closes, risk, max_pos)


# ------------------------------------------------------------------ S4 saturación de largos
def s4_crowded_longs(symbols, K=20, risk=0.005, max_pos=10):
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    rows, closes, used = [], {}, 0
    for s in symbols:
        p = ROOT / "data" / "metrics" / f"{s}.parquet"
        if not p.exists():
            continue
        d = _daily_bars(s)
        oi = pd.read_parquet(p)["sum_open_interest"]
        oi = oi[~oi.index.duplicated(keep="last")].sort_index().replace(0, np.nan).resample("1D").last().reindex(d.index)
        f = _funding(s)
        f3 = (f.resample("1D").sum().reindex(d.index).fillna(0).rolling(3).sum() / 9) if len(f) else pd.Series(0.0, index=d.index)
        pc = d["close"].shift()
        tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(), (d["low"] - pc).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        sig = (f3 >= 0.0005) & (oi / oi.shift(7) - 1 >= 0.30) & (d["close"] / d["close"].shift(7) - 1 <= 0.05)
        sig = sig.to_numpy() & is_member(members, s, d.index)
        rows += _short_daily_trades(s, d, sig, (d["close"] + 2 * atr).to_numpy(), 3, f)
        closes[s] = d["close"]; used += 1
    return (*_run_portfolio(pd.DataFrame(rows, columns=COLS), closes, risk, max_pos)[:2], {"monedas_con_OI": used})


# ------------------------------------------------------------------ S5 cesta corta de lotería
def s5_lottery_short(symbols, K=25, n_short=5):
    btc = data.load("BTCUSDT", "1h")
    bd = btc["close"].resample("1D").last(); rb = bd.pct_change()
    D, MX, F = {}, {}, {}
    for s in symbols:
        h = data.load(s, "1h")
        D[s] = h["close"].resample("1D").last()
        c4 = h["close"].resample("4h").last()
        MX[s] = c4.pct_change(fill_method=None).rolling(42, min_periods=36).max().resample("1D").last()
        f = _funding(s)
        F[s] = f.resample("1D").sum() if len(f) else pd.Series(dtype=float)
    D, MX = pd.DataFrame(D), pd.DataFrame(MX).reindex(D.index if isinstance(D, pd.DataFrame) else None)
    D = pd.DataFrame(D); MX = MX.reindex(D.index); F = pd.DataFrame(F).reindex(D.index).fillna(0)
    R = D.pct_change(fill_method=None)
    beta = R.rolling(90, min_periods=60).cov(rb.reindex(D.index)).div(rb.reindex(D.index).rolling(90, min_periods=60).var(), axis=0)
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    Df = D.ffill(); fb = _funding("BTCUSDT").resample("1D").sum().reindex(D.index).fillna(0)
    out = []
    mondays = D.index[D.index.dayofweek == 0]
    for t0, t1 in zip(mondays[:-1], mondays[1:]):
        dec = t0 - pd.Timedelta("1D")
        if dec not in D.index:
            continue
        mem = members.get(pd.Timestamp(t0.year, t0.month, 1, tz="UTC"), set())
        el = [s for s in mem if s != "BTCUSDT" and np.isfinite(MX.loc[dec].get(s, np.nan)) and np.isfinite(beta.loc[dec].get(s, np.nan))
              and np.isfinite(D.loc[dec, s])]
        if len(el) < 10:
            continue
        sh = MX.loc[dec, el].sort_values().index[-n_short:]
        b = beta.loc[dec, sh].clip(0.3, 3.0)
        ws = pd.Series(1.0 / n_short, index=sh)
        hedge = float((ws * b).sum())
        scale = 1.0 / (1.0 + hedge)
        ws, hedge = ws * scale, hedge * scale
        end = t1 - pd.Timedelta("1D")
        p_end = Df.loc[dec:end, sh].iloc[-1]
        r_s = (p_end / D.loc[dec, sh] - 1).fillna(-1.0).clip(upper=3.0)
        r_b = bd.loc[end] / bd.loc[dec] - 1
        fs = F.loc[t0:end, sh].sum()
        ret = -(ws * r_s).sum() + (ws * fs).sum() + hedge * r_b - hedge * fb.loc[t0:end].sum() - 2 * (ws.sum() + hedge) * 0.0007
        out.append((t0, ret, float(r_s.mean())))
    w = pd.DataFrame(out, columns=["entry", "ret", "ret_cortos"]).set_index("entry")
    daily = w.ret
    return daily, w.reset_index(), {"semanas": len(w), "subida_media_de_los_cortos": float(w.ret_cortos.mean())}


def summary(daily: pd.Series, tr: pd.DataFrame, weekly=False) -> dict:
    ppy = 52 if weekly else 365
    eq = (1 + daily).cumprod()
    yrs = (daily.index[-1] - daily.index[0]).days / 365.25
    mid = daily.index[0] + (daily.index[-1] - daily.index[0]) / 2
    x = tr.ret
    return {"sharpe": daily.mean() / daily.std() * np.sqrt(ppy), "CAGR": eq.iloc[-1] ** (1 / max(yrs, 1e-9)) - 1,
            "maxDD": float((1 - eq / eq.cummax()).max()), "mitad1": float((1 + daily[daily.index < mid]).prod() - 1),
            "mitad2": float((1 + daily[daily.index >= mid]).prod() - 1), "corte": mid.strftime("%Y-%m"), "n": len(x),
            "WR": float((x > 0).mean()), "PF": float(x[x > 0].sum() / -x[x <= 0].sum()),
            "por_año": daily.groupby(daily.index.year).apply(lambda r: (1 + r).prod() - 1).round(3).to_dict()}
