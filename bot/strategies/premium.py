"""Bloque H — Prima rápida (Lección 23, T4): perpetuo despegado por debajo de su índice spot.

Cada hora: si el precio marcado del perpetuo está más de un 0,5 % por debajo de su índice (media del spot), largo en el perpetuo y
corto en spot con monedas prestadas (mismo nocional). Salida cuando |prima| < 0,1 % o a las 24 h. Se cobra el funding (normalmente
negativo en esos momentos) y se paga el interés del préstamo.
En la investigación, entrando 1 h tarde: +0,5 % por operación (2020–2023) y +1,3 % (examen). Muy sensible a la velocidad de ejecución.
"""
from __future__ import annotations

from ..mensajes import tras

import pandas as pd

NAME = "H_prima"


class PrimaRapida:
    def __init__(self, cfg, state, broker, market, journal, universe_fn):
        self.cfg, self.st, self.b, self.m, self.j = cfg, state, broker, market, journal
        self.universe_fn = universe_fn
        self.name = NAME
        self.sl = state.sleeve(NAME, cfg["capital"])

    def due(self, now):
        return True

    def run(self, now):
        prem = self.m.premiums() if hasattr(self.m, "premiums") else {}
        if not prem:
            return
        exit_th, max_h = self.cfg.get("salida", 0.001), self.cfg.get("max_horas", 24)
        for sym, pos in list(self.sl["positions"].items()):
            p = prem.get(sym)
            age = (now - pd.Timestamp(pos["entry_time"])) / pd.Timedelta("1h")
            if p is None:
                if age >= max_h:
                    self._close(sym, pos, now, "sin datos de prima")
                continue
            if abs(p) < exit_th:
                self._close(sym, pos, now, f"prima normalizada ({100 * p:+.2f} %)")
            elif age >= max_h:
                self._close(sym, pos, now, f"tiempo ({max_h} h)")
        enter_th, max_pos = self.cfg.get("entrada", -0.005), self.cfg.get("max_pos", 4)
        cands = sorted(((prem[s], s) for s in self.universe_fn(now) if s in prem and prem[s] < enter_th and s not in self.sl["positions"]))
        for p, sym in cands:
            if len(self.sl["positions"]) >= max_pos:
                break
            self._open(sym, p, now)

    def _open(self, sym, p, now):
        sp, pp = self.m.spot_price(sym), self.m.price(sym)
        if not (sp > 0 and pp > 0):
            return
        notional = self.cfg.get("slot", 0.25) * self.sl["balance"]
        qty = notional / pp
        fs = self.b.execute(sym, -qty, "margin", tag="H")
        if not (fs.ok or fs.msg == "simulacro"):
            self.j.log(NAME, "error_entrada", sym, "", qty, sp, fs.msg, ts=str(now)); return
        fp = self.b.execute(sym, qty, "perp", tag="H")
        if not (fp.ok or fp.msg == "simulacro"):
            self.b.execute(sym, qty, "margin", tag="H")
            self.j.log(NAME, "error_entrada", sym, "", qty, pp, f"pata perpetua fallida ({fp.msg}); spot deshecho", ts=str(now)); return
        self.sl["positions"][sym] = {"qty": qty, "spot_px": fs.price if fs.price == fs.price else sp,
                                     "perp_px": fp.price if fp.price == fp.price else pp, "fees": fs.fee + fp.fee,
                                     "entry_time": str(now), "prima": p, "notional": notional}
        self.j.log(NAME, "entrada", sym, "BUY", qty, pp, f"prima={100 * p:.3f}%", ts=str(now))

    def _close(self, sym, pos, now, why):
        sp, pp = self.m.spot_price(sym), self.m.price(sym)
        fs = self.b.execute(sym, pos["qty"], "margin", tag="H")
        fp = self.b.execute(sym, -pos["qty"], "perp", tag="H")
        xs = fs.price if fs.price == fs.price else (sp if sp > 0 else pos["spot_px"])
        xp = fp.price if fp.price == fp.price else (pp if pp > 0 else pos["perp_px"])
        legs = pos["qty"] * ((xp - pos["perp_px"]) - (xs - pos["spot_px"]))
        f = self.m.funding(sym, pd.Timestamp(pos["entry_time"]))
        f = f[f.index <= now]
        fund = -pos["qty"] * pos["perp_px"] * float(f.sum())                 # el largo cobra cuando el funding es negativo
        hours = (now - pd.Timestamp(pos["entry_time"])) / pd.Timedelta("1h")
        borrow = self.cfg.get("borrow_apr", 0.30) * hours / 8760 * pos["qty"] * pos["spot_px"]
        fees = pos["fees"] + fs.fee + fp.fee
        pnl = legs + fund - borrow - fees
        self.sl["balance"] += pnl; self.sl["pnl"] += pnl; self.sl["closed"] += 1
        self.sl.setdefault("trades", []).append({"symbol": sym, "entry_time": pos["entry_time"], "exit_time": str(now), "pnl": pnl,
                                                 "patas": legs, "funding": fund, "prestamo": borrow, "costes": fees, "motivo": why})
        del self.sl["positions"][sym]
        self.j.log(NAME, "salida", sym, "SELL", pos["qty"], xp, f"{why} pnl={pnl:.2f} funding={fund:.2f}" + tras(pos), ts=str(now))
