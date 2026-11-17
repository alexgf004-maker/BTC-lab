"""Ejecución: PaperBroker (simulada, sin dinero) y ExchangeBroker (testnet o real).
Los dos devuelven Fill(precio, cantidad, comisión) con la misma interfaz."""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

log = logging.getLogger("bot.broker")

TAKER, MAKER, SLIP = 0.0005, 0.0002, 0.0002
SPOT_FEE = 0.0010


@dataclass
class Fill:
    symbol: str
    qty: float          # con signo: + compra, − venta
    price: float
    fee: float          # en USDT
    leg: str            # "perp" | "spot" | "margin"
    ok: bool = True
    msg: str = ""


class PaperBroker:
    """Ejecuta al precio de mercado del momento con deslizamiento y comisiones; no envía nada a ningún exchange."""

    def __init__(self, market, slip=SLIP):
        self.m, self.slip = market, slip

    def protect(self, symbol, position_qty, stop):         # en simulación el stop lo gestiona la estrategia
        return None

    def stop_filled(self, symbol):
        return None

    def can_trade(self, symbol, qty, leg="perp"):
        return True

    def position_qty(self, symbol):
        return None

    def execute(self, symbol, qty, leg="perp", tag=""):
        px = self.m.spot_price(symbol) if leg in ("spot", "margin") else self.m.price(symbol)
        if not (px > 0):
            return Fill(symbol, 0.0, float("nan"), 0.0, leg, ok=False, msg="sin precio")
        fill_px = px * (1 + self.slip) if qty > 0 else px * (1 - self.slip)
        fee_rate = SPOT_FEE if leg in ("spot", "margin") else TAKER
        return Fill(symbol, qty, fill_px, abs(qty) * fill_px * fee_rate, leg)


class ExchangeBroker:
    """Envía órdenes a mercado reales (testnet o real). Redondea a las reglas del símbolo y comprueba el nocional mínimo."""

    def __init__(self, client, dry_run=False):
        self.c, self.dry = client, dry_run

    def transfer(self, asset, amount, kind):
        if self.dry or amount <= 0:
            return None
        try:
            return self.c.transfer(asset, amount, kind)
        except Exception as e:
            log.error("transferencia %s %.2f %s fallida: %s", kind, amount, asset, e)
            return None

    def can_trade(self, symbol, qty, leg="perp"):
        """¿La orden cumple la cantidad y el nocional mínimos de Binance? Se comprueba ANTES de enviar cualquier pata."""
        try:
            px = float(self.c.premium_index(symbol)["markPrice"])
            q = self.c.round_qty(symbol, qty)
            r = self.c.rules(symbol)
        except Exception:
            return False
        min_notional = r["min_notional"] if leg == "perp" else 10.0
        return q >= r["min_qty"] and q * px >= min_notional * 1.05

    def stop_filled(self, symbol):
        """True si la orden de stop de la tendencia se ejecutó en el exchange (independiente de otras posiciones del mismo símbolo)."""
        try:
            o = self.c.get_order(symbol, f"btclab-stop-{symbol}"[:36])
        except Exception:
            return False
        if o.get("status") == "FILLED":
            return float(o.get("avgPrice") or o.get("stopPrice") or 0) or True
        return False

    def position_qty(self, symbol):
        for p in self.c.positions():
            if p["symbol"] == symbol:
                return float(p["positionAmt"])
        return 0.0

    def protect(self, symbol, position_qty, stop):
        """Mantiene en el exchange una orden STOP_MARKET de solo reducción al nivel del stop (sustituye a la anterior)."""
        cid = f"btclab-stop-{symbol}"[:36]
        try:
            self.c.cancel_order(symbol, cid)
        except Exception:
            pass
        q = self.c.round_qty(symbol, position_qty, market=True)
        if q <= 0:
            return None
        side = "SELL" if position_qty > 0 else "BUY"
        try:
            return self.c.order(symbol, side, q, type_="STOP_MARKET", stop_price=stop, reduce_only=True, client_id=cid)
        except Exception as e:
            log.error("no se pudo colocar el stop de %s: %s", symbol, e)
            return None

    def execute(self, symbol, qty, leg="perp", tag=""):
        side = "BUY" if qty > 0 else "SELL"
        q = self.c.round_qty(symbol, qty)
        if q <= 0:
            return Fill(symbol, 0.0, float("nan"), 0.0, leg, ok=False, msg="cantidad por debajo del mínimo")
        cid = f"btclab-{tag}-{uuid.uuid4().hex[:10]}"
        if self.dry:
            log.info("[simulacro] %s %s %s %s", leg, side, q, symbol)
            return Fill(symbol, q if qty > 0 else -q, float("nan"), 0.0, leg, ok=False, msg="simulacro")
        try:
            if leg == "perp":
                r = self.c.order(symbol, side, q, client_id=cid)
                px = float(r.get("avgPrice") or 0)
                fee = abs(q) * px * TAKER
            elif leg == "spot":
                r = self.c.spot_order(symbol, side, q, client_id=cid)
                px = sum(float(f["price"]) * float(f["qty"]) for f in r["fills"]) / max(sum(float(f["qty"]) for f in r["fills"]), 1e-12)
                fee = sum(float(f["commission"]) * (px if f["commissionAsset"] != "USDT" else 1) for f in r["fills"])
            else:   # margen: venta con préstamo automático o compra con devolución automática
                eff = "MARGIN_BUY" if side == "SELL" else "AUTO_REPAY"
                r = self.c.margin_order(symbol, side, q, client_id=cid, side_effect=eff)
                px = float(r.get("cummulativeQuoteQty", 0)) / max(float(r.get("executedQty", 1)), 1e-12)
                fee = abs(q) * px * SPOT_FEE
        except Exception as e:
            log.error("orden fallida %s %s %s: %s", leg, side, symbol, e)
            return Fill(symbol, 0.0, float("nan"), 0.0, leg, ok=False, msg=str(e))
        return Fill(symbol, q if qty > 0 else -q, px, fee, leg)
