"""Descarga de HistData (ASCII, M1) mediante su formulario público de descarga. Guarda data/histdata/<PAR>_<periodo>.zip.
Uso: python3 sclab/histdata_dl.py XAUUSD 2012 2026"""
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "histdata"
S = requests.Session()


def fetch(pair, year, month=None):
    tag = f"{year}{month:02d}" if month else f"{year}"
    f = OUT / f"{pair}_{tag}.zip"
    if f.exists() and f.stat().st_size > 1000:
        return "ya"
    page = f"https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair.lower()}/{year}" + (f"/{month}" if month else "")
    html = S.get(page, timeout=60).text
    fields = dict(re.findall(r'name="(tk|date|datemonth|platform|timeframe|fxpair)" id="\w+" value="([^"]*)"', html))
    if "tk" not in fields:
        return "sin formulario"
    r = S.post("https://www.histdata.com/get.php", data=fields, headers={"Referer": page}, timeout=180)
    if r.status_code != 200 or r.content[:2] != b"PK":
        return f"fallo {r.status_code}"
    f.write_bytes(r.content)
    return f"{len(r.content) // 1024} KB"


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    pair, y0, y1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    for y in range(y0, y1 + 1):
        if y < y1:
            print(pair, y, fetch(pair, y), flush=True); time.sleep(2)
        else:
            for m in range(1, 13):
                res = fetch(pair, y, m)
                print(pair, y, m, res, flush=True); time.sleep(2)
                if res == "sin formulario":
                    break
