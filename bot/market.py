"""Fuentes de datos de mercado con la misma interfaz:
- ReplayMarket: datos históricos de data.binance.vision, con un reloj que avanza hora a hora (para pruebas de paridad).
- LiveMarket: API de Binance (testnet o real).
Solo se devuelven velas CERRADAS en el instante `now`: el bot nunca ve el futuro.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data as hist  # noqa: E402

H = pd.Timedelta("1h")


class ReplayMarket:
    def __init__(self, now: pd.Timestamp):
        self.now = pd.Timestamp(now).tz_convert("UTC") if pd.Timestamp(now).tzinfo else pd.Timestamp(now, tz="UTC")

    @staticmethod
    @lru_cache(maxsize=None)
    def _bars(sym):
        return hist.load(sym, "1h")

    @staticmethod
    @lru_cache(maxsize=None)
    def _fund(sym):
        try:
            return hist.load_funding(sym)
        except Exception:
            return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))

    def candles(self, sym, lookback_hours=24 * 400):
        b = self._bars(sym)
        lo = self.now - pd.Timedelta(hours=lookback_hours)
        return b[(b.index >= lo) & (b.index + H <= self.now)]

    def funding(self, sym, since, until=None):
        f = self._fund(sym)
        until = until or self.now + pd.Timedelta("1min")          # los pagos llevan unos milisegundos de retraso
        return f[(f.index > since) & (f.index <= until)]

    @staticmethod
    @lru_cache(maxsize=None)
    def _spot(sym):
        from bot.lecciones_spot import spot_close
        return spot_close(sym)

    def spot_price(self, sym):
        s = self._spot(sym)
        if s is None:
            return float("nan")
        v = s.get(self.now, np.nan)               # apertura aproximada = cierre de la vela anterior
        prev = s[(s.index < self.now) & (s.index >= self.now - pd.Timedelta("8h"))]
        return float(prev.iloc[-1]) if len(prev) else float("nan")

    def price(self, sym):
        """Precio negociable en `now`: apertura de la vela que empieza en `now`."""
        b = self._bars(sym)
        return float(b["open"].get(self.now, np.nan))

    def bar_now(self, sym):
        b = self._bars(sym)
        return b.loc[self.now] if self.now in b.index else None


class LiveMarket:
    def __init__(self, client):
        self.c = client
        self.now = pd.Timestamp.now(tz="UTC").floor("1h")
        self._cache = {}

    def refresh_clock(self):
        self.now = pd.Timestamp.now(tz="UTC").floor("1h")
        self._cache = {}                         # la caché solo vale dentro de un ciclo

    def candles(self, sym, lookback_hours=24 * 400):
        key = (sym, self.now)
        hit = self._cache.get(key)
        if hit is not None and hit[0] >= lookback_hours:
            return hit[1][hit[1].index >= self.now - pd.Timedelta(hours=lookback_hours)]
        df = self._fetch(sym, lookback_hours)
        self._cache[key] = (lookback_hours, df)
        return df

    def _fetch(self, sym, lookback_hours):
        end = int(self.now.timestamp() * 1000) - 1
        start = int((self.now - pd.Timedelta(hours=lookback_hours)).timestamp() * 1000)
        rows = []
        while start < end:
            k = self.c.klines(sym, "1h", start_ms=start, end_ms=end, limit=1500)
            if not k:
                break
            rows += k
            start = k[-1][0] + 3600_000
            if len(k) < 1500:
                break
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "quote_volume"])
        df = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume", "ct", "quote_volume", "n", "tbv", "tbq", "x"])
        df.index = pd.to_datetime(df.t, unit="ms", utc=True)
        df = df[["open", "high", "low", "close", "volume", "quote_volume", "n", "tbv"]].astype(float).rename(
            columns={"tbv": "taker_buy_volume", "n": "count"})
        return df[df.index + H <= self.now]

    def spot_price(self, sym):
        k = self.c.spot_klines(sym, "1m", limit=1)
        return float(k[-1][4]) if k else float("nan")

    def funding(self, sym, since, until=None):
        f = self.c.funding_history(sym, start_ms=int(since.timestamp() * 1000) + 1)
        if not f:
            return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
        return pd.Series([float(x["fundingRate"]) for x in f], index=pd.to_datetime([x["fundingTime"] for x in f], unit="ms", utc=True))

    def price(self, sym):
        return float(self.c.premium_index(sym)["markPrice"])

    def last_price(self, sym):
        """Último precio negociado del perpetuo (vela de 1 min en curso)."""
        k = self.c.klines(sym, "1m", limit=1)
        return float(k[-1][4]) if k else float("nan")

    def coinbase_premium(self, days=34):
        """Prima horaria de Coinbase BTC-USD frente a Binance spot BTCUSDT (índice = hora en que se conoce el cierre)."""
        key = ("cbp", self.now, days)
        if key in self._cache:
            return self._cache[key]
        import requests
        start, rows, t = self.now - pd.Timedelta(days=days), [], None
        t = start
        while t < self.now:
            t2 = min(t + pd.Timedelta(hours=300), self.now)
            r = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/candles", timeout=15,
                             params={"granularity": 3600, "start": t.isoformat(), "end": t2.isoformat()},
                             headers={"User-Agent": "btclab-bot"})
            r.raise_for_status()
            rows += r.json()
            t = t2
        cb = pd.Series({pd.Timestamp(int(x[0]), unit="s", tz="UTC"): float(x[4]) for x in rows}).sort_index()
        k = self.c.spot_klines("BTCUSDT", "1h", start_ms=int(start.timestamp() * 1000), limit=1000)
        bs = pd.Series({pd.Timestamp(int(x[0]), unit="ms", tz="UTC"): float(x[4]) for x in k}).sort_index()
        prem = (cb / bs.reindex(cb.index) - 1).dropna()
        prem.index = prem.index + H
        prem = prem[prem.index <= self.now]
        self._cache[key] = prem
        return prem

    def premiums(self):
        """Prima del perpetuo frente a su índice spot (precio marcado / índice − 1) de todos los símbolos, una vez por ciclo."""
        key = ("premiums", self.now)
        if key not in self._cache:
            try:
                rows = self.c.premium_index()
                self._cache[key] = {r["symbol"]: float(r["markPrice"]) / float(r["indexPrice"]) - 1
                                    for r in rows if float(r.get("indexPrice") or 0) > 0}
            except Exception:
                self._cache[key] = {}
        return self._cache[key]
