"""Descarga de datos públicos de Hyperliquid: funding horario y velas de 8h (con caché en parquet)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "data" / "hl"
URL = "https://api.hyperliquid.xyz/info"
START = int(pd.Timestamp("2023-05-12", tz="UTC").timestamp() * 1000)
END = int(pd.Timestamp("2026-11-01", tz="UTC").timestamp() * 1000)


def _post(body, pause=0.2):
    for attempt in range(8):
        try:
            r = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            out = json.load(urllib.request.urlopen(r, timeout=30))
            time.sleep(pause)
            return out
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("límite de peticiones de Hyperliquid")


def funding(coin: str) -> pd.Series:
    DIR.mkdir(parents=True, exist_ok=True)
    f = DIR / f"{coin}-funding.parquet"
    if f.exists():
        return pd.read_parquet(f)["rate"]
    rows, t = [], START
    while t < END:
        d = _post({"type": "fundingHistory", "coin": coin, "startTime": t, "endTime": END})
        if not d:
            break
        rows += [(x["time"], float(x["fundingRate"])) for x in d]
        if len(d) < 500:
            break
        t = d[-1]["time"] + 1
    s = pd.DataFrame(rows, columns=["t", "rate"])
    s.index = pd.to_datetime(s.pop("t"), unit="ms", utc=True).dt.floor("1h")
    s = s[~s.index.duplicated()]
    s.to_parquet(f)
    return s["rate"]


def candles_8h(coin: str) -> pd.DataFrame:
    """Velas de 8h indexadas por el momento de CIERRE."""
    DIR.mkdir(parents=True, exist_ok=True)
    f = DIR / f"{coin}-8h.parquet"
    if f.exists():
        return pd.read_parquet(f)
    d = _post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "8h", "startTime": START, "endTime": END}})
    df = pd.DataFrame([(x["t"], float(x["o"]), float(x["h"]), float(x["l"]), float(x["c"]), float(x["v"])) for x in d],
                      columns=["t", "open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df.pop("t"), unit="ms", utc=True) + pd.Timedelta("8h")
    df.to_parquet(f)
    return df


if __name__ == "__main__":
    import sys
    for c in sys.argv[1:]:
        k = candles_8h(c); fu = funding(c)
        print(c, len(k), len(fu), flush=True)
