"""Bloque B — S1: corto en altcoins débiles frente a BTC (Lección 15).
Ratio alt/BTC en 4h; filtro: ratio diario bajo su EMA50; entrada en la ruptura del mínimo de 120 velas; chandelier de 5 ATR sobre el ratio.
Posición: corto en la altcoin y largo en BTC por el mismo nocional. 1 % de riesgo; máximo 10 posiciones; universo point-in-time."""
from __future__ import annotations

import pandas as pd

from .common import BAR, chandelier_step, ratio_bars4, with_trend_signals

NAME = "B_corto_alt_btc"


class WeakAlts:
    def __init__(self, cfg, state, broker, market, journal, universe_fn):
        self.cfg, self.st, self.b, self.m, self.j = cfg, state, broker, market, journal
        self.universe_fn = universe_fn               # (now) -> lista ordenada de símbolos miembros del mes
        self.name = NAME
        self.sl = state.sleeve(NAME, cfg["capital"])

    def due(self, now):
        return self.cfg.get("salidas_horarias", False) or now.hour % 4 in (0, 1)

    def _ratio(self, sym, lookback):
        a = self.m.candles(sym, lookback)["close"]; b = self.m.candles("BTCUSDT", lookback)["close"]
        return with_trend_signals(ratio_bars4(a, b), self.cfg.get("N", 120), -1)

    def run(self, now):
        m, risk, K = self.cfg.get("m", 5.0), self.cfg.get("risk", 0.01), self.cfg.get("max_pos", 10)
        if self.cfg.get("salidas_horarias") and now.hour % 4 not in (0, 1):
            for sym, pos in list(self.sl["positions"].items()):     # en vivo: salir en cuanto el ratio cierre una hora por encima del stop
                a = self.m.candles(sym, 2)["close"]; b = self.m.candles("BTCUSDT", 2)["close"]
                if len(a) and len(b):
                    r = float(a.iloc[-1] / b.iloc[-1])
                    if r >= pos["stop"]:
                        self._close(sym, pos, r, now, "stop_horario")
            return
        if now.hour % 4 == 1:                    # ejecutar las entradas señaladas hace una hora, al cierre de la primera hora
            for sym, sig in sorted(self.sl.pop("pending", {}).items()):
                if sym in self.sl["positions"] or len(self.sl["positions"]) >= K:
                    continue
                a = self.m.candles(sym, 2)["close"]; b = self.m.candles("BTCUSDT", 2)["close"]
                if len(a) and len(b) and a.index[-1] == b.index[-1] == now - pd.Timedelta("1h"):
                    self._open(sym, sig["R"], float(a.iloc[-1] / b.iloc[-1]), now, risk, entry_bar=str(now - pd.Timedelta("1h")))
            return
        # 1) gestionar posiciones abiertas (salidas antes que entradas, como en el backtest)
        for sym, pos in list(self.sl["positions"].items()):
            df = self._ratio(sym, 24 * 420)
            if df.empty or df.index[-1] + BAR != now:
                if df.empty or now - (df.index[-1] + BAR) > pd.Timedelta("3D"):        # moneda retirada: cerrar al último ratio
                    self._close(sym, pos, float(df["close"].iloc[-1]) if len(df) else pos["entry"], now, "sin_datos")
                continue
            last = df.iloc[-1]
            px = chandelier_step(pos, last, float(last["atr"]), m, is_entry_bar=(str(df.index[-1]) == pos["entry_bar"]))
            if px is not None:
                self._close(sym, pos, px, now, "stop")
        # 2) nuevas entradas, en orden alfabético como el backtest
        for sym in sorted(self.universe_fn(now)):
            if sym == "BTCUSDT" or sym in self.sl["positions"] or len(self.sl["positions"]) >= K:
                continue
            df = self._ratio(sym, 24 * 420)
            if len(df) < 130 or df.index[-1] + BAR != now:
                continue
            last = df.iloc[-1]
            if bool(last["signal"]):
                n_pend = len(self.sl.setdefault("pending", {}))
                if len(self.sl["positions"]) + n_pend < K:
                    self.sl["pending"][sym] = {"R": float(m * last["atr"]), "signal_bar": str(df.index[-1])}

    def _open(self, sym, R, ratio_px, now, risk, entry_bar):
        if sym in self.st.d.get("bloqueados", {}) or ("BTCUSDT" in self.st.d.get("bloqueados", {}) and self.name.startswith("B")):
            return
        if not (R > 0):
            return
        units = risk * self.sl["balance"] / R                    # unidades de ratio
        notional = units * ratio_px                              # nocional por pata en USDT (aprox.)
        pa, pb = self.m.price(sym), self.m.price("BTCUSDT")
        if not (self.b.can_trade(sym, notional / pa, "perp") and self.b.can_trade("BTCUSDT", notional / pb, "perp")):
            self.j.log(NAME, "omitida_minimo", sym, "SELL", notional / pa, pa, f"nocional {notional:.2f} por debajo del mínimo de una pata", ts=str(now))
            return
        fa = self.b.execute(sym, -notional / pa, "perp", tag="B")
        if not (fa.ok or fa.msg == "simulacro"):
            self.j.log(NAME, "error_entrada", sym, "SELL", notional / pa, pa, fa.msg, ts=str(now)); return
        fb = self.b.execute("BTCUSDT", notional / pb, "perp", tag="B")
        if not (fb.ok or fb.msg == "simulacro"):                     # la cobertura falló: deshacer la pata de la altcoin
            self.b.execute(sym, -fa.qty, "perp", tag="B")
            self.j.log(NAME, "error_entrada", "BTCUSDT", "BUY", notional / pb, pb, f"cobertura fallida ({fb.msg}); altcoin deshecha", ts=str(now)); return
        self.sl["positions"][sym] = {"side": -1, "entry": ratio_px, "R": R, "stop": ratio_px + R, "ext": ratio_px, "units": units,
                                     "qty_alt": fa.qty, "qty_btc": fb.qty, "px_alt": fa.price, "px_btc": fb.price,
                                     "fees": fa.fee + fb.fee, "entry_time": entry_bar, "entry_bar": entry_bar}
        self.j.log(NAME, "entrada", sym, "SELL", fa.qty, fa.price, f"ratio={ratio_px:.6g} R={R:.3g} BTC {fb.qty:+.5f} @ {fb.price:.2f}", ts=str(now))

    def _close(self, sym, pos, ratio_exit, now, why):
        fa = self.b.execute(sym, -pos["qty_alt"], "perp", tag="B")
        fb = self.b.execute("BTCUSDT", -pos["qty_btc"], "perp", tag="B")
        pnl_ratio = pos["units"] * (pos["entry"] - ratio_exit)                    # resultado medido sobre el ratio (backtest)
        legs = (pos["qty_alt"] * ((fa.price if fa.ok else pos["px_alt"]) - pos["px_alt"]) +
                pos["qty_btc"] * ((fb.price if fb.ok else pos["px_btc"]) - pos["px_btc"]))  # resultado de las patas reales
        fees = pos["fees"] + fa.fee + fb.fee
        self.sl["balance"] += legs - fees; self.sl["pnl"] += legs - fees; self.sl["closed"] += 1
        self.sl.setdefault("trades", []).append({"symbol": sym, "entry_time": pos["entry_time"], "exit_time": str(now), "entry": pos["entry"],
                                                 "exit": ratio_exit, "R": pos["R"], "pnl_ratio": pnl_ratio, "pnl_patas": legs - fees, "motivo": why})
        del self.sl["positions"][sym]
        self.j.log(NAME, "salida", sym, "BUY", -pos["qty_alt"], fa.price, f"{why} ratio={ratio_exit:.6g} pnl={legs - fees:.2f}", ts=str(now))
