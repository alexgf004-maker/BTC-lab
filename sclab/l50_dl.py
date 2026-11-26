"""Descargas de la Lección 50: velas spot de 1 h (data.binance.vision) y TVL de DefiLlama."""
from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data, universe  # noqa: E402

SPOT = ROOT / "data" / "spot1h"; TVL = ROOT / "data" / "tvl"
CHAINS = {"ETH": "Ethereum", "SOL": "Solana", "BNB": "BSC", "AVAX": "Avalanche", "TRX": "Tron", "MATIC": "Polygon", "POL": "Polygon",
          "ADA": "Cardano", "NEAR": "Near", "FTM": "Fantom", "S": "Sonic", "SUI": "Sui", "APT": "Aptos", "ARB": "Arbitrum", "OP": "Optimism",
          "TON": "TON", "INJ": "Injective", "SEI": "Sei", "ALGO": "Algorand", "KAVA": "Kava", "LUNA": "Terra"}
PROTOS = {"UNI": "uniswap", "AAVE": "aave", "CRV": "curve-dex", "MKR": "makerdao", "LDO": "lido", "COMP": "compound-finance",
          "SNX": "synthetix", "CAKE": "pancakeswap", "SUSHI": "sushi", "DYDX": "dydx", "GMX": "gmx", "PENDLE": "pendle",
          "JUP": "jupiter", "RAY": "raydium"}


def spot_month(sym, m):
    r = None
    for k in range(5):
        try:
            r = requests.get(f"https://data.binance.vision/data/spot/monthly/klines/{sym}/1h/{sym}-1h-{m}.zip", timeout=60)
            break
        except requests.RequestException:
            time.sleep(3 * (k + 1))
    if r is None or r.status_code != 200:
        return None
    z = zipfile.ZipFile(io.BytesIO(r.content)); d = pd.read_csv(z.open(z.namelist()[0]), header=None)
    t = d[0].astype("int64"); t = t.where(t < 1e14, t // 1000)
    return pd.DataFrame({"close": d[4].astype(float).to_numpy(), "quote_volume": d[7].astype(float).to_numpy()},
                        index=pd.DatetimeIndex(pd.to_datetime(t, unit="ms", utc=True), name="time"))


def spot(sym, start="2019-12"):
    f = SPOT / f"{sym}.parquet"
    if f.exists():
        return
    parts = [x for x in (spot_month(sym, p.strftime("%Y-%m")) for p in pd.period_range(start, "2026-10", freq="M")) if x is not None]
    if parts:
        pd.concat(parts).sort_index().to_parquet(f)


def base(sym):
    b = sym[:-4]
    for p in ("1000000", "1000"):
        if b.startswith(p) and len(b) > len(p):
            return b[len(p):]
    return b


def tvl():
    TVL.mkdir(parents=True, exist_ok=True)
    for tok, ch in CHAINS.items():
        f = TVL / f"{tok}.parquet"
        if f.exists():
            continue
        r = requests.get(f"https://api.llama.fi/v2/historicalChainTvl/{ch}", timeout=60)
        if r.status_code == 200 and r.json():
            s = pd.Series({pd.Timestamp(int(x["date"]), unit="s", tz="UTC"): float(x["tvl"]) for x in r.json()})
            s.sort_index().to_frame("tvl").to_parquet(f); print("TVL cadena", tok, len(s), flush=True)
        else:
            print("TVL cadena", tok, "NO DISPONIBLE", r.status_code, flush=True)
        time.sleep(0.5)
    for tok, slug in PROTOS.items():
        f = TVL / f"{tok}.parquet"
        if f.exists():
            continue
        js, code = {}, None
        for k in range(3):
            try:
                r = requests.get(f"https://api.llama.fi/protocol/{slug}", timeout=240)
                code = r.status_code
                js = r.json() if r.status_code == 200 else {}
                break
            except requests.RequestException as e:
                code = type(e).__name__; time.sleep(5 * (k + 1))
        rows = js.get("tvl") or []
        if rows:
            s = pd.Series({pd.Timestamp(int(x["date"]), unit="s", tz="UTC"): float(x["totalLiquidityUSD"]) for x in rows})
            s = s.groupby(s.index.floor("1D")).last()
            s.sort_index().to_frame("tvl").to_parquet(f); print("TVL protocolo", tok, len(s), flush=True)
        else:
            print("TVL protocolo", tok, "NO DISPONIBLE", code, flush=True)
        time.sleep(0.5)


if __name__ == "__main__":
    SPOT.mkdir(parents=True, exist_ok=True)
    tvl()
    spot("PAXGUSDT", "2020-08")
    print("PAXG listo", flush=True)
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    mem = universe.monthly_members(vol, 30)
    syms = sorted({base(s) + "USDT" for s in set().union(*mem.values())})
    first = vol.apply(lambda c: c.first_valid_index())
    def job(s):
        perp = next((p for p in first.index if base(p) + "USDT" == s), None)
        st = max(pd.Timestamp("2019-12-01", tz="UTC"), first[perp] - pd.Timedelta("62D")) if perp is not None and pd.notna(first[perp]) else pd.Timestamp("2019-12-01", tz="UTC")
        spot(s, st.strftime("%Y-%m"))
        return s
    with ThreadPoolExecutor(4) as ex:
        for i, s in enumerate(ex.map(job, syms)):
            if i % 20 == 0:
                print("spot", i, "/", len(syms), s, flush=True)
    print("FIN", flush=True)
