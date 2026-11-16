"""Simulación de cartera: un capital, interés compuesto, límite de posiciones y corta-circuitos.

Entrada: lista de trades CANDIDATOS (todas las señales, sin bloqueo por activo) generada por
trend.simulate(one_at_a_time=False). La cartera decide cuáles se toman:
- no se abre un activo que ya está en posición;
- no se abre si hay K posiciones abiertas;
- corta-circuitos por drawdown (marcado a mercado).
Riesgo $ = riesgo% × saldo realizado al entrar. Curva de capital marcada a mercado cada vela.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def run(cands: pd.DataFrame, closes: dict[str, pd.Series], risk: float, K: int = 999,
        breakers: bool = False, dd_half: float = 0.15, dd_stop: float = 0.30,
        vol_target: float | None = None, vol_window: int = 60, vol_clip: tuple = (0.5, 1.5)):
    """cands: columnas obligatorias symbol, entry_time, exit_time, side, entry, R, r_net.
    Opcionales: key (una posición por key; por defecto el símbolo), risk_mult (por defecto 1),
    cid/parent (un añadido solo se toma si su trade padre está abierto)."""
    idx = pd.DatetimeIndex(sorted(set().union(*[set(s.index) for s in closes.values()])))
    bar = idx[1] - idx[0]
    per_day = int(pd.Timedelta("1D") / bar)
    px = pd.DataFrame(closes).reindex(idx).ffill()
    P = px.to_numpy()
    col = {s: i for i, s in enumerate(px.columns)}
    c = cands.copy()
    if "key" not in c: c["key"] = c["symbol"]
    if "risk_mult" not in c: c["risk_mult"] = 1.0
    if "cid" not in c: c["cid"] = np.arange(len(c))
    if "parent" not in c: c["parent"] = -1
    c = c.sort_values(["entry_time", "parent", "symbol"]).reset_index(drop=True)
    by_entry = {}
    for r in c.itertuples():
        by_entry.setdefault(r.entry_time, []).append(r)
    balance, peak, halted = 1.0, 1.0, False
    open_pos, open_cids = {}, set()
    taken, eq, lev, daily = [], np.empty(len(idx)), np.zeros(len(idx)), []
    for b, T in enumerate(idx):
        for key in [k for k, p in open_pos.items() if p["exit_time"] <= T]:
            p = open_pos.pop(key)
            open_cids.discard(p["cid"])
            pnl = p["risk_usd"] * p["r_net"]
            balance += pnl
            taken.append({**p, "pnl": pnl, "balance_after": balance})
        prev = max(b - 1, 0)
        unreal = sum(p["risk_usd"] * p["side"] * (P[prev, col[p["symbol"]]] - p["entry"]) / p["R"]
                     for p in open_pos.values())
        equity = balance + unreal
        peak = max(peak, equity)
        dd = 1 - equity / peak
        if b % per_day == 0:
            daily.append(equity)
        scale = 1.0
        if vol_target and len(daily) > 21:
            d = np.diff(np.log(daily[-(vol_window + 1):]))
            rv = d.std() * np.sqrt(365)
            if rv > 0:
                scale = float(np.clip(vol_target / rv, *vol_clip))
        if breakers:
            halted = (dd > dd_stop) or (halted and dd >= dd_half)
        for r in by_entry.get(T, []):
            if r.key in open_pos or len(open_pos) >= K:
                continue
            if r.parent >= 0 and r.parent not in open_cids:
                continue
            rk = risk * r.risk_mult * scale
            if breakers:
                if halted: continue
                if dd > dd_half: rk /= 2
            risk_usd = rk * balance
            open_pos[r.key] = {"symbol": r.symbol, "key": r.key, "cid": r.cid, "entry_time": r.entry_time,
                               "exit_time": r.exit_time, "side": r.side, "entry": r.entry, "R": r.R,
                               "r_net": r.r_net, "risk_usd": risk_usd, "units": risk_usd / r.R}
            open_cids.add(r.cid)
        eq[b] = equity
        lev[b] = sum(p["units"] * P[b, col[p["symbol"]]] for p in open_pos.values()) / max(equity, 1e-12)
    return pd.Series(eq, idx), pd.DataFrame(taken), pd.Series(lev, idx)


def metrics(curve: pd.Series, lev: pd.Series | None = None) -> dict:
    years = (curve.index[-1] - curve.index[0]).days / 365.25
    dd = 1 - curve / curve.cummax()
    m = curve.resample("ME").last()
    mret = m.pct_change().dropna()
    under = (curve < curve.cummax()).astype(int)
    grp = (under.diff() != 0).cumsum()
    longest = (under.groupby(grp).sum() * (curve.index[1] - curve.index[0])).max()
    dr = curve.resample("1D").last().pct_change().dropna()
    out = {"sharpe": dr.mean() / dr.std() * np.sqrt(365) if dr.std() > 0 else np.nan, "final_x": curve.iloc[-1] / curve.iloc[0], "CAGR": (curve.iloc[-1] / curve.iloc[0]) ** (1 / years) - 1,
           "maxDD": dd.max(), "peor_mes": mret.min(), "meses_pos": (mret > 0).mean(),
           "max_bajo_agua_dias": longest.days}
    out["MAR"] = out["CAGR"] / out["maxDD"] if out["maxDD"] > 0 else np.nan
    if lev is not None:
        out["lev_max"] = lev.max()
    return out


def block_bootstrap(curve: pd.Series, months: int = 36, block: int = 3, n: int = 10000, seed: int = 0) -> dict:
    """Remuestrea rendimientos DIARIOS en bloques de `block` meses para conservar rachas y correlación."""
    d = curve.resample("1D").last().pct_change().dropna().to_numpy()
    L = 30 * block
    rng = np.random.default_rng(seed)
    nb = months // block
    starts = rng.integers(0, len(d) - L, size=(n, nb))
    paths = np.stack([np.concatenate([d[s:s + L] for s in row]) for row in starts])
    eq = np.cumprod(1 + paths, axis=1)
    dd = 1 - eq / np.maximum.accumulate(eq, axis=1)
    cagr = eq[:, -1] ** (12 / months) - 1
    return {"CAGR_p50": np.median(cagr), "CAGR_p5": np.percentile(cagr, 5),
            "DD_p50": np.median(dd.max(1)), "DD_p95": np.percentile(dd.max(1), 95),
            "P(perder 3a)": (eq[:, -1] < 1).mean()}
