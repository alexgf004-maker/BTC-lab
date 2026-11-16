"""Descarga masiva en paralelo desde data.binance.vision (velas 1h de futuros y spot, funding)."""
from __future__ import annotations

import concurrent.futures as cf
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
B = "https://data.binance.vision/data"


def _get(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except urllib.error.HTTPError:
        return False


def jobs(symbols, start="2020-01", end="2026-10", spot=True):
    months = pd.period_range(start, end, freq="M").strftime("%Y-%m")
    raw, fund, sp = ROOT / "data/raw", ROOT / "data/funding", ROOT / "data/spot"
    for d in (raw, fund, sp):
        d.mkdir(parents=True, exist_ok=True)
    for s in symbols:
        for m in months:
            yield f"{B}/futures/um/monthly/klines/{s}/1h/{s}-1h-{m}.zip", raw / f"{s}-1h-{m}.zip"
            yield f"{B}/futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{m}.zip", fund / f"{s}-fundingRate-{m}.zip"
            if spot:
                yield f"{B}/spot/monthly/klines/{s}/1h/{s}-1h-{m}.zip", sp / f"{s}-1h-{m}.zip"


def download(symbols, workers=24, **kw):
    js = list(jobs(symbols, **kw))
    with cf.ThreadPoolExecutor(workers) as ex:
        ok = sum(ex.map(lambda j: _get(*j), js))
    return ok, len(js)


if __name__ == "__main__":
    import sys
    syms = sys.argv[1:]
    print(download(syms))
