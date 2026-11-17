"""Bloques A y E — Carry de funding en los dos sentidos (Lecciones 8, 16 y 17).
A (normal): largo spot + corto perpetuo cuando el funding medio de 3 días > 0,015 % por 8h; salida < 0,005 %.
E (inverso): largo perpetuo + corto spot prestado cuando (−funding − interés del préstamo) > 0,015 %; salida < 0,005 %.
4 huecos del 25 % del bloque; nocional = 2/3 del hueco (pata corta a 2x). Decisiones cada 8h (00, 08, 16 UTC)."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

NAMES = {1: "A_carry", -1: "E_carry_inverso"}
log = logging.getLogger("bot.carry")


class Carry:
    def __init__(self, cfg, state, broker, market, journal, universe_fn, direction=1, borrow_rate_fn=None, borrow_ok_fn=None):
        self.cfg, self.st, self.b, self.m, self.j = cfg, state, broker, market, journal
        self.dir, self.universe_fn = direction, universe_fn
        self.borrow_rate_fn = borrow_rate_fn or (lambda sym: cfg.get("borrow_apr", 0.30) / (365 * 3))   # por 8h
        self.borrow_ok_fn = borrow_ok_fn or (lambda sym, qty: True)
        self.name = NAMES[direction]
        self.sl = state.sleeve(self.name, cfg["capital"])

    def due(self, now):
        return now.hour % 8 == 0

    def _yield3d(self, sym, now):
        f = self.m.funding(sym, now - pd.Timedelta("72h") + pd.Timedelta("1min"))
        y = float(f.sum()) / 9
        return y if self.dir == 1 else -y - self.borrow_rate_fn(sym)

    def run(self, now):
        enter, exit_ = self.cfg.get("enter", 0.00015), self.cfg.get("exit", 0.00005)
        slots, slot_frac, nfrac = self.cfg.get("slots", 4), self.cfg.get("slot", 0.25), self.cfg.get("notional_frac", 2 / 3)
        # 1) devengo y salidas
        for sym, pos in list(self.sl["positions"].items()):
            f = self.m.funding(sym, pd.Timestamp(pos["last_accrual"]))
            pp = self.m.price(sym)
            mark = pp if pp > 0 else pos["ref"]
            pos["funding"] += self.dir * float(f.sum()) * pos["qty"] * mark      # sobre el valor ACTUAL de la posición
            if self.dir == -1:
                pos["funding"] -= pos["notional"] * self.borrow_rate_fn(sym) * max((now - pd.Timestamp(pos["last_accrual"])) / pd.Timedelta("8h"), 0)
            pos["last_accrual"] = str(now + pd.Timedelta("1min"))   # evita contar dos veces el pago que llega ms después de la hora
            if pp > 0 and abs(pp / pos["ref"] - 1) >= self.cfg.get("rebal_move", 0.20):
                self._rebalance(sym, pos, pp, now)
            y = self._yield3d(sym, now)
            if not (y > exit_) or not (pp > 0):
                self._close(sym, pos, now, f"rendimiento {y:.5%}")
        # 2) entradas: las de mayor rendimiento primero
        free = slots - len(self.sl["positions"])
        if free <= 0:
            return
        cands = []
        for sym in self.universe_fn(now):
            if sym in self.sl["positions"]:
                continue
            y = self._yield3d(sym, now)
            if y > enter:
                cands.append((y, sym))
        for y, sym in sorted(cands, reverse=True)[:free]:
            self._open(sym, y, now, self.sl["balance"] * slot_frac * nfrac)

    def _free_cash(self):
        nf = self.cfg.get("notional_frac", 2 / 3)
        used = sum(p["notional"] / nf + p.get("margen_extra", 0.0) for p in self.sl["positions"].values())
        return self.sl["balance"] - used

    def _rebalance(self, sym, pos, pp, now):
        """El precio se ha movido ≥ 20 % desde la referencia. La pata que pierde necesita margen.
        1) Si el bloque tiene USDT libres (lo normal: el carry está parado la mayor parte del tiempo), se traspasan a la cuenta
           que los necesita SIN tocar las patas → igual que el backtest validado.
        2) Si no hay reserva suficiente, se reducen las dos patas en la fracción que devuelve el nocional a su valor y se traspasan
           los USDT liberados. Más seguro, pero cobra menos funding.
        Los traspasos son internos entre cuentas propias (nunca retiradas). En simulación solo se registra."""
        up = pp > pos["ref"]
        if self.dir == 1 and not up:
            pos["ref"] = pp; return                              # A: si baja, el corto gana y el spot no tiene apalancamiento
        amount = abs(pos["qty"] * (pp - pos["ref"]))
        kind_from_main = "MAIN_UMFUTURE" if (self.dir == 1 or not up) else "MAIN_MARGIN"
        tr = getattr(self.b, "transfer", None)
        if self._free_cash() >= amount:
            moved = tr("USDT", amount, kind_from_main) if tr else None
            pos["margen_extra"] = pos.get("margen_extra", 0.0) + amount
            pos["ref"] = pp; pos["rebal"] += 1
            self.j.log(self.name, "margen_transferido" if moved else "reequilibrar_margen", sym, kind_from_main, "", pp,
                       f"precio {'al alza' if up else 'a la baja'} ≥ 20 %: traspaso de {amount:.2f} USDT de la reserva del bloque"
                       + ("" if moved or tr is None else " — FALLÓ, revisar"), ts=str(now))
            return
        f = 1 - (pos["ref"] / pp if up else pp / pos["ref"])
        dq = f * pos["qty"]
        if self.dir == 1:
            trades, kind = [("spot", -1), ("perp", +1)], "MAIN_UMFUTURE"
        else:
            trades, kind = ([("margin", +1), ("perp", -1)], "MARGIN_UMFUTURE") if not up else ([("perp", -1), ("margin", +1)], "UMFUTURE_MARGIN")
        ok = True
        for leg, sign in trades:
            fl = self.b.execute(sym, sign * dq, leg, tag=self.name[0] + "r")
            ok &= fl.ok or fl.msg == "simulacro"
        moved = tr("USDT", amount, kind) if (tr and ok) else None
        pos["qty"] -= dq; pos["ref"] = pp; pos["rebal"] += 1
        self.j.log(self.name, "margen_insuficiente", sym, kind, round(dq, 8), pp,
                   f"sin reserva: reducción de las dos patas un {f:.1%} y traspaso de {amount:.2f} USDT"
                   + ("" if moved or tr is None else " — FALLÓ, revisar"), ts=str(now))

    def _open(self, sym, y, now, notional):
        if sym in self.st.d.get("bloqueados", {}):
            return
        sp, pp = self.m.spot_price(sym), self.m.price(sym)
        if not (sp > 0 and pp > 0):
            return
        qty = notional / pp
        if self.dir == -1 and not self.borrow_ok_fn(sym, qty):
            self.j.log(self.name, "sin_prestamo", sym, "", qty, sp, "no se puede pedir prestado", ts=str(now)); return
        f_spot = self.b.execute(sym, self.dir * qty, "spot" if self.dir == 1 else "margin", tag=self.name[0])
        f_perp = self.b.execute(sym, -self.dir * qty, "perp", tag=self.name[0])
        self.sl["positions"][sym] = {"notional": notional, "qty": qty, "spot_px": f_spot.price if f_spot.price == f_spot.price else sp,
                                     "perp_px": f_perp.price if f_perp.price == f_perp.price else pp, "ref": pp,
                                     "fees": f_spot.fee + f_perp.fee, "funding": 0.0, "rebal": 0, "entry_time": str(now), "last_accrual": str(now + pd.Timedelta("1min"))}
        self.j.log(self.name, "entrada", sym, "carry" if self.dir == 1 else "carry_inverso", qty, pp, f"rendimiento {y:.5%} por 8h", ts=str(now))

    def _close(self, sym, pos, now, why):
        sp, pp = self.m.spot_price(sym), self.m.price(sym)
        sp = sp if sp > 0 else pos["spot_px"]; pp = pp if pp > 0 else pos["perp_px"]
        f_spot = self.b.execute(sym, -self.dir * pos["qty"], "spot" if self.dir == 1 else "margin", tag=self.name[0])
        f_perp = self.b.execute(sym, self.dir * pos["qty"], "perp", tag=self.name[0])
        xs = f_spot.price if f_spot.price == f_spot.price else sp; xp = f_perp.price if f_perp.price == f_perp.price else pp
        legs = self.dir * pos["qty"] * ((xs - pos["spot_px"]) - (xp - pos["perp_px"]))
        fees = pos["fees"] + f_spot.fee + f_perp.fee + pos["rebal"] * pos["notional"] * 0.0014
        pnl = legs + pos["funding"] - fees
        self.sl["balance"] += pnl; self.sl["pnl"] += pnl; self.sl["closed"] += 1
        self.sl.setdefault("trades", []).append({"symbol": sym, "entry_time": pos["entry_time"], "exit_time": str(now), "pnl": pnl,
                                                 "funding": pos["funding"], "patas": legs, "costes": fees, "motivo": why, "notional": pos["notional"]})
        del self.sl["positions"][sym]
        self.j.log(self.name, "salida", sym, "", pos["qty"], xp, f"{why} pnl={pnl:.2f} funding={pos['funding']:.2f}", ts=str(now))
