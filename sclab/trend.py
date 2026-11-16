"""Motor de seguimiento de tendencia: entrada a mercado, stop chandelier, funding real.

Reglas (docs/leccion_03.md):
- Señal al cierre de i -> entrada a la apertura de i+1 (taker + slippage).
- Stop inicial = entrada - d*m*ATR[i]  (1R).
- Al cierre de cada vela k: stop = max(stop, extremo_desde_entrada - m*ATR[k]) (largos).
  El nuevo stop se aplica a partir de la vela k+1 (sin mirar al futuro).
- Gap más allá del stop: salida a la apertura.
- Parcial opcional: frac en +tp1 R con limit (maker); solo a partir de la vela siguiente a la entrada,
  y si en la misma vela se tocan stop y TP1 se asume el stop.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .swing import SwingCosts


def simulate(df: pd.DataFrame, side: np.ndarray, m: float, funding: pd.Series | None = None,
             costs: SwingCosts = SwingCosts(), bar: pd.Timedelta = pd.Timedelta("4h"),
             partial: tuple[float, float] | None = None) -> pd.DataFrame:
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    a = df["atr"].to_numpy()
    t, t_ns = df.index, df.index.as_unit("ns").asi8
    n = len(df)
    if funding is not None:
        f_t = funding.index.as_unit("ns").asi8
        f_cum = np.concatenate([[0.0], np.cumsum(funding.to_numpy())])
    rows, busy = [], -1
    for i in np.flatnonzero(side != 0):
        if i <= busy or i + 1 >= n or not (a[i] > 0):
            continue
        d, j = int(side[i]), i + 1
        entry = o[j]
        R = m * a[i]
        stop = entry - d * R
        ext = entry
        p_done, p_r = False, 0.0
        exit_px, k = None, j
        for k in range(j, n):
            if k > j and (o[k] - stop) * d <= 0:
                exit_px = o[k]; break
            if ((l[k] if d == 1 else h[k]) - stop) * d <= 0:
                exit_px = stop; break
            if partial and not p_done and k > j:
                tp1 = entry + d * partial[1] * R
                if ((h[k] if d == 1 else l[k]) - tp1) * d >= 0:
                    p_done = True
                    p_r = (d * (tp1 - entry) - tp1 * costs.maker) / R
            ext = max(ext, h[k]) if d == 1 else min(ext, l[k])
            new = ext - d * m * a[k]
            stop = max(stop, new) if d == 1 else min(stop, new)
        if exit_px is None:          # sigue abierta al final de los datos: cerrar al último cierre
            exit_px, k = c[n - 1], n - 1
        fee_in = entry * (costs.taker + costs.slip)
        fee_out = exit_px * (costs.taker + costs.slip)
        fund = 0.0
        if funding is not None:
            fa = np.searchsorted(f_t, t_ns[j], side="right")
            fb = np.searchsorted(f_t, t_ns[k] + bar.value, side="right")
            fund = d * (f_cum[fb] - f_cum[fa]) * entry
        r_full = (d * (exit_px - entry) - fee_in - fee_out - fund) / R
        if partial and p_done:
            f = partial[0]
            r_net = f * (p_r - (fee_in + fund) / R) + (1 - f) * r_full
        else:
            r_net = r_full
        rows.append((t[i], t[k] + bar, d, entry, exit_px, k - j + 1,
                     d * (exit_px - entry) / R, r_net, p_done))
        busy = k
    return pd.DataFrame(rows, columns=["signal_time", "exit_time", "side", "entry", "exit",
                                       "bars", "r_gross", "r_net", "partial_hit"])
