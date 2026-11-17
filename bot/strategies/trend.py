"""Bloque D — Tendencia en BTC y ETH (Lecciones 3 y 7): ruptura de 120 velas de 4h con filtro EMA50 diaria, chandelier 5 ATR."""
from __future__ import annotations

import pandas as pd

from .common import BAR, bars4_from_1h, chandelier_step, with_trend_signals

NAME = "D_tendencia"


class Trend:
    def __init__(self, cfg, state, broker, market, journal):
        self.cfg, self.st, self.b, self.m, self.j = cfg, state, broker, market, journal
        self.name = NAME
        self.sl = state.sleeve(NAME, cfg["capital"])

    def due(self, now):
        return now.hour % 4 == 0

    def run(self, now):
        N, m, risk = self.cfg.get("N", 120), self.cfg.get("m", 5.0), self.cfg.get("risk", 0.05)
        for sym in self.cfg.get("symbols", ["BTCUSDT", "ETHUSDT"]):
            df = with_trend_signals(bars4_from_1h(self.m.candles(sym, 24 * 420)), N, 1)
            if df.empty or df.index[-1] + BAR != now:
                continue
            last = df.iloc[-1]; t_last = df.index[-1]
            pos = self.sl["positions"].get(sym)
            if pos:
                filled = self.b.stop_filled(sym)
                if filled:                                            # el stop del exchange ya se ejecutó
                    px = filled if isinstance(filled, float) else pos["stop"]
                    self._close(sym, pos, px, now, send=False)
                    self.sl["busy_until"] = {**self.sl.get("busy_until", {}), sym: str(t_last)}
                    pos = None
            if pos:
                exit_px = chandelier_step(pos, last, float(last["atr"]), m, is_entry_bar=(str(t_last) == pos["entry_bar"]))
                if exit_px is None:
                    self.b.protect(sym, pos["qty"], pos["stop"])
                if exit_px is not None:
                    self._close(sym, pos, exit_px, now)
                    self.sl["busy_until"] = {**self.sl.get("busy_until", {}), sym: str(t_last)}
                    pos = None
            busy = self.sl.get("busy_until", {}).get(sym)
            if pos is None and bool(last["signal"]) and (busy is None or t_last > pd.Timestamp(busy)):
                self._open(sym, float(m * last["atr"]), now, risk)

    def _open(self, sym, R, now, risk):
        if sym in self.st.d.get("bloqueados", {}) or ("BTCUSDT" in self.st.d.get("bloqueados", {}) and self.name.startswith("B")):
            return
        if not (R > 0):
            return
        px = self.m.price(sym)
        units = risk * self.sl["balance"] / R
        if not self.b.can_trade(sym, units, "perp"):
            self.j.log(NAME, "omitida_minimo", sym, "BUY", units, px, "por debajo del mínimo de Binance", ts=str(now)); return
        f = self.b.execute(sym, units, "perp", tag="D")
        if not f.ok and f.msg != "simulacro":
            self.j.log(NAME, "error_entrada", sym, "BUY", units, px, f.msg); return
        entry = f.price if f.price == f.price else px
        self.sl["positions"][sym] = {"side": 1, "entry": entry, "qty": f.qty, "R": R, "stop": entry - R, "ext": entry,
                                     "entry_time": str(now), "entry_bar": str(now), "fees": f.fee}
        self.j.log(NAME, "entrada", sym, "BUY", f.qty, entry, f"R={R:.2f} stop={entry - R:.2f}", ts=str(now))
        self.b.protect(sym, f.qty, entry - R)

    def _close(self, sym, pos, exit_px, now, send=True):
        if send and self.b.position_qty(sym) is not None:           # en el exchange: cerrar a mercado y retirar el stop
            try:
                self.b.c.cancel_order(sym, f"btclab-stop-{sym}"[:36])
            except Exception:
                pass
            f = self.b.execute(sym, -pos["qty"], "perp", tag="D")
            exit_px = f.price if f.ok else exit_px
        fund = self.m.funding(sym, pd.Timestamp(pos["entry_time"]))
        fund = fund[fund.index <= now]
        pnl = pos["qty"] * (exit_px - pos["entry"]) - pos["fees"] - abs(pos["qty"]) * exit_px * 0.0007 - pos["qty"] * float(fund.sum()) * pos["entry"]
        self.sl["balance"] += pnl; self.sl["pnl"] += pnl; self.sl["closed"] += 1
        self.sl.setdefault("trades", []).append({"symbol": sym, "entry_time": pos["entry_time"], "exit_time": str(now), "entry": pos["entry"],
                                                 "exit": exit_px, "R": pos["R"], "pnl": pnl})
        del self.sl["positions"][sym]
        self.j.log(NAME, "salida", sym, "SELL", pos["qty"], exit_px, f"pnl={pnl:.2f}", ts=str(now))
