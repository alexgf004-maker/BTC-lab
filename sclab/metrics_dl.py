"""Descarga de métricas de posicionamiento de Binance Futures (interés abierto y ratios largos/cortos, cada 5 min)."""
import concurrent.futures as cf
import io
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metrics"
B = "https://data.binance.vision/data/futures/um/daily/metrics"
COLS = ["create_time", "sum_open_interest", "sum_open_interest_value", "count_toptrader_long_short_ratio",
        "sum_toptrader_long_short_ratio", "count_long_short_ratio", "sum_taker_long_short_vol_ratio"]


def _day(sym, day):
    try:
        raw = urllib.request.urlopen(f"{B}/{sym}/{sym}-metrics-{day}.zip", timeout=30).read()
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        d = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
    d = d[COLS]
    d["create_time"] = pd.to_datetime(d["create_time"], utc=True)
    # se reduce a 1h (último valor de cada hora) para ahorrar espacio
    return d.set_index("create_time").resample("1h").last()


def symbol(sym, ex):
    f = OUT / f"{sym}.parquet"
    if f.exists():
        return 0
    days = pd.date_range("2020-09-01", "2026-10-31", freq="1D").strftime("%Y-%m-%d")
    parts = [p for p in ex.map(lambda d: _day(sym, d), days) if p is not None]
    if parts:
        pd.concat(parts).sort_index().to_parquet(f)
    return len(parts)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(48) as ex:
        for s in sys.argv[1:]:
            print(s, symbol(s, ex), flush=True)
