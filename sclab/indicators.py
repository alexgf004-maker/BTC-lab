"""Indicadores técnicos (sin dependencias externas)."""
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def rsi(s: pd.Series, n: int) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def daily_on_intraday(daily: pd.Series, intraday_index: pd.DatetimeIndex, bar: pd.Timedelta) -> pd.Series:
    """Proyecta un valor diario sobre velas intradía usando SOLO días ya cerrados
    en el momento del cierre de cada vela intradía (sin mirar al futuro)."""
    d = daily.copy()
    d.index = d.index + pd.Timedelta("1D")          # disponible al terminar el día
    closes = intraday_index + bar                    # momento del cierre de la vela
    v = d.reindex(d.index.union(closes)).ffill().reindex(closes)
    v.index = intraday_index
    return v
