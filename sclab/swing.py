"""Motor de backtest swing con entrada limit, salidas maker/taker y funding real.

Ver docs/leccion_02.md para las reglas de simulación (conservadoras).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .costs import MAKER, TAKER


@dataclass(frozen=True)
class SwingCosts:
    maker: float = MAKER
    taker: float = TAKER
    slip: float = 0.0002   # por orden a mercado


def simulate(df: pd.DataFrame, side: np.ndarray, limit: np.ndarray, risk: np.ndarray,
             rr: float, max_bars: int, funding: pd.Series | None = None,
             costs: SwingCosts = SwingCosts(), bar: pd.Timedelta = pd.Timedelta("4h")) -> pd.DataFrame:
    """side[i]: +1/-1/0 señal al cierre de la vela i.
    limit[i]: precio de la orden limit para la vela i+1.
    risk[i]: distancia del stop en precio (1R)."""
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    t = df.index
    t_ns = df.index.as_unit("ns").asi8
    n = len(df)
    f_t = funding.index.as_unit("ns").asi8 if funding is not None else None
    f_cum = np.concatenate([[0.0], np.cumsum(funding.to_numpy())]) if funding is not None else None
    rows, busy, missed = [], -1, 0
    for i in np.flatnonzero(side != 0):
        if i <= busy or i + 1 >= n or not (risk[i] > 0):
            continue
        d, j, lim = int(side[i]), i + 1, limit[i]
        if d == 1:
            if o[j] <= lim: fill = o[j]
            elif l[j] <= lim: fill = lim
            else: missed += 1; continue
        else:
            if o[j] >= lim: fill = o[j]
            elif h[j] >= lim: fill = lim
            else: missed += 1; continue
        R = risk[i]
        stop, tp = fill - d * R, fill + d * rr * R
        exit_px, why, k = None, "time", j
        last = min(j + max_bars, n) - 1
        for k in range(j, last + 1):
            if k > j and (o[k] - stop) * d <= 0:
                exit_px, why = o[k], "sl"; break
            if (l[k] if d == 1 else h[k]) * d <= stop * d:
                exit_px, why = stop, "sl"; break
            if k > j and (h[k] if d == 1 else l[k]) * d >= tp * d:
                exit_px, why = tp, "tp"; break
        if exit_px is None:
            exit_px, k = c[last], last
        fee = fill * costs.maker + exit_px * (costs.maker if why == "tp" else costs.taker + costs.slip)
        fund = 0.0
        if funding is not None:
            a = np.searchsorted(f_t, t_ns[j], side="right")
            b = np.searchsorted(f_t, t_ns[k] + bar.value, side="right")
            fund = d * (f_cum[b] - f_cum[a]) * fill      # >0 = pagamos
        gross = d * (exit_px - fill)
        rows.append((t[i], t[k] + bar, d, fill, exit_px, why, gross / R, (gross - fee - fund) / R))
        busy = k
    out = pd.DataFrame(rows, columns=["signal_time", "exit_time", "side", "entry", "exit",
                                      "reason", "r_gross", "r_net"])
    out.attrs["missed"] = missed
    return out


def stats(r: pd.Series) -> dict:
    if len(r) == 0:
        return {"trades": 0, "win_rate": np.nan, "E_R": np.nan, "PF": np.nan, "total_R": 0.0}
    w, ls = r[r > 0].sum(), -r[r <= 0].sum()
    return {"trades": len(r), "win_rate": (r > 0).mean(), "E_R": r.mean(),
            "PF": w / ls if ls > 0 else np.inf, "total_R": r.sum()}
