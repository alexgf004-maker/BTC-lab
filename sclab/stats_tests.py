"""Deflated Sharpe Ratio (Bailey y López de Prado, 2014)."""
import numpy as np
from scipy.stats import norm, skew, kurtosis

EULER = 0.5772156649


def expected_max_sharpe(n_trials: int, var_sr: float) -> float:
    """Sharpe máximo esperado por azar entre n_trials pruebas sin ventaja (por periodo)."""
    return np.sqrt(var_sr) * ((1 - EULER) * norm.ppf(1 - 1 / n_trials) + EULER * norm.ppf(1 - 1 / (n_trials * np.e)))


def deflated_sharpe(returns: np.ndarray, n_trials: int, var_sr: float) -> dict:
    r = np.asarray(returns)
    sr = r.mean() / r.std(ddof=1)
    sr0 = expected_max_sharpe(n_trials, var_sr)
    g3, g4 = skew(r), kurtosis(r, fisher=False)
    z = (sr - sr0) * np.sqrt(len(r) - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return {"SR_diario": sr, "SR0_azar": sr0, "DSR": norm.cdf(z)}
