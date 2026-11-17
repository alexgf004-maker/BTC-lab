"""Operaciones individuales de los primeros segundos tras la liquidación de las 00:00 UTC (descarga parcial del fichero diario)."""
import concurrent.futures as cf
import io
import struct
import urllib.request
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
B = "https://data.binance.vision/data/futures/um/daily/aggTrades"
OUT = ROOT / "data" / "cache" / "trades_tras_funding.parquet"
WINDOW_MS = 90_000


def fetch(item):
    sym, T = item
    t0 = int(T.timestamp() * 1000)
    url = f"{B}/{sym}/{sym}-aggTrades-{T:%Y-%m-%d}.zip"
    for nbytes in (400_000, 2_000_000, 8_000_000):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers={"Range": f"bytes=0-{nbytes - 1}"}), timeout=60).read()
        except Exception:
            return None
        n, m = struct.unpack("<HH", raw[26:30])
        try:
            txt = zlib.decompressobj(-15).decompress(raw[30 + n + m:])
        except zlib.error:
            return None
        txt = txt[: txt.rfind(b"\n")]
        hdr = 0 if txt[:1].isalpha() else None
        d = pd.read_csv(io.BytesIO(txt), header=hdr, usecols=[1, 2, 5, 6], names=None if hdr == 0 else list(range(7)))
        d.columns = ["price", "qty", "ms", "bm"]
        if d.ms.iloc[-1] >= t0 + WINDOW_MS or len(raw) < nbytes:
            break
    d = d[(d.ms >= t0) & (d.ms < t0 + WINDOW_MS)]
    if d.empty:
        return None
    return pd.DataFrame({"symbol": sym, "T": T, "dt": (d.ms - t0).astype("int32"), "price": d.price.astype("float64"),
                         "qty": d.qty.astype("float64"), "bm": d.bm.astype(str).str.lower().eq("true")})


if __name__ == "__main__":
    E = pd.read_parquet(ROOT / "data/cache/eventos_funding.parquet")
    E = E[(E.time.dt.hour == 0) & (E.time.dt.minute == 0)]
    items = list(zip(E.symbol, E.time))
    res = []
    with cf.ThreadPoolExecutor(24) as ex:
        for i, r in enumerate(ex.map(fetch, items)):
            if r is not None:
                res.append(r)
            if (i + 1) % 1000 == 0:
                print(i + 1, len(items), len(res), flush=True)
    pd.concat(res, ignore_index=True).to_parquet(OUT)
    print("eventos con operaciones:", len(res), "de", len(items), flush=True)
