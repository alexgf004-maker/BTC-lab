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


def run(cands: pd.DataFrame, closes: dict[str, pd.Series], risk: float, K: int = 99,
        breakers: bool = False, dd_half: float = 0.15, dd_stop: float = 0.30):
    idx = sorted(set().union(*[set(s.index) for s in closes.values()]))
    idx = pd.DatetimeIndex(idx)
    bar = idx[1] - idx[0]
    px = pd.DataFrame(closes).reindex(idx).ffill()
    syms = list(px.columns)
    P = px.to_numpy()
    col = {s: i for i, s in enumerate(syms)}
    pos_of = {ts: i for i, ts in enumerate(idx)}
    c = cands.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    by_entry = {}
    for r in c.itertuples():
        by_entry.setdefault(r.entry_time, []).append(r)
    balance, peak, halted = 1.0, 1.0, False
    open_pos = {}      # symbol -> dict
    taken, eq, lev = [], np.empty(len(idx)), np.zeros(len(idx))
    for b, T in enumerate(idx):
        # 1) salidas que ocurrieron durante la vela anterior (exit_time == T)
        for s in [s for s, p in open_pos.items() if p["exit_time"] <= T]:
            p = open_pos.pop(s)
            pnl = p["risk_usd"] * p["r_net"]
            balance += pnl
            taken.append({**p, "pnl": pnl, "balance_after": balance})
        # 2) capital marcado a mercado con el cierre de la vela anterior
        prev = max(b - 1, 0)
        unreal = sum(p["risk_usd"] * p["side"] * (P[prev, col[s]] - p["entry"]) / p["R"] for s, p in open_pos.items())
        equity = balance + unreal
        peak = max(peak, equity)
        dd = 1 - equity / peak
        if breakers:   # histéresis: se para con DD > dd_stop y se reanuda con DD < dd_half
            halted = (dd > dd_stop) or (halted and dd >= dd_half)
        # 3) entradas a la apertura de T
        for r in by_entry.get(T, []):
            if r.symbol in open_pos or len(open_pos) >= K:
                continue
            rk = risk
            if breakers:
                if halted:
                    continue
                if dd > dd_half:
                    rk = risk / 2
            risk_usd = rk * balance
            open_pos[r.symbol] = {"symbol": r.symbol, "entry_time": r.entry_time, "exit_time": r.exit_time,
                                  "side": r.side, "entry": r.entry, "R": r.R, "r_net": r.r_net,
                                  "risk_usd": risk_usd, "units": risk_usd / r.R}
        eq[b] = equity
        lev[b] = sum(p["units"] * P[b, col[s]] for s, p in open_pos.items()) / max(equity, 1e-12)
    curve = pd.Series(eq, idx)
    return curve, pd.DataFrame(taken), pd.Series(lev, idx)


def metrics(curve: pd.Series, lev: pd.Series | None = None) -> dict:
    years = (curve.index[-1] - curve.index[0]).days / 365.25
    dd = 1 - curve / curve.cummax()
    m = curve.resample("ME").last()
    mret = m.pct_change().dropna()
    under = (curve < curve.cummax()).astype(int)
    grp = (under.diff() != 0).cumsum()
    longest = (under.groupby(grp).sum() * (curve.index[1] - curve.index[0])).max()
    out = {"final_x": curve.iloc[-1] / curve.iloc[0], "CAGR": (curve.iloc[-1] / curve.iloc[0]) ** (1 / years) - 1,
           "maxDD": dd.max(), "peor_mes": mret.min(), "meses_pos": (mret > 0).mean(),
           "max_bajo_agua_dias": longest.days}
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
