"""bookDepth de futuros: descarga diaria y reducción a 5 minutos (desequilibrios al ±1 % y ±5 %)."""
import concurrent.futures as cf, io, sys, urllib.request, zipfile
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "bookdepth"


def day(args):
    sym, d = args
    try:
        raw = urllib.request.urlopen(f"https://data.binance.vision/data/futures/um/daily/bookDepth/{sym}/{sym}-bookDepth-{d}.zip", timeout=60).read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            x = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
    except Exception:
        return None
    x["timestamp"] = pd.to_datetime(x["timestamp"], utc=True)
    p = x.pivot_table(index="timestamp", columns="percentage", values="notional", aggfunc="last")
    if not {-1, 1, -5, 5} <= set(p.columns):
        return None
    f = pd.DataFrame({"obi1": (p[-1] - p[1]) / (p[-1] + p[1]), "obi5": (p[-5] - p[5]) / (p[-5] + p[5])}, index=p.index)
    return f.resample("5min").last()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    days = pd.date_range("2023-01-01", "2026-10-31", freq="1D").strftime("%Y-%m-%d")
    with cf.ThreadPoolExecutor(32) as ex:
        for s in sys.argv[1:]:
            parts = [p for p in ex.map(day, [(s, d) for d in days]) if p is not None]
            pd.concat(parts).sort_index().to_parquet(OUT / f"{s}.parquet")
            print(s, len(parts), "días", flush=True)
