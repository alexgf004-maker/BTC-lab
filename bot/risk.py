"""Control de riesgo de la cartera: caída desde el máximo, parada de emergencia y límites de apalancamiento."""
from __future__ import annotations

import logging

log = logging.getLogger("bot.risk")


class RiskGuard:
    def __init__(self, state, review_dd=0.15, stop_dd=0.25, max_gross_leverage=3.0):
        self.state, self.review_dd, self.stop_dd, self.max_lev = state, review_dd, stop_dd, max_gross_leverage

    def update(self, equity: float) -> str:
        """Devuelve 'ok', 'revisar' o 'parar'. Al llegar a 'parar' el bot queda detenido hasta que una persona lo reactive."""
        d = self.state.d
        d["equity_peak"] = max(d.get("equity_peak") or equity, equity)
        dd = 1 - equity / d["equity_peak"]
        d["drawdown"] = dd
        if d.get("halted"):
            return "parar"
        if dd >= self.stop_dd:
            d["halted"] = True
            log.error("CAÍDA %.1f %% ≥ %.0f %%: bot detenido; cerrar posiciones y revisar", dd * 100, self.stop_dd * 100)
            return "parar"
        if dd >= self.review_dd:
            log.warning("caída %.1f %% ≥ %.0f %%: revisar la cartera", dd * 100, self.review_dd * 100)
            return "revisar"
        return "ok"

    def leverage_ok(self, gross_notional: float, equity: float) -> bool:
        return equity > 0 and gross_notional / equity <= self.max_lev
