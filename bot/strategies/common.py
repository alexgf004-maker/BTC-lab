"""Piezas comunes: barras de 4h, filtro de tendencia diaria y stop chandelier (idénticos al backtest de sclab)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from sclab import indicators as ind  # noqa: E402

BAR = pd.Timedelta("4h")


def bars4_from_1h(h: pd.DataFrame) -> pd.DataFrame:
    df = h.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return df


def ratio_bars4(alt_close: pd.Series, btc_close: pd.Series) -> pd.DataFrame:
    """Ratio alt/BTC en 4h construido con los cierres de 1h (como en el backtest de S1)."""
    r = (alt_close / btc_close.reindex(alt_close.index)).dropna()
    df = r.resample("4h").agg(["first", "max", "min", "last"]).dropna()
    df.columns = ["open", "high", "low", "close"]
    return df


def with_trend_signals(df: pd.DataFrame, N: int, direction: int) -> pd.DataFrame:
    """Añade atr, filtro diaria (signo del cierre diario frente a su EMA50, solo días cerrados) y señal de ruptura."""
    df = df.copy()
    df["atr"] = ind.atr(df, 14)
    dd = df["close"].resample("1D").last().dropna()
    df["trend"] = ind.daily_on_intraday(np.sign(dd - ind.ema(dd, 50)), df.index, BAR)
    if direction == 1:
        df["signal"] = (df["trend"] > 0) & (df["close"] > df["high"].rolling(N).max().shift(1))
    else:
        df["signal"] = (df["trend"] < 0) & (df["close"] < df["low"].rolling(N).min().shift(1))
    return df


def chandelier_step(pos: dict, bar: pd.Series, atr_now: float, m: float, is_entry_bar: bool):
    """Procesa una vela cerrada de una posición abierta. Devuelve (precio de salida o None).
    Orden idéntico al motor del backtest: hueco en la apertura → toque del stop → actualizar extremo y stop."""
    d, stop = pos["side"], pos["stop"]
    if not is_entry_bar and (bar["open"] - stop) * d <= 0:
        return float(bar["open"])
    if ((bar["low"] if d == 1 else bar["high"]) - stop) * d <= 0:
        return float(stop)
    pos["ext"] = max(pos["ext"], bar["high"]) if d == 1 else min(pos["ext"], bar["low"])
    new = pos["ext"] - d * m * atr_now
    pos["stop"] = max(stop, new) if d == 1 else min(stop, new)
    return None
