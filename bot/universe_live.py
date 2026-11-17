"""Universos en vivo (point-in-time): se recalculan el día 1 de cada mes con el volumen de los 30 días previos."""
from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger("bot.universe")


class LiveUniverse:
    def __init__(self, client):
        self.c = client
        self._month = None
        self._vol: dict[str, float] = {}
        self._spot: set[str] = set()
        self._info = {}

    def _refresh(self, now):
        m = pd.Timestamp(now.year, now.month, 1, tz="UTC")
        if self._month == m:
            return
        info = self.c.exchange_info()
        self._info = {s["symbol"]: s for s in info["symbols"]}
        try:
            sp = self.c._request("GET", "spot", "/api/v3/exchangeInfo")
            self._spot = {s["symbol"] for s in sp["symbols"] if s["status"] == "TRADING" and s["quoteAsset"] == "USDT"}
        except Exception as e:
            log.warning("sin información de spot (%s): el carry queda desactivado", e)
            self._spot = set()
        cutoff = int((m - pd.Timedelta("60D")).timestamp() * 1000)
        vol = {}
        for sym, s in self._info.items():
            if s["status"] != "TRADING" or s["quoteAsset"] != "USDT" or s["contractType"] != "PERPETUAL" or s.get("underlyingType") != "COIN":
                continue
            if int(s.get("onboardDate", 0)) > cutoff:
                continue
            k = self.c.klines(sym, "1d", start_ms=int((m - pd.Timedelta("30D")).timestamp() * 1000), end_ms=int(m.timestamp() * 1000) - 1, limit=31)
            if len(k) >= 25:
                vol[sym] = sum(float(x[7]) for x in k)
        self._vol, self._month = vol, m
        log.info("universo de %s: %d perpetuos cripto con historia suficiente", m.date(), len(vol))

    def top(self, now, K, need_spot=False):
        self._refresh(now)
        v = {s: x for s, x in self._vol.items() if (not need_spot or s in self._spot)}
        return sorted(sorted(v, key=v.get, reverse=True)[:K])

    def equities(self, now):
        self._refresh(now)
        return sorted(s for s, x in self._info.items() if x["status"] == "TRADING" and x.get("underlyingType") == "EQUITY"
                      and x["contractType"] == "PERPETUAL" and x["quoteAsset"] == "USDT")
