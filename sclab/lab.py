"""Laboratorio de hipótesis (Lección 8). Cada función devuelve (rentabilidad diaria sobre el capital, trades o None)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data, universe

C_LEG = 0.0014      # ida y vuelta por pata: 2 × (taker 0,05 % + slippage 0,02 %)
C_TURN = 0.0007     # por unidad rotada


def panel(symbols):
    H, HI, QV, F = {}, {}, {}, {}
    for s in symbols:
        h = data.load(s, "1h")
        H[s], HI[s], QV[s] = h["close"], h["high"], h["quote_volume"]
        try:
            F[s] = data.load_funding(s)
        except ValueError:
            F[s] = pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
    H, HI, QV = pd.DataFrame(H), pd.DataFrame(HI), pd.DataFrame(QV)
    D = H.resample("1D").last()
    Fd = pd.DataFrame({s: f.resample("1D").sum() for s, f in F.items() if len(f)}).reindex(D.index).reindex(columns=D.columns)
    return {"H": H, "HI": HI, "QV": QV, "F": F, "D": D, "Fd": Fd}


def member_frame(members: dict, index: pd.DatetimeIndex, symbols) -> pd.DataFrame:
    months = pd.DatetimeIndex(index.tz_localize(None).to_period("M").to_timestamp()).tz_localize("UTC")
    return pd.DataFrame([[s in members.get(m, ()) for s in symbols] for m in months], index=index, columns=symbols)


def _fund_sum(f: pd.Series, t0, t1) -> float:
    if not len(f):
        return 0.0
    return float(f[(f.index > t0) & (f.index <= t1 + pd.Timedelta("1min"))].sum())


# ---------------------------------------------------------------- transversales diarias (H1, H9)
def cross_sectional(P, M, signal: pd.DataFrame, long_low: bool, weekly: bool, q=0.2):
    """signal[i-1] decide la cartera del día i. long_low=True: largo en el quintil de señal más BAJA, corto en la más alta."""
    D, Fd = P["D"], P["Fd"].fillna(0)
    R = D.pct_change(fill_method=None)
    out, w = [], pd.Series(dtype=float)
    for i in range(8, len(D)):
        day = D.index[i]
        if (not weekly) or day.dayofweek == 0 or w.empty:
            s = signal.iloc[i - 1][M.iloc[i]].dropna()
            s = s[D.iloc[i - 1][s.index].notna()]
            if len(s) >= 10:
                n = max(2, int(len(s) * q))
                rk = s.sort_values()
                lo, hi = rk.index[:n], rk.index[-n:]
                nw = pd.Series(0.0, index=s.index)
                nw[lo] = (0.5 if long_low else -0.5) / n
                nw[hi] = (-0.5 if long_low else 0.5) / n
                nw = nw[nw != 0]
            else:
                nw = pd.Series(dtype=float)
            allw = nw.index.union(w.index)
            turn = (nw.reindex(allw, fill_value=0) - w.reindex(allw, fill_value=0)).abs().sum()
            w = nw
        else:
            turn = 0.0
        if w.empty:
            out.append((day, 0.0)); continue
        r = R.iloc[i][w.index].fillna(0)
        out.append((day, float((w * r).sum() - (w * Fd.iloc[i][w.index]).sum() - turn * C_TURN)))
    return pd.Series(dict(out)), None


def h1(P, M, weekly):
    return cross_sectional(P, M, P["Fd"].rolling(7).mean(), long_low=True, weekly=weekly)


def h9(P, M):
    return cross_sectional(P, M, P["D"].pct_change(fill_method=None), long_low=True, weekly=False)


# ---------------------------------------------------------------- H3 cascadas
def h3(P, M, direction: int, k=4.0, vol_mult=3.0, hold=24, alloc=0.10):
    H, QV = P["H"], P["QV"]
    r = H.pct_change(fill_method=None)
    sd = r.rolling(168).std().shift(1)
    vr = QV / QV.rolling(168).mean().shift(1)
    Mh = M.reindex(H.index, method="ffill").fillna(False)
    cond = ((r < -k * sd) if direction == 1 else (r > k * sd)) & (vr > vol_mult) & Mh
    Hf = H.ffill()
    rows = []
    for s in H.columns:
        idx = np.flatnonzero(cond[s].to_numpy())
        c = Hf[s].to_numpy(); busy = -1
        for i in idx:
            if i <= busy or i + hold >= len(c):
                continue
            t0, t1 = H.index[i], H.index[i + hold]
            ret = direction * (c[i + hold] / c[i] - 1) - C_LEG - direction * _fund_sum(P["F"][s], t0, t1)
            rows.append((s, t0, t1, ret)); busy = i + hold
    tr = pd.DataFrame(rows, columns=["symbol", "entry", "exit", "ret"])
    daily = (tr.set_index("exit").ret * alloc).resample("1D").sum().reindex(P["D"].index, fill_value=0)
    return daily, tr


# ---------------------------------------------------------------- H4 estacionalidad
def h4(P, cost=0.0009):
    c = P["H"]["BTCUSDT"].dropna()
    a, b = c[c.index.hour == 20], c[c.index.hour == 22]      # cierres a las 21:00 y a las 23:00
    a.index, b.index = a.index.floor("1D"), b.index.floor("1D")
    return (b / a - 1 - cost).dropna(), None


# ---------------------------------------------------------------- H6 ratio alt/BTC
def h6(P, M, win=180, z_in=2.0, z_stop=4.0, max_bars=180, alloc=0.10):
    C4 = P["H"].resample("4h").last()
    M4 = M.reindex(C4.index, method="ffill").fillna(False)
    btc = C4["BTCUSDT"].to_numpy()
    rows = []
    for s in C4.columns:
        if s == "BTCUSDT":
            continue
        alt = C4[s].to_numpy()
        x = pd.Series(np.log(alt / btc))
        z = ((x - x.rolling(win).mean()) / x.rolling(win).std()).to_numpy()
        mem = M4[s].to_numpy()
        i, n = win, len(alt)
        while i < n - 1:
            if mem[i] and np.isfinite(z[i]) and z_in < abs(z[i]) < z_stop:
                d = -np.sign(z[i]); j = i + 1
                while j < n - 1 and j - i < max_bars and np.isfinite(z[j]) and z[j] * z[i] > 0 and abs(z[j]) <= z_stop:
                    j += 1
                if not (np.isfinite(alt[j]) and np.isfinite(btc[j])):
                    j -= 1
                ret = d * ((alt[j] / alt[i] - 1) - (btc[j] / btc[i] - 1)) - 2 * C_LEG
                rows.append((s, C4.index[i], C4.index[j], ret))
                i = j + 1
            else:
                i += 1
    tr = pd.DataFrame(rows, columns=["symbol", "entry", "exit", "ret"])
    daily = (tr.set_index("exit").ret * alloc).resample("1D").sum().reindex(P["D"].index, fill_value=0)
    return daily, tr


# ---------------------------------------------------------------- H10 nuevos listados
def h10(P, btc_close: pd.Series, btc_funding: pd.Series, wait_days=7, hold_days=60, stop_mult=2.0, alloc=0.05):
    H, HI = P["H"], P["HI"]
    rows = []
    for s in H.columns:
        c = H[s].dropna()
        if s == "BTCUSDT" or c.empty or c.index[0] < pd.Timestamp("2020-07-15", tz="UTC"):
            continue
        t0 = c.index[0] + pd.Timedelta(days=wait_days)
        t1 = t0 + pd.Timedelta(days=hold_days)
        seg = c[(c.index >= t0) & (c.index <= t1)]
        if len(seg) < 48:
            continue
        e = seg.iloc[0]; hi = HI[s].reindex(seg.index)
        stop = hi >= stop_mult * e
        if stop.iloc[1:].any():
            tx = stop.iloc[1:].idxmax(); px = stop_mult * e
        else:
            tx, px = seg.index[-1], seg.iloc[-1]
        b = btc_close.reindex([seg.index[0], tx], method="ffill")
        ret = -(px / e - 1) + (b.iloc[1] / b.iloc[0] - 1) + _fund_sum(P["F"][s], seg.index[0], tx) \
              - _fund_sum(btc_funding, seg.index[0], tx) - 2 * C_LEG
        rows.append((s, seg.index[0], tx, ret, bool(stop.iloc[1:].any())))
    tr = pd.DataFrame(rows, columns=["symbol", "entry", "exit", "ret", "stopped"])
    daily = (tr.set_index("exit").ret * alloc).resample("1D").sum().reindex(P["D"].index, fill_value=0)
    return daily, tr


# ---------------------------------------------------------------- métricas
def metrics(daily: pd.Series, trades: pd.DataFrame | None = None, a=None, b=None) -> dict:
    d = daily
    if a is not None:
        d = d[(d.index >= pd.Timestamp(a, tz="UTC")) & (d.index < pd.Timestamp(b, tz="UTC"))]
    eq = (1 + d).cumprod()
    yrs = max((d.index[-1] - d.index[0]).days / 365.25, 1e-9)
    out = {"sharpe": d.mean() / d.std() * np.sqrt(365) if d.std() > 0 else np.nan,
           "CAGR": eq.iloc[-1] ** (1 / yrs) - 1, "maxDD": (1 - eq / eq.cummax()).max()}
    x = d[d != 0] if trades is None else trades.ret
    if trades is not None and a is not None:
        x = trades.ret[(trades.entry >= pd.Timestamp(a, tz="UTC")) & (trades.entry < pd.Timestamp(b, tz="UTC"))]
    out.update({"n": len(x), "WR": (x > 0).mean() if len(x) else np.nan,
                "PF": x[x > 0].sum() / -x[x <= 0].sum() if (x <= 0).any() and x[x <= 0].sum() < 0 else np.nan,
                "media": x.mean() if len(x) else np.nan})
    return out
