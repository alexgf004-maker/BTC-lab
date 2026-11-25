"""Velas de 4 h de Upbit (mercados KRW) para las monedas del top 30 de Binance (Lección 48, U). Guarda data/upbit/<MONEDA>.parquet."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import universe  # noqa: E402

OUT = ROOT / "data" / "upbit"
S = requests.Session()


def base(sym):
    b = sym[:-4]
    for p in ("1000000", "1000"):
        if b.startswith(p) and len(b) > len(p):
            return b[len(p):]
    return b


def get(url, params):
    for k in range(6):
        r = S.get(url, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        time.sleep(1 + 2 * k)                                  # 429: esperar y reintentar (límite de Upbit)
    r.raise_for_status()


def candles(market, start="2019-10-01"):
    rows, to = [], None
    while True:
        p = {"market": market, "count": 200}
        if to:
            p["to"] = to
        js = get("https://api.upbit.com/v1/candles/minutes/240", p)
        if not js:
            break
        rows += js
        last = js[-1]["candle_date_time_utc"]
        to = last.replace("T", " ")
        if last < start or len(js) < 200:
            break
        time.sleep(0.15)
    if not rows:
        return None
    d = pd.DataFrame(rows).drop_duplicates("candle_date_time_utc")
    d.index = pd.to_datetime(d["candle_date_time_utc"]).dt.tz_localize("UTC")
    return d[["trade_price", "candle_acc_trade_price"]].rename(columns={"trade_price": "close", "candle_acc_trade_price": "krw_vol"}).sort_index()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    vol = universe.daily_volume(sorted(set(OLD + NEW)))
    vol.to_parquet(ROOT / "data" / "vol_diario.parquet")
    mem = universe.monthly_members(vol, 30)
    syms = sorted(set().union(*mem.values()))
    krw = {x["market"] for x in get("https://api.upbit.com/v1/market/all", {})}
    todo = sorted({base(s) for s in syms if f"KRW-{base(s)}" in krw} | {"BTC"})
    print(f"top 30 histórico: {len(syms)} monedas; con mercado KRW en Upbit: {len(todo)}", flush=True)
    for b in todo:
        f = OUT / f"{b}.parquet"
        if f.exists():
            continue
        d = candles(f"KRW-{b}")
        if d is not None:
            d.to_parquet(f)
            print(b, len(d), d.index[0].date(), flush=True)
