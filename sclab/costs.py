"""Modelo de costes de Binance USDⓈ-M Futures (nivel VIP 0).

Comisiones públicas VIP0: maker 0,0200 %, taker 0,0500 %
(con BNB: 10 % de descuento). Revisa tu nivel real en Binance.
"""
from dataclasses import dataclass

MAKER = 0.0002
TAKER = 0.0005
TICK = {"BTCUSDT": 0.1, "ETHUSDT": 0.01, "SOLUSDT": 0.01}


@dataclass(frozen=True)
class CostModel:
    entry_fee: float = TAKER      # fracción del nocional
    exit_fee: float = TAKER
    slippage: float = 0.0001      # 0,01 % por lado en órdenes a mercado (stop)

    @property
    def round_trip(self) -> float:
        """Coste total ida+vuelta como fracción del precio."""
        return self.entry_fee + self.exit_fee + 2 * self.slippage


SCENARIOS = {
    "taker/taker": CostModel(TAKER, TAKER, 0.0001),
    "maker/taker": CostModel(MAKER, TAKER, 0.00005),
    "maker/maker": CostModel(MAKER, MAKER, 0.0),
}


def cost_in_r(stop_pct: float, model: CostModel) -> float:
    """Coste de un trade expresado en R (R = distancia al stop)."""
    return model.round_trip / stop_pct


def breakeven_winrate(rr: float, c: float) -> float:
    """Win rate mínimo para E=0 con recompensa rr (en R) y coste c (en R)."""
    return (1 + c) / (1 + rr)
