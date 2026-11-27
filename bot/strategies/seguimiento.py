"""Bloques EN PRUEBA (seguimiento hacia adelante, siempre simulados y fuera del capital de la cartera).

I_coinbase   — Lección 47, CP4: prima de Coinbase a 4 h. z > +1 → largo BTC; z < −1 → corto; si no, fuera.
J_redondos   — Lección 46 (observación posterior): apostar a que la ruptura de un número redondo falla. Es la operación
               contraria a la de la lección, con sus mismas salidas: se cierra con beneficio cuando el cierre diario vuelve al
               otro lado del nivel; stop en el siguiente número redondo; máximo 20 días.
K_tokenizadas — Lección 37, K3: si el token spot de una acción se separa > 0,5 % de su perpetuo, comprar el barato y vender el
               caro; salida cuando la diferencia baja de 0,1 % o a las 24 h.

Ninguno usa el bróker: calculan su resultado con los precios reales y costes fijos, para no tocar nunca la cuenta.
"""
from __future__ import annotations

from ..mensajes import tras

import math

import numpy as np
import pandas as pd

PERP_COST = 0.0007
SPOT_COST = 0.0012


class _Seguimiento:
    NAME = ""

    def __init__(self, cfg, state, market, journal, universe_fn=None):
        self.cfg, self.st, self.m, self.j = cfg, state, market, journal
        self.universe_fn = universe_fn
        self.name = self.NAME
        self.sl = state.sleeve(self.NAME, cfg["capital"])

    def _book(self, sym, pnl, now, why, extra=None):
        pos = self.sl["positions"].pop(sym)
        self.sl["balance"] += pnl; self.sl["pnl"] += pnl; self.sl["closed"] += 1
        self.sl.setdefault("trades", []).append({"symbol": sym, "entry_time": pos["entry_time"], "exit_time": str(now),
                                                 "pnl": pnl, "motivo": why, **(extra or {})})
        return pos

    def _perp_close(self, sym, px, now, why):
        pos = self.sl["positions"][sym]
        f = self.m.funding(sym, pd.Timestamp(pos["entry_time"]))
        f = f[f.index <= now]
        q, e = pos["qty"], pos["entry"]
        pnl = q * (px - e) - pos["fees"] - abs(q) * px * PERP_COST - q * e * float(f.sum())
        self._book(sym, pnl, now, why, {"entry": e, "exit": px})
        self.j.log(self.NAME, "salida", sym, "SELL" if q > 0 else "BUY", abs(q), px, f"{why} pnl={pnl:.2f}" + tras(pos), ts=str(now))


# ------------------------------------------------------------------------------------------------ I · prima de Coinbase
def coinbase_z(prem_h: pd.Series, now) -> float:
    """z-score de la media de 4 h de la prima frente a las 180 barras de 4 h anteriores (índice = hora en que se conoce)."""
    cp4 = prem_h.resample("4h", label="right", closed="right").mean()
    cp4 = cp4[cp4.index <= now]
    if not len(cp4) or cp4.index[-1] != now:
        return float("nan")
    m = cp4.rolling(180, min_periods=90).mean().shift(1)
    s = cp4.rolling(180, min_periods=90).std().shift(1)
    return float(((cp4 - m) / s).iloc[-1])


class PrimaCoinbase(_Seguimiento):
    NAME = "I_coinbase"

    def due(self, now):
        return now.hour % 4 == 0

    def run(self, now):
        if not hasattr(self.m, "coinbase_premium"):
            return
        z = coinbase_z(self.m.coinbase_premium(34), now)
        if not math.isfinite(z):
            return
        want = 1 if z > 1 else (-1 if z < -1 else 0)
        sym = "BTCUSDT"
        pos = self.sl["positions"].get(sym)
        have = 0 if not pos else (1 if pos["qty"] > 0 else -1)
        if want == have:
            return
        px = self.m.price(sym)
        if not px > 0:
            return
        if pos:
            self._perp_close(sym, px, now, f"la prima cambió (z {z:+.2f})")
        if want:
            q = want * self.sl["balance"] / px
            self.sl["positions"][sym] = {"qty": q, "entry": px, "fees": abs(q) * px * PERP_COST, "entry_time": str(now),
                                         "texto": f"{'Largo' if want > 0 else 'Corto'} en BTC a {px:,.0f} $ porque la prima de Coinbase "
                                                  f"está {'muy alta' if want > 0 else 'muy baja'} (z {z:+.2f}). Se revisa cada 4 h."}
            self.j.log(self.NAME, "entrada", sym, "BUY" if want > 0 else "SELL", abs(q), px,
                       f"{'Largo' if want > 0 else 'Corto'} en el futuro de BTC (≈ {abs(q) * px:,.0f} $): los compradores de EE. UU. "
                       f"pagan {'más' if want > 0 else 'menos'} de lo normal en Coinbase (z {z:+.2f}). Se revisa cada 4 h.", ts=str(now))


# ------------------------------------------------------------------------------------------------ J · ruptura fallida de redondos
def round_break(d: pd.DataFrame):
    """Mira el último día cerrado. Devuelve (dirección de la ruptura, nivel L, paso) o None (reglas de la Lección 46)."""
    if len(d) < 5:
        return None
    h, l, c = (d[k].to_numpy(float) for k in ("high", "low", "close"))
    i = len(d) - 1
    P = c[i - 1]
    if not P > 0:
        return None
    step = 5 * 10 ** (math.floor(math.log10(P)) - 1)
    top = c[i - 3:i].min()
    if c[i] < top:
        L = math.floor(top / step) * step
        if L > c[i] and l[i - 3:i].min() <= L * 1.01:
            return -1, L, step
    bot = c[i - 3:i].max()
    if c[i] > bot:
        L = math.ceil(bot / step) * step
        if L < c[i] and h[i - 3:i].max() >= L * 0.99:
            return 1, L, step
    return None


def daily(df: pd.DataFrame, now) -> pd.DataFrame:
    d = df.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    n = df["close"].resample("1D").count()
    d = d[(n.reindex(d.index) >= 23) & (d.index + pd.Timedelta("1D") <= now)]
    return d


class RedondoFalla(_Seguimiento):
    NAME = "J_redondos"

    def due(self, now):
        return True                                                     # stop cada hora; salidas diarias y entradas a las 00:00

    def _stops(self, now):
        """Revisa el stop con cada vela de 1 h cerrada desde la última revisión (como una orden stop en el exchange)."""
        for sym, pos in list(self.sl["positions"].items()):
            h = self.m.candles(sym, 72)
            if h is None or h.empty:
                continue
            since = pd.Timestamp(pos.get("checked") or pos["entry_time"])
            first = pd.Timestamp(pos["entry_time"])
            for t, bar in h[(h.index >= first) & (h.index + pd.Timedelta("1h") <= now)].iterrows():
                if pos.get("checked") and t <= since:
                    continue
                pos["checked"] = str(t)
                side, stop = pos["lado"], pos["stop"]
                if (side > 0 and bar.low <= stop) or (side < 0 and bar.high >= stop):
                    px = min(bar.open, stop) if side > 0 else max(bar.open, stop)
                    self._perp_close(sym, float(px), t + pd.Timedelta("1h"), "stop en el siguiente número redondo")
                    break

    def run(self, now):
        self._stops(now)
        if now.hour != 0:
            return
        for sym, pos in list(self.sl["positions"].items()):
            d = daily(self.m.candles(sym, 24 * 30), now)
            d = d[d.index >= pd.Timestamp(pos["entry_time"]).floor("1D")]
            if not len(d):
                if (now - pd.Timestamp(pos["entry_time"])) > pd.Timedelta("22D"):
                    self._perp_close(sym, pos["entry"], now, "sin datos")
                continue
            bar, side, L = d.iloc[-1], pos["lado"], pos["L"]
            if (side > 0 and bar.close > L) or (side < 0 and bar.close < L):
                self._perp_close(sym, float(bar.close), now, "la ruptura falló: volvió al otro lado del nivel")
            elif len(d) >= self.cfg.get("max_dias", 20):
                self._perp_close(sym, float(bar.close), now, "tiempo (20 días)")
        if not self.universe_fn:
            return
        for sym in self.universe_fn(now):
            if len(self.sl["positions"]) >= self.cfg.get("max_pos", 10):
                break
            if sym in self.sl["positions"]:
                continue
            d = daily(self.m.candles(sym, 24 * 8), now)
            if not len(d) or d.index[-1] + pd.Timedelta("1D") != now:
                continue
            sig = round_break(d)
            if not sig:
                continue
            brk, L, step = sig
            side = -brk                                                 # se apuesta a que la ruptura falla
            px = self.m.price(sym)
            if not px > 0:
                continue
            q = side * self.cfg.get("slot", 0.10) * self.sl["balance"] / px
            stop = L - step if side > 0 else L + step
            from ..mensajes import precio as _p
            nivel = _p(L)
            self.sl["positions"][sym] = {"qty": q, "entry": px, "fees": abs(q) * px * PERP_COST, "entry_time": str(now),
                                         "lado": side, "L": L, "stop": stop,
                                         "texto": f"{'Largo' if side > 0 else 'Corto'} a {_p(px)} $: apuesta a que la ruptura del número "
                                                  f"redondo {nivel} $ es falsa. Gana si un cierre diario vuelve al otro lado de {nivel} $; "
                                                  f"stop en {_p(stop)} $; máximo 20 días."}
            self.j.log(self.NAME, "entrada", sym, "BUY" if side > 0 else "SELL", abs(q), px,
                       f"{'Largo' if side > 0 else 'Corto'} en el futuro de {sym[:-4]} a {_p(px)} $ (≈ {abs(q) * px:,.0f} $).\n"
                       + (f"{sym[:-4]} estuvo 3 días por encima de {nivel} $ y ayer cerró por debajo; "
                          if brk < 0 else f"{sym[:-4]} estuvo 3 días por debajo de {nivel} $ sin poder superarlo y ayer cerró por encima; ")
                       + f"se apuesta a que la ruptura es falsa.\nGana si un cierre diario vuelve al otro lado de {nivel} $. "
                       f"Stop en {_p(stop)} $ (siguiente número redondo). Máximo 20 días.", ts=str(now))


# ------------------------------------------------------------------------------------------------ K · arbitraje de tokenizadas
class ArbitrajeTokenizadas(_Seguimiento):
    NAME = "K_tokenizadas"

    def due(self, now):
        return True

    def _gap(self, sym):
        tok = sym[:-4] + "BUSDT"
        try:
            s, p = self.m.spot_price(tok), self.m.last_price(sym)
        except Exception:
            return None, None, None
        if not (s > 0 and p > 0):
            return None, None, None
        return s / p - 1, s, p

    def run(self, now):
        if not hasattr(self.m, "last_price"):
            return
        for sym, pos in list(self.sl["positions"].items()):
            b, s, p = self._gap(sym)
            age = (now - pd.Timestamp(pos["entry_time"])) / pd.Timedelta("1h")
            if b is None:
                if age >= 24:
                    self._close(sym, pos["b"], now, "sin precio")
                continue
            if abs(b) < self.cfg.get("salida", 0.001):
                self._close(sym, b, now, f"diferencia cerrada ({100 * b:+.2f} %)")
            elif age >= self.cfg.get("max_horas", 24):
                self._close(sym, b, now, f"tiempo (24 h), diferencia {100 * b:+.2f} %")
        if not self.universe_fn:
            return
        for sym in self.universe_fn():
            if len(self.sl["positions"]) >= self.cfg.get("max_pos", 4) or sym in self.sl["positions"]:
                continue
            b, s, p = self._gap(sym)
            if b is None or abs(b) <= self.cfg.get("entrada", 0.005):
                continue
            side = -1 if b > 0 else 1                                   # +1: comprar el token spot y vender el perpetuo
            n = self.cfg.get("slot", 0.25) * self.sl["balance"]
            a = sym[:-4]
            txt = (f"El token spot de {a} está un {abs(100 * b):.2f} % {'por debajo' if side > 0 else 'por encima'} de su futuro. "
                   + (f"Compra el token a {s:,.2f} $ y corto en el futuro a {p:,.2f} $" if side > 0 else
                      f"Venta del token a {s:,.2f} $ (requeriría tenerlo o pedirlo prestado) y largo en el futuro a {p:,.2f} $")
                   + f", ≈ {n:,.0f} $ por pata. Se cierra cuando la diferencia baja de 0,1 % o a las 24 h.")
            self.sl["positions"][sym] = {"b": b, "lado": side, "notional": n, "spot_px": s, "perp_px": p, "entry_time": str(now), "texto": txt}
            self.j.log(self.NAME, "entrada", sym, "BUY" if side > 0 else "SELL", n / s, s, txt, ts=str(now))

    def _close(self, sym, b, now, why):
        pos = self.sl["positions"][sym]
        n, side, b0 = pos["notional"], pos["lado"], pos["b"]
        f = self.m.funding(sym, pd.Timestamp(pos["entry_time"]))
        f = f[f.index <= now]
        pnl = n * (side * (b - b0) / (1 + b0) - 2 * (SPOT_COST + PERP_COST) + side * float(f.sum()))
        self._book(sym, pnl, now, why, {"b_entrada": b0, "b_salida": b})
        self.j.log(self.NAME, "salida", sym, "SELL" if side > 0 else "BUY", n, 0, f"{why} pnl={pnl:.2f}" + tras(pos), ts=str(now))
