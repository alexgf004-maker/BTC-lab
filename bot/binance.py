"""Cliente REST mínimo de Binance (futuros USDⓈ-M, spot y margen) con firma HMAC, reintentos y reglas de cada símbolo.

Las claves se leen de variables de entorno (BINANCE_API_KEY / BINANCE_API_SECRET); nunca se escriben en ficheros.
Las claves deben tener SOLO permisos de lectura y trading (nunca de retirada).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import math
import os
import time
import urllib.parse

import requests

log = logging.getLogger("bot.binance")

URLS = {
    "live": {"fut": "https://fapi.binance.com", "spot": "https://api.binance.com"},
    "testnet": {"fut": "https://testnet.binancefuture.com", "spot": "https://testnet.binance.vision"},
}


class BinanceError(RuntimeError):
    def __init__(self, status, code, msg):
        super().__init__(f"HTTP {status} código {code}: {msg}")
        self.status, self.code, self.msg = status, code, msg


class Binance:
    def __init__(self, env: str = "testnet", key: str | None = None, secret: str | None = None, timeout: int = 15):
        self.env = env
        self.base = URLS[env]
        self.key = key if key is not None else os.environ.get("BINANCE_API_KEY", "")
        self.secret = (secret if secret is not None else os.environ.get("BINANCE_API_SECRET", "")).encode()
        self.timeout = timeout
        self.s = requests.Session()
        self._rules: dict[str, dict] = {}
        self._time_offset = 0

    # ------------------------------------------------------------------ transporte
    def _request(self, method, market, path, params=None, signed=False, retries=4):
        params = dict(params or {})
        url = self.base[market] + path
        headers = {"X-MBX-APIKEY": self.key} if (signed or self.key) else {}
        for attempt in range(retries):
            p = dict(params)
            if signed:
                p["timestamp"] = int(time.time() * 1000) + self._time_offset
                p.setdefault("recvWindow", 5000)
                q = urllib.parse.urlencode(p, doseq=True)
                p["signature"] = hmac.new(self.secret, q.encode(), hashlib.sha256).hexdigest()
            try:
                r = self.s.request(method, url, params=p if method in ("GET", "DELETE") else None,
                                   data=p if method in ("POST", "PUT") else None, headers=headers, timeout=self.timeout)
            except requests.RequestException as e:
                log.warning("red: %s (intento %d)", e, attempt + 1)
                time.sleep(2 ** attempt)
                continue
            if r.status_code in (418, 429) or r.status_code >= 500:
                wait = int(r.headers.get("Retry-After", 2 ** attempt))
                log.warning("HTTP %s en %s, espero %ss", r.status_code, path, wait)
                time.sleep(wait)
                continue
            body = r.json() if r.content else {}
            if r.status_code >= 400:
                code = body.get("code") if isinstance(body, dict) else None
                if code == -1021 and attempt < retries - 1:          # reloj desincronizado
                    self.sync_time(market); continue
                raise BinanceError(r.status_code, code, body.get("msg") if isinstance(body, dict) else body)
            return body
        raise BinanceError(0, None, f"sin respuesta tras {retries} intentos: {path}")

    def sync_time(self, market="fut"):
        path = "/fapi/v1/time" if market == "fut" else "/api/v3/time"
        t = self._request("GET", market, path)["serverTime"]
        self._time_offset = t - int(time.time() * 1000)

    # ------------------------------------------------------------------ datos públicos (futuros)
    def exchange_info(self):
        info = self._request("GET", "fut", "/fapi/v1/exchangeInfo")
        for s in info["symbols"]:
            f = {x["filterType"]: x for x in s["filters"]}
            self._rules[s["symbol"]] = {
                "tick": float(f["PRICE_FILTER"]["tickSize"]), "step": float(f["LOT_SIZE"]["stepSize"]),
                "min_qty": float(f["LOT_SIZE"]["minQty"]), "mkt_step": float(f.get("MARKET_LOT_SIZE", f["LOT_SIZE"])["stepSize"]),
                "min_notional": float(f.get("MIN_NOTIONAL", {}).get("notional", 5)), "status": s["status"],
                "type": s.get("underlyingType"), "contract": s.get("contractType"), "onboard": s.get("onboardDate")}
        return info

    def rules(self, symbol):
        if not self._rules:
            self.exchange_info()
        return self._rules[symbol]

    def klines(self, symbol, interval="1h", start_ms=None, end_ms=None, limit=1500):
        p = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_ms: p["startTime"] = start_ms
        if end_ms: p["endTime"] = end_ms
        return self._request("GET", "fut", "/fapi/v1/klines", p)

    def funding_history(self, symbol, start_ms=None, limit=1000):
        p = {"symbol": symbol, "limit": limit}
        if start_ms: p["startTime"] = start_ms
        return self._request("GET", "fut", "/fapi/v1/fundingRate", p)

    def premium_index(self, symbol=None):
        return self._request("GET", "fut", "/fapi/v1/premiumIndex", {"symbol": symbol} if symbol else None)

    def ticker_24h(self):
        return self._request("GET", "fut", "/fapi/v1/ticker/24hr")

    def spot_klines(self, symbol, interval="1h", start_ms=None, limit=1000):
        p = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_ms: p["startTime"] = start_ms
        return self._request("GET", "spot", "/api/v3/klines", p)

    # ------------------------------------------------------------------ privado (futuros)
    def account(self):
        return self._request("GET", "fut", "/fapi/v2/account", signed=True)

    def positions(self):
        return [p for p in self._request("GET", "fut", "/fapi/v2/positionRisk", signed=True) if float(p["positionAmt"]) != 0]

    def set_leverage(self, symbol, lev):
        return self._request("POST", "fut", "/fapi/v1/leverage", {"symbol": symbol, "leverage": lev}, signed=True)

    def round_qty(self, symbol, qty, market=True):
        r = self.rules(symbol)
        step = r["mkt_step"] if market else r["step"]
        q = math.floor(abs(qty) / step) * step
        return round(q, 10)

    def round_price(self, symbol, price):
        t = self.rules(symbol)["tick"]
        return round(round(price / t) * t, 10)

    def order(self, symbol, side, qty, type_="MARKET", price=None, stop_price=None, reduce_only=False, client_id=None):
        p = {"symbol": symbol, "side": side, "type": type_, "quantity": f"{qty:.10f}".rstrip("0").rstrip(".")}
        if price is not None:
            p["price"] = f"{self.round_price(symbol, price)}"; p["timeInForce"] = "GTC"
        if stop_price is not None:
            p["stopPrice"] = f"{self.round_price(symbol, stop_price)}"; p["workingType"] = "MARK_PRICE"
        if reduce_only:
            p["reduceOnly"] = "true"
        if client_id:
            p["newClientOrderId"] = client_id[:36]
        p["newOrderRespType"] = "RESULT"
        return self._request("POST", "fut", "/fapi/v1/order", p, signed=True)

    def open_orders(self, symbol=None):
        return self._request("GET", "fut", "/fapi/v1/openOrders", {"symbol": symbol} if symbol else None, signed=True)

    def cancel_order(self, symbol, client_id):
        return self._request("DELETE", "fut", "/fapi/v1/order", {"symbol": symbol, "origClientOrderId": client_id}, signed=True)

    def cancel_all(self, symbol):
        return self._request("DELETE", "fut", "/fapi/v1/allOpenOrders", {"symbol": symbol}, signed=True)

    # ------------------------------------------------------------------ privado (spot y margen)
    def spot_order(self, symbol, side, qty, client_id=None):
        p = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": f"{qty:.10f}".rstrip("0").rstrip("."), "newOrderRespType": "FULL"}
        if client_id: p["newClientOrderId"] = client_id[:36]
        return self._request("POST", "spot", "/api/v3/order", p, signed=True)

    def margin_max_borrowable(self, asset):
        return float(self._request("GET", "spot", "/sapi/v1/margin/maxBorrowable", {"asset": asset}, signed=True)["amount"])

    def margin_interest_rate(self, asset):
        r = self._request("GET", "spot", "/sapi/v1/margin/next-hourly-interest-rate", {"assets": asset, "isIsolated": "FALSE"}, signed=True)
        return float(r[0]["nextHourlyInterestRate"]) if r else None

    def margin_borrow_repay(self, asset, amount, kind):            # kind: "BORROW" | "REPAY"
        return self._request("POST", "spot", "/sapi/v1/margin/borrow-repay", {"asset": asset, "amount": amount, "type": kind, "isIsolated": "FALSE"}, signed=True)

    def spot_balances(self):
        a = self._request("GET", "spot", "/api/v3/account", {"omitZeroBalances": "true"}, signed=True)
        return {b["asset"]: float(b["free"]) + float(b["locked"]) for b in a["balances"]}

    def margin_account(self):
        a = self._request("GET", "spot", "/sapi/v1/margin/account", signed=True)
        return {"nivel": float(a.get("marginLevel", 999)),
                "activos": {x["asset"]: {"libre": float(x["free"]), "prestado": float(x["borrowed"]), "interes": float(x["interest"]),
                                         "neto": float(x["netAsset"])} for x in a["userAssets"]}}

    def transfer(self, asset, amount, kind):
        """Transferencia INTERNA entre cuentas propias (no es una retirada). kind: MAIN_UMFUTURE, UMFUTURE_MAIN,
        MARGIN_UMFUTURE, UMFUTURE_MARGIN, MAIN_MARGIN, MARGIN_MAIN. Requiere el permiso de transferencia universal en la clave."""
        return self._request("POST", "spot", "/sapi/v1/asset/transfer", {"type": kind, "asset": asset, "amount": f"{amount:.4f}"}, signed=True)

    def margin_order(self, symbol, side, qty, client_id=None, side_effect="NO_SIDE_EFFECT"):
        p = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": f"{qty:.10f}".rstrip("0").rstrip("."), "sideEffectType": side_effect}
        if client_id: p["newClientOrderId"] = client_id[:36]
        return self._request("POST", "spot", "/sapi/v1/margin/order", p, signed=True)
