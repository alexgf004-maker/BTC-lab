"""Bloque F (candidata, tamaño pequeño) — Reversión del fin de semana en perpetuos de acciones de EE. UU. (Lecciones 23–24).
Domingo 21:00 UTC: W = log(precio ahora / apertura del viernes 21:00); si |W| ≥ 1 %, posición −signo(W). Cierre el lunes 03:00 UTC."""
from __future__ import annotations

import numpy as np
import pandas as pd

NAME = "F_fin_de_semana"


class Weekend:
    def __init__(self, cfg, state, broker, market, journal, symbols_fn):
        self.cfg, self.st, self.b, self.m, self.j = cfg, state, broker, market, journal
        self.symbols_fn = symbols_fn                       # () -> perpetuos con underlyingType == "EQUITY"
        self.name = NAME
        self.sl = state.sleeve(NAME, cfg["capital"])

    def due(self, now):
        return (now.day_of_week == 6 and now.hour == 21) or (now.day_of_week == 0 and now.hour == 3)

    def run(self, now):
        if now.day_of_week == 0:
            for sym, pos in list(self.sl["positions"].items()):
                f = self.b.execute(sym, -pos["qty"], "perp", tag="F")
                px = f.price if f.price == f.price else self.m.price(sym)
                fund = self.m.funding(sym, pd.Timestamp(pos["entry_time"]))
                pnl = pos["qty"] * (px - pos["entry"]) - pos["fees"] - f.fee - pos["qty"] * float(fund.sum()) * pos["entry"]
                self.sl["balance"] += pnl; self.sl["pnl"] += pnl; self.sl["closed"] += 1
                self.sl.setdefault("trades", []).append({"symbol": sym, "entry_time": pos["entry_time"], "exit_time": str(now), "W": pos["W"], "pnl": pnl})
                del self.sl["positions"][sym]
                self.j.log(NAME, "salida", sym, "", -pos["qty"], px, f"pnl={pnl:.2f}", ts=str(now))
            return
        fri = now - pd.Timedelta("2D")                      # viernes 21:00
        per_trade, th = self.cfg.get("per_trade_usd", 500.0), self.cfg.get("threshold", 0.01)
        for sym in self.symbols_fn():
            if sym in self.st.d.get("bloqueados", {}):
                continue
            c = self.m.candles(sym, 60)
            if fri not in c.index or len(c) < 10:
                continue
            p0, p1 = float(c.loc[fri, "open"]), self.m.price(sym)
            if not (p0 > 0 and p1 > 0):
                continue
            W = float(np.log(p1 / p0))
            if abs(W) < th:
                continue
            vol3h = float(c["quote_volume"].iloc[-3:].sum())
            notional = min(per_trade, 0.10 * vol3h, self.sl["balance"] * self.cfg.get("max_frac_per_trade", 0.10))
            if notional < 10:
                continue
            f = self.b.execute(sym, -np.sign(W) * notional / p1, "perp", tag="F")
            if not f.ok and f.msg != "simulacro":
                continue
            self.sl["positions"][sym] = {"qty": f.qty, "entry": f.price if f.price == f.price else p1, "fees": f.fee, "W": W, "entry_time": str(now)}
            self.j.log(NAME, "entrada", sym, "SELL" if W > 0 else "BUY", f.qty, p1, f"W={W:+.2%}", ts=str(now))
