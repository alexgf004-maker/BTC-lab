"""Descarga de indicadores de flujo (Lección 47): Coinbase BTC-USD 1 h, Upbit KRW-BTC diario, spot Binance BTCUSDT 1 h,
dólar/won (FRED) y oferta total de stablecoins (DefiLlama). Todo se guarda en data/flujos/ en parquet."""
from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "flujos"
S = requests.Session()


def _get(url, params=None, tries=5):
    for k in range(tries):
        r = S.get(url, params=params, timeout=30)
        if r.status_code == 200:
            return r
        time.sleep(2 * (k + 1))                                  # respetar el límite de peticiones
    r.raise_for_status()


def coinbase(start="2019-09-01", end="2026-11-01"):
    rows, t = [], pd.Timestamp(start, tz="UTC")
    end = pd.Timestamp(end, tz="UTC")
    while t < end:
        t2 = min(t + pd.Timedelta(hours=300), end)
        r = _get("https://api.exchange.coinbase.com/products/BTC-USD/candles",
                 {"granularity": 3600, "start": t.isoformat(), "end": t2.isoformat()})
        rows += r.json()
        t = t2
        time.sleep(0.4)
    df = pd.DataFrame(rows, columns=["time", "low", "high", "open", "close", "volume"]).drop_duplicates("time")
    df.index = pd.to_datetime(df.pop("time"), unit="s", utc=True)
    return df.sort_index()


def upbit():
    rows, to = [], None
    while True:
        p = {"market": "KRW-BTC", "count": 200}
        if to:
            p["to"] = to
        js = _get("https://api.upbit.com/v1/candles/days", p).json()
        if not js:
            break
        rows += js
        to = js[-1]["candle_date_time_utc"].replace("T", " ")
        if js[-1]["candle_date_time_utc"] < "2018-01-01":
            break
        time.sleep(0.3)
    df = pd.DataFrame(rows).drop_duplicates("candle_date_time_utc")
    df.index = pd.to_datetime(df["candle_date_time_utc"]).dt.tz_localize("UTC")
    return df[["opening_price", "trade_price"]].rename(columns={"opening_price": "open", "trade_price": "close"}).sort_index()


def binance_spot(months):
    out = []
    for m in months:
        url = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{m}.zip"
        z = zipfile.ZipFile(io.BytesIO(_get(url).content))
        d = pd.read_csv(z.open(z.namelist()[0]), header=None)
        t = d[0].astype("int64")
        t = t.where(t < 1e14, t // 1000)                          # desde 2025 el spot viene en microsegundos
        out.append(pd.DataFrame({"close": d[4].astype(float).to_numpy()}, index=pd.DatetimeIndex(pd.to_datetime(t, unit="ms", utc=True), name="time")))
    return pd.concat(out).sort_index()


def fred_krw():
    d = pd.read_csv(io.StringIO(_get("https://fred.stlouisfed.org/graph/fredgraph.csv", {"id": "DEXKOUS"}).text))
    d.columns = ["date", "krw"]
    d["krw"] = pd.to_numeric(d["krw"], errors="coerce")
    return d.dropna().set_index(pd.to_datetime(d.dropna()["date"]).dt.tz_localize("UTC"))["krw"]


def stablecoins():
    js = _get("https://stablecoins.llama.fi/stablecoincharts/all").json()
    s = pd.Series({pd.Timestamp(int(x["date"]), unit="s", tz="UTC"): x["totalCirculatingUSD"].get("peggedUSD", float("nan")) for x in js})
    return s.sort_index().rename("supply")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    months = [p.strftime("%Y-%m") for p in pd.period_range("2019-09", "2026-10", freq="M")]
    for name, fn in (("stablecoins", stablecoins), ("krw", fred_krw), ("upbit", upbit),
                     ("binance_spot", lambda: binance_spot(months)), ("coinbase", coinbase)):
        f = OUT / f"{name}.parquet"
        if f.exists():
            continue
        x = fn()
        (x.to_frame() if isinstance(x, pd.Series) else x).to_parquet(f)
        print(name, len(x), x.index[0], x.index[-1], flush=True)
