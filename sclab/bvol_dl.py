"""Índice de volatilidad implícita de Binance (BVOL): descarga diaria y reducción a valores horarios."""
import concurrent.futures as cf
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def day(args):
    sym, d = args
    try:
        raw = urllib.request.urlopen(f"https://data.binance.vision/data/option/daily/BVOLIndex/{sym}/{sym}-BVOLIndex-{d}.zip", timeout=60).read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            x = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), usecols=["calc_time", "index_value"])
        x.index = pd.to_datetime(x.pop("calc_time"), unit="ms", utc=True)
        return x["index_value"].resample("1h").first()
    except Exception:
        return None


if __name__ == "__main__":
    days = pd.date_range("2023-01-01", "2026-10-31", freq="1D").strftime("%Y-%m-%d")
    out = {}
    with cf.ThreadPoolExecutor(16) as ex:
        for sym in ["BTCBVOLUSDT", "ETHBVOLUSDT"]:
            parts = [p for p in ex.map(day, [(sym, d) for d in days]) if p is not None]
            out[sym[:3]] = pd.concat(parts).sort_index()
            print(sym, len(parts), out[sym[:3]].index[0], flush=True)
    pd.DataFrame(out).to_parquet(ROOT / "data/cache/bvol.parquet")
