"""Motor de backtest por barras, deliberadamente conservador.

Reglas de simulación:
- La señal se evalúa al CIERRE de la vela i; la entrada es en la APERTURA de i+1
  (nunca usamos información del futuro).
- Stop y take profit fijos en precio. Si en una misma vela se tocan ambos,
  se asume que salta primero el STOP (peor caso).
- Si la vela abre más allá del stop (gap), se sale al precio de apertura.
- Salida por tiempo opcional (max_bars) al cierre de la vela.
- Costes aplicados sobre el nocional de entrada y salida.
Resultados en R: +RR si toca TP, ~-1 si toca SL, menos costes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .costs import CostModel


def simulate(df: pd.DataFrame, signals: pd.Series, stop_dist: pd.Series,
             rr: float, cost: CostModel, max_bars: int = 60,
             one_at_a_time: bool = True) -> pd.DataFrame:
    """signals: +1 largo, -1 corto, 0 nada (evaluado al cierre de cada vela).
    stop_dist: distancia del stop en PRECIO para cada vela de señal."""
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    sig = signals.reindex(df.index).fillna(0).to_numpy()
    sd = stop_dist.reindex(df.index).to_numpy()
    idx = df.index
    n = len(df)
    out = []
    i, busy_until = 0, -1
    cand = np.flatnonzero(sig != 0)
    for i in cand:
        if one_at_a_time and i <= busy_until:
            continue
        j = i + 1
        if j >= n or not np.isfinite(sd[i]) or sd[i] <= 0:
            continue
        d = int(sig[i])
        entry = o[j]
        stop = entry - d * sd[i]
        tp = entry + d * rr * sd[i]
        exit_px, reason, k = None, None, j
        for k in range(j, min(j + max_bars, n)):
            if d == 1:
                if o[k] <= stop and k > j:
                    exit_px, reason = o[k], "sl_gap"; break
                if l[k] <= stop:
                    exit_px, reason = stop, "sl"; break
                if h[k] >= tp:
                    exit_px, reason = tp, "tp"; break
            else:
                if o[k] >= stop and k > j:
                    exit_px, reason = o[k], "sl_gap"; break
                if h[k] >= stop:
                    exit_px, reason = stop, "sl"; break
                if l[k] <= tp:
                    exit_px, reason = tp, "tp"; break
        if exit_px is None:
            exit_px, reason = c[k], "time"
        gross = d * (exit_px - entry)
        fees = entry * cost.entry_fee + exit_px * cost.exit_fee
        slip = entry * cost.slippage + (exit_px * cost.slippage if reason != "tp" else 0)
        out.append((idx[j], idx[k], d, entry, exit_px, reason,
                    gross / sd[i], (gross - fees - slip) / sd[i]))
        busy_until = k
    return pd.DataFrame(out, columns=["entry_time", "exit_time", "side", "entry",
                                      "exit", "reason", "r_gross", "r_net"])


def stats(trades: pd.DataFrame, col: str = "r_net") -> dict:
    if trades.empty:
        return {"trades": 0}
    r = trades[col]
    wins, losses = r[r > 0], r[r <= 0]
    eq = r.cumsum()
    dd = (eq - eq.cummax()).min()
    pf = wins.sum() / -losses.sum() if losses.sum() < 0 else np.inf
    return {"trades": len(r), "win_rate": len(wins) / len(r), "E_R": r.mean(),
            "PF": pf, "total_R": r.sum(), "max_dd_R": dd}
