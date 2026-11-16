"""Universo point-in-time: cada mes, los K activos más líquidos según los 30 días previos."""
from __future__ import annotations

import pandas as pd

from . import data


def daily_volume(symbols) -> pd.DataFrame:
    cols = {}
    for s in symbols:
        h = data.load(s, "1h")
        cols[s] = h["quote_volume"].resample("1D").sum(min_count=1)
    return pd.DataFrame(cols)


def monthly_members(vol: pd.DataFrame, K: int, min_history_days: int = 60) -> dict:
    """{inicio_de_mes: set(símbolos)} usando SOLO datos anteriores al inicio de cada mes."""
    first = vol.apply(lambda c: c.first_valid_index())
    out = {}
    for m in pd.date_range(pd.Timestamp("2020-03-01", tz="UTC"), vol.index[-1], freq="MS"):
        win = vol[(vol.index >= m - pd.Timedelta("30D")) & (vol.index < m)]
        ok = [s for s in vol.columns if pd.notna(first[s]) and first[s] <= m - pd.Timedelta(f"{min_history_days}D")
              and win[s].notna().sum() >= 25]
        out[m] = set(win[ok].sum().sort_values(ascending=False).head(K).index)
    return out


def is_member(members: dict, symbol: str, times: pd.DatetimeIndex):
    """Vector booleano: ¿el símbolo pertenece al universo del mes de cada instante?"""
    months = pd.DatetimeIndex(times.tz_convert("UTC").tz_localize(None).to_period("M").to_timestamp()).tz_localize("UTC")
    return months.map(lambda m: symbol in members.get(m, set())).to_numpy(bool)
