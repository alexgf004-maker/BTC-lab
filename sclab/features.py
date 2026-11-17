"""Biblioteca de variables para la Lección 11 (todas conocidas al cierre de cada vela de 4h)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import data

ROOT = Path(__file__).resolve().parent.parent
D = 6                     # velas de 4h por día
HORIZONS = {"4h": 1, "24h": 6, "72h": 18}


def bars4(sym):
    h = data.load(sym, "1h")
    return h.resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last",
                                 "quote_volume": "sum", "volume": "sum", "taker_buy_volume": "sum"}).dropna()


def base_features(b: pd.DataFrame, btc: pd.DataFrame, fund: pd.Series) -> pd.DataFrame:
    c, r = b["close"], np.log(b["close"]).diff()
    f = pd.DataFrame(index=b.index)
    for name, k in [("4h", 1), ("8h", 2), ("24h", 6), ("3d", 18), ("7d", 42), ("14d", 84), ("30d", 180), ("60d", 360)]:
        f[f"ret_{name}"] = c / c.shift(k) - 1
    for n in (7, 30, 90):
        f[f"dist_max_{n}d"] = c / b["high"].rolling(n * D).max() - 1
        f[f"dist_min_{n}d"] = c / b["low"].rolling(n * D).min() - 1
    f["vol_1d"], f["vol_7d"], f["vol_30d"] = r.rolling(D).std(), r.rolling(7 * D).std(), r.rolling(30 * D).std()
    f["vol_ratio"] = f["vol_1d"] / f["vol_30d"]
    f["asim_7d"] = r.rolling(7 * D).skew()
    f["max_ret_7d"] = r.rolling(7 * D).max()
    f["rango"] = (b["high"] - b["low"]) / c
    qv = b["quote_volume"]
    f["volumen_1d_30d"] = qv.rolling(D).mean() / qv.rolling(30 * D).mean()
    f["amihud_7d"] = (r.abs() / qv.replace(0, np.nan)).rolling(7 * D).mean()
    f["tamano"] = np.log(qv.rolling(30 * D).mean())
    tb, v = b["taker_buy_volume"], b["volume"].replace(0, np.nan)
    f["compras_4h"] = tb / v
    f["compras_24h"] = tb.rolling(D).sum() / v.rolling(D).sum()
    f["compras_7d"] = tb.rolling(7 * D).sum() / v.rolling(7 * D).sum()
    rb = np.log(btc["close"]).diff().reindex(b.index)
    cov = r.rolling(30 * D).cov(rb)
    f["beta_30d"] = cov / rb.rolling(30 * D).var()
    f["corr_30d"] = r.rolling(30 * D).corr(rb)
    bc = btc["close"].reindex(b.index)
    f["resid_1d"] = f["ret_24h"] - f["beta_30d"] * (bc / bc.shift(D) - 1)
    f["resid_7d"] = f["ret_7d"] - f["beta_30d"] * (bc / bc.shift(7 * D) - 1)
    # funding pagado dentro de cada vela (se conoce al cierre)
    f4 = fund.groupby((fund.index - pd.Timedelta("1min")).floor("4h")).sum().reindex(b.index).fillna(0) if len(fund) else pd.Series(0.0, index=b.index)
    f["fund_ultimo"] = f4.rolling(2).sum()
    f["fund_3d"] = f4.rolling(3 * D).sum()
    f["fund_7d"] = f4.rolling(7 * D).sum()
    f["fund_cambio"] = f["fund_3d"] / 3 - f4.rolling(30 * D).sum() / 30
    f["_f4"] = f4
    return f


def positioning_features(b: pd.DataFrame, sym: str) -> pd.DataFrame:
    p = ROOT / "data" / "metrics" / f"{sym}.parquet"
    f = pd.DataFrame(index=b.index)
    names = ["oi_4h", "oi_24h", "oi_7d", "oi_sobre_volumen", "ls_grandes", "ls_grandes_cambio", "ls_global",
             "ls_global_cambio", "ratio_agresivo", "divergencia_oi"]
    if not p.exists():
        for n in names:
            f[n] = np.nan
        return f
    m = pd.read_parquet(p).resample("4h").last().reindex(b.index)
    oi = m["sum_open_interest"].replace(0, np.nan)
    f["oi_4h"], f["oi_24h"], f["oi_7d"] = oi / oi.shift(1) - 1, oi / oi.shift(D) - 1, oi / oi.shift(7 * D) - 1
    f["oi_sobre_volumen"] = m["sum_open_interest_value"] / b["quote_volume"].rolling(D).sum()
    f["ls_grandes"] = m["sum_toptrader_long_short_ratio"]
    f["ls_grandes_cambio"] = f["ls_grandes"] - f["ls_grandes"].shift(D)
    f["ls_global"] = m["count_long_short_ratio"]
    f["ls_global_cambio"] = f["ls_global"] - f["ls_global"].shift(D)
    f["ratio_agresivo"] = m["sum_taker_long_short_vol_ratio"]
    f["divergencia_oi"] = f["oi_24h"] - (b["close"] / b["close"].shift(D) - 1)
    return f


POS = ["oi_4h", "oi_24h", "oi_7d", "oi_sobre_volumen", "ls_grandes", "ls_grandes_cambio", "ls_global",
       "ls_global_cambio", "ratio_agresivo", "divergencia_oi"]
MKT = ["btc_ret_24h", "btc_ret_7d", "btc_vol_7d", "amplitud", "fund_medio"]


def build_panel(symbols, members: dict) -> pd.DataFrame:
    """Panel largo (time, symbol) con variables, objetivos, pertenencia al universo y funding futuro."""
    btc = bars4("BTCUSDT")
    parts = []
    for s in symbols:
        b = bars4(s)
        try:
            fund = data.load_funding(s)
        except ValueError:
            fund = pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
        f = base_features(b, btc, fund).join(positioning_features(b, s))
        c = b["close"]
        for name, k in HORIZONS.items():
            f[f"fwd_{name}"] = c.shift(-k) / c - 1
            f[f"ffund_{name}"] = f["_f4"].shift(-k).rolling(k).sum()      # funding pagado durante la tenencia
        months = pd.DatetimeIndex(b.index.tz_localize(None).to_period("M").to_timestamp()).tz_localize("UTC")
        f["miembro"] = [s in members.get(m, ()) for m in months]
        f["symbol"] = s
        parts.append(f.drop(columns="_f4").reset_index(names="time"))
    P = pd.concat(parts, ignore_index=True)
    P = P[P.time >= pd.Timestamp("2020-03-01", tz="UTC")]
    # estado del mercado
    rb = np.log(btc["close"]).diff()
    mk = pd.DataFrame({"btc_ret_24h": btc["close"] / btc["close"].shift(D) - 1,
                       "btc_ret_7d": btc["close"] / btc["close"].shift(7 * D) - 1, "btc_vol_7d": rb.rolling(7 * D).std()})
    mem = P[P.miembro]
    mk["amplitud"] = (mem.assign(up=mem.ret_30d > 0).groupby("time").up.mean())
    mk["fund_medio"] = mem.groupby("time").fund_3d.mean()
    P = P.merge(mk.reset_index(names="time"), on="time", how="left")
    return P.set_index(["time", "symbol"]).sort_index()


def feature_names(P, positioning: bool, market: bool = False):
    skip = {"miembro"} | {c for c in P.columns if c.startswith(("fwd_", "ffund_"))}
    cols = [c for c in P.columns if c not in skip and c not in MKT and (positioning or c not in POS)]
    return cols + (MKT if market else [])
