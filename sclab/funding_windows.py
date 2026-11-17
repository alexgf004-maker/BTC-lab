"""Descarga las velas de 1m alrededor de cada evento de funding extremo (T-60 … T+60 min)."""
import concurrent.futures as cf
import io
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
B = "https://data.binance.vision/data/futures/um/daily/klines"
OUT = ROOT / "data" / "cache" / "ventanas_funding.parquet"


def day_file(sym, day):
    try:
        raw = urllib.request.urlopen(f"{B}/{sym}/1m/{sym}-1m-{day:%Y-%m-%d}.zip", timeout=40).read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            b = z.read(z.namelist()[0])
        hdr = 0 if b[:1].isalpha() else None
        d = pd.read_csv(io.BytesIO(b), header=hdr, usecols=[0, 1, 2, 3, 4])
        d.columns = ["t", "open", "high", "low", "close"]
        d.index = pd.to_datetime(d.pop("t"), unit="ms", utc=True)
        return d.astype("float64")
    except Exception:
        return None


def work(item):
    (sym, day), times = item
    days = {day}
    for T in times:
        days.add((T - pd.Timedelta("60min")).floor("1D")); days.add((T + pd.Timedelta("60min")).floor("1D"))
    parts = [p for p in (day_file(sym, d) for d in sorted(days)) if p is not None]
    if not parts:
        return []
    m = pd.concat(parts).sort_index()
    m = m[~m.index.duplicated()]
    out = []
    for T in times:
        w = m[(m.index >= T - pd.Timedelta("60min")) & (m.index <= T + pd.Timedelta("60min"))]
        if len(w) < 100:
            continue
        w = w.assign(symbol=sym, T=T, off=((w.index - T).total_seconds() // 60).astype(int))
        out.append(w.reset_index(drop=True))
    return out


if __name__ == "__main__":
    E = pd.read_parquet(ROOT / "data/cache/eventos_funding.parquet")
    groups = {k: list(v) for k, v in E.groupby(["symbol", E.time.dt.floor("1D")]).time}
    res, done = [], 0
    with cf.ThreadPoolExecutor(24) as ex:
        for r in ex.map(work, groups.items()):
            res += r; done += 1
            if done % 1000 == 0:
                print(done, len(groups), len(res), flush=True)
    pd.concat(res, ignore_index=True).to_parquet(OUT)
    print("eventos con ventana:", len(res), "de", len(E), flush=True)
