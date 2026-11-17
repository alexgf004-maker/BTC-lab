"""Descarga de Deribit: DVOL, precios de entrega y operaciones de opciones en la ventana del viernes 08:10–09:10 UTC."""
from __future__ import annotations

import concurrent.futures as cf
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/deribit"


def get(url, tries=6):
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(url, timeout=60).read())["result"]
        except Exception:
            time.sleep(2 ** i)
    raise RuntimeError(url)


def dvol(cur):
    rows, end = [], int(pd.Timestamp("2026-11-17", tz="UTC").timestamp() * 1000)
    start = int(pd.Timestamp("2021-03-01", tz="UTC").timestamp() * 1000)
    while end > start:
        r = get(f"https://www.deribit.com/api/v2/public/get_volatility_index_data?currency={cur}&start_timestamp={start}&end_timestamp={end}&resolution=3600")
        d = r["data"]
        if not d:
            break
        rows += d
        end = d[0][0] - 1
        if len(d) < 10:
            break
    df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c"]).drop_duplicates("t").sort_values("t")
    df.to_csv(OUT / f"dvol_{cur}.csv", index=False)
    return len(df)


def delivery(idx):
    rows, off = [], 0
    while True:
        r = get(f"https://www.deribit.com/api/v2/public/get_delivery_prices?index_name={idx}&offset={off}&count=1000")
        rows += r["data"]; off += len(r["data"])
        if off >= r["records_total"] or not r["data"]:
            break
    pd.DataFrame(rows).to_csv(OUT / f"delivery_{idx}.csv", index=False)
    return len(rows)


def window(cur, day):
    f = OUT / f"trades_{cur}_{day.date()}.json"
    if f.exists():
        return 0
    a = int((day + pd.Timedelta("8h10min")).timestamp() * 1000); b = int((day + pd.Timedelta("9h10min")).timestamp() * 1000)
    trades = []
    while True:
        r = get(f"https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time?currency={cur}&kind=option"
                f"&start_timestamp={a}&end_timestamp={b}&count=1000&sorting=asc")
        t = r["trades"]; trades += t
        if not r.get("has_more") or not t:
            break
        a = t[-1]["timestamp"] + 1
    keep = [{k: x[k] for k in ("timestamp", "instrument_name", "price", "mark_price", "iv", "index_price", "amount")} for x in trades]
    f.write_text(json.dumps(keep))
    return len(keep)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print("dvol", dvol("BTC"), dvol("ETH"))
    print("delivery", delivery("btc_usd"), delivery("eth_usd"))
    days = pd.date_range("2019-01-04", "2026-11-13", freq="W-FRI", tz="UTC")
    jobs = [(c, d) for c in ("BTC", "ETH") for d in days]
    with cf.ThreadPoolExecutor(6) as ex:
        n = list(ex.map(lambda j: window(*j), jobs))
    print("ventanas", len(jobs), "operaciones", sum(n))
