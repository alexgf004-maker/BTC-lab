"""Gestión del riesgo: tamaño de posición y Monte Carlo de drawdowns."""
from __future__ import annotations
import numpy as np


def position_size(equity: float, risk_frac: float, entry: float, stop: float) -> float:
    """Cantidad de moneda tal que, si salta el stop, se pierde risk_frac del capital."""
    return equity * risk_frac / abs(entry - stop)


def notional_leverage(risk_frac: float, stop_pct: float) -> float:
    """Apalancamiento nocional implícito: riesgo / distancia del stop."""
    return risk_frac / stop_pct


def monte_carlo(r_trades: np.ndarray, risk_frac: float, n_trades: int = 300,
                n_sims: int = 20000, seed: int = 0) -> dict:
    """Remuestrea resultados en R con interés compuesto. Devuelve percentiles de DD y retorno."""
    rng = np.random.default_rng(seed)
    r = rng.choice(r_trades, size=(n_sims, n_trades), replace=True)
    eq = np.cumprod(1 + risk_frac * r, axis=1)
    eq = np.clip(eq, 1e-9, None)
    peak = np.maximum.accumulate(np.concatenate([np.ones((n_sims, 1)), eq], axis=1), axis=1)[:, 1:]
    dd = 1 - eq / peak
    max_dd = dd.max(axis=1)
    final = eq[:, -1] - 1
    streak = np.zeros(n_sims, int)
    for s in range(n_sims):
        neg = r[s] < 0
        best = cur = 0
        for v in neg:
            cur = cur + 1 if v else 0
            best = max(best, cur)
        streak[s] = best
    return {"dd_p50": np.median(max_dd), "dd_p95": np.percentile(max_dd, 95),
            "P(dd>30%)": (max_dd > 0.30).mean(), "P(dd>50%)": (max_dd > 0.50).mean(),
            "ret_p5": np.percentile(final, 5), "ret_p50": np.median(final),
            "P(perder)": (final < 0).mean(), "racha_p95": np.percentile(streak, 95)}
