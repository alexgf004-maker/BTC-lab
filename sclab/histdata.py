"""Convierte los ZIP de HistData (M1, hora EST fija = UTC−5) en velas de 1 hora en UTC: data/fxd/<PAR>.parquet."""
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "data/histdata", ROOT / "data/fxd"


def convert(pair):
    parts = []
    for f in sorted(SRC.glob(f"{pair}_*.zip")):
        try:
            with zipfile.ZipFile(f) as z:
                name = [n for n in z.namelist() if n.endswith(".csv")][0]
                d = pd.read_csv(io.BytesIO(z.read(name)), sep=";", header=None, names=["t", "open", "high", "low", "close", "v"])
        except Exception as e:
            print("fallo", f.name, e); continue
        parts.append(d)
    d = pd.concat(parts)
    t = pd.to_datetime(d.t, format="%Y%m%d %H%M%S") + pd.Timedelta("5h")
    df = d[["open", "high", "low", "close"]].set_index(pd.DatetimeIndex(t).tz_localize("UTC")).sort_index()
    df = df[~df.index.duplicated()]
    h = df.resample("1h", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    DST.mkdir(parents=True, exist_ok=True)
    h.to_parquet(DST / f"{pair}.parquet")
    return len(h), h.index[0], h.index[-1]


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, convert(p))
