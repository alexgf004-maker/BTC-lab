"""Universo point-in-time por rango de volumen (p. ej. puestos 31–100), con la misma lógica que universe.monthly_members."""
import pandas as pd


def monthly_rank_members(vol: pd.DataFrame, lo: int, hi: int, min_history_days: int = 60) -> dict:
    first = vol.apply(lambda c: c.first_valid_index())
    out = {}
    for m in pd.date_range(pd.Timestamp("2020-03-01", tz="UTC"), vol.index[-1], freq="MS"):
        win = vol[(vol.index >= m - pd.Timedelta("30D")) & (vol.index < m)]
        ok = [s for s in vol.columns if pd.notna(first[s]) and first[s] <= m - pd.Timedelta(f"{min_history_days}D")
              and win[s].notna().sum() >= 25]
        rank = win[ok].sum().sort_values(ascending=False)
        out[m] = set(rank.index[lo:hi])
    return out
