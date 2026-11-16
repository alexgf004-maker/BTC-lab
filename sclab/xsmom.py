"""Momentum relativo semanal (Liu, Tsyvinski y Wu, 2022) con universo point-in-time."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .universe import is_member

COST = 0.0005 + 0.0002   # taker + slippage por unidad rotada


def weekly_returns(closes_d: pd.DataFrame, funding_d: pd.DataFrame, members: dict, lookback_days=21,
                   mode="long", quantile=0.2):
    """closes_d: cierres diarios (índice = inicio del día UTC); funding_d: suma diaria de funding."""
    mondays = closes_d.index[closes_d.index.dayofweek == 0]
    rows, w_prev = [], pd.Series(dtype=float)
    for t0, t1 in zip(mondays[:-1], mondays[1:]):
        # precio de decisión = cierre del día anterior a t0 (domingo), conocido a las 00:00 del lunes
        dec = t0 - pd.Timedelta("1D")
        past = dec - pd.Timedelta(f"{lookback_days}D")
        if past not in closes_d.index:
            continue
        elig = [s for s in closes_d.columns if is_member(members, s, pd.DatetimeIndex([t0]))[0]]
        p_now, p_past = closes_d.loc[dec, elig], closes_d.loc[past, elig]
        mom = (p_now / p_past - 1).dropna()
        if len(mom) < 10:
            continue
        n = max(2, int(len(mom) * quantile))
        rank = mom.sort_values()
        w = pd.Series(0.0, index=mom.index)
        if mode == "long":
            w[rank.index[-n:]] = 1 / n
        elif mode == "longshort":
            w[rank.index[-n:]] = 0.5 / n
            w[rank.index[:n]] = -0.5 / n
        elif mode == "market":
            w[:] = 1 / len(w)
        # rentabilidad de la semana: del cierre del domingo previo al del domingo siguiente;
        # si un activo deja de cotizar, se usa su último precio (captura los colapsos)
        end = t1 - pd.Timedelta("1D")
        seg = closes_d.loc[dec:end, w.index]
        p_end = seg.ffill().iloc[-1]
        r = (p_end / p_now - 1).fillna(-1.0)
        fund = funding_d.reindex(columns=w.index).loc[t0:end].sum().fillna(0)
        allw = w.index.union(w_prev.index)
        turnover = (w.reindex(allw, fill_value=0) - w_prev.reindex(allw, fill_value=0)).abs().sum()
        ret = (w * r).sum() - (w * fund).sum() - turnover * COST
        rows.append((t0, ret, turnover, len(mom)))
        w_prev = w
    return pd.DataFrame(rows, columns=["week", "ret", "turnover", "n_universe"]).set_index("week")
