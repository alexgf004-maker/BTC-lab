"""Descarga y carga de velas de futuros USDⓈ-M de Binance (data.binance.vision)."""
from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "cache"
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def download(symbol: str, months: list[str], interval: str = "1m") -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for m in months:
        f = RAW / f"{symbol}-{interval}-{m}.zip"
        if not f.exists():
            urllib.request.urlretrieve(f"{BASE}/{symbol}/{interval}/{f.name}", f)


def _read_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        raw = z.read(z.namelist()[0])
    first = raw.split(b"\n", 1)[0]
    header = 0 if first.startswith(b"open_time") else None
    df = pd.read_csv(io.BytesIO(raw), header=header, names=None if header == 0 else COLS)
    return df


def load(symbol: str, interval: str = "1m") -> pd.DataFrame:
    """Devuelve OHLCV indexado por tiempo UTC (inicio de la vela)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    pq = CACHE / f"{symbol}-{interval}.parquet"
    files = sorted(RAW.glob(f"{symbol}-{interval}-*.zip"))
    if pq.exists() and pq.stat().st_mtime > max(f.stat().st_mtime for f in files):
        return pd.read_parquet(pq)
    df = pd.concat([_read_zip(f) for f in files], ignore_index=True)
    df["time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = (df.set_index("time")[["open", "high", "low", "close", "volume",
                                "quote_volume", "count", "taker_buy_volume"]]
            .astype(float).sort_index())
    df = df[~df.index.duplicated()]
    df.to_parquet(pq)
    return df


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Agrega velas de 1m a otro marco ('5min', '15min'...)."""
    agg = {"open": "first", "high": "max", "low": "min", "close": "last",
           "volume": "sum", "quote_volume": "sum", "count": "sum", "taker_buy_volume": "sum"}
    return df.resample(rule, label="left", closed="left").agg(agg).dropna()


FUNDING = ROOT / "data" / "funding"


def load_funding(symbol: str) -> pd.Series:
    """Tasa de funding por pago (fracción), indexada por hora UTC del pago."""
    parts = []
    for f in sorted(FUNDING.glob(f"{symbol}-fundingRate-*.zip")):
        with zipfile.ZipFile(f) as z:
            raw = z.read(z.namelist()[0])
        hdr = 0 if raw[:1].isalpha() else None
        d = pd.read_csv(io.BytesIO(raw), header=hdr)
        d.columns = ["calc_time", "interval_h", "rate"][: d.shape[1]] if hdr is None else d.columns
        d = d.rename(columns={"last_funding_rate": "rate"})
        parts.append(d[["calc_time", "rate"]])
    d = pd.concat(parts)
    s = pd.Series(d["rate"].astype(float).to_numpy(),
                  index=pd.to_datetime(d["calc_time"], unit="ms", utc=True)).sort_index()
    return s[~s.index.duplicated()]
