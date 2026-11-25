"""Bloque G — Ráfaga de momentum (motor A del BTC-Strategy-Monitor; validado fuera de BTC en la Lección 40).

En la cartera desde la Lección 40 (20 % del capital). Filtro de euforia (Lección 45): no abre si el funding medio de 3 días > 0,03 % por 8 h.

Reglas (idénticas al motor A, velas de 1 h cerradas):
  señal en la vela i: subida de 3 horas > 1,5 %; z-score del número de operaciones > 3,9362322227 frente a las 168 velas
  anteriores (desviación muestral, mínimo 72); cierre > EMA200; vela alcista.
  entrada: apertura de la vela siguiente. Stop: entrada − 1,5 ATR(14) de Wilder de la vela de señal.
  control a las 6 velas: si la 6.ª vela cierra por debajo de la entrada, se sale a ese cierre. Máximo 60 velas.
  stop conservador dentro de la vela; si la vela abre por debajo del stop, se sale a la apertura. Una posición por moneda.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

NAME = "G_rafaga"
Z_TH = 3.9362322227
H = pd.Timedelta("1h")


def features(df: pd.DataFrame) -> pd.DataFrame:
    """EMA200 (semilla en el primer valor), ATR de Wilder 14 y z-score de operaciones frente a las 168 velas previas."""
    c, h, l = df["close"].to_numpy(float), df["high"].to_numpy(float), df["low"].to_numpy(float)
    n = len(df)
    ema = np.empty(n); a = 2 / 201
    for i in range(n):
        ema[i] = c[0] if i == 0 else a * c[i] + (1 - a) * ema[i - 1]
    tr = np.empty(n)
    for i in range(n):
        tr[i] = h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    atr = np.full(n, np.nan)
    if n >= 14:
        atr[13] = tr[:14].mean()
        for i in range(14, n):
            atr[i] = (atr[i - 1] * 13 + tr[i]) / 14
    cnt = df["count"].to_numpy(float)
    z = np.full(n, np.nan)
    for i in range(n):
        s = cnt[max(0, i - 168):i]
        if len(s) >= 72:
            sd = s.std(ddof=1)
            if sd > 0:
                z[i] = (cnt[i] - s.mean()) / sd
    out = df.copy()
    out["ema200"], out["atr"], out["z"] = ema, atr, z
    out["ret3"] = out["close"] / out["close"].shift(3) - 1
    return out


def is_signal(f: pd.DataFrame, i: int) -> bool:
    r = f.iloc[i]
    return bool(i >= 72 and r.ret3 > 0.015 and np.isfinite(r.z) and r.z > Z_TH and r.close > r.ema200 and r.close > r.open
                and np.isfinite(r.atr) and r.atr > 0)


def step_exit(pos: dict, bar, k: int):
    """Comprueba la vela k (0 = vela de entrada) de una posición abierta. Devuelve (precio, motivo) o None."""
    stop, entry = pos["stop"], pos["entry"]
    if bar.open <= stop:
        return bar.open, "stop (hueco)"
    if bar.low <= stop:
        return stop, "stop"
    if k == 5 and bar.close < entry:
        return bar.close, "control de 6 h en negativo"
    if k == 59:
        return bar.close, "tiempo (60 h)"
    return None


def backtest(df: pd.DataFrame, fee=0.0024):
    """Réplica fuera de línea del motor A (para comprobar paridad con el monitor)."""
    f = features(df)
    trades, i, n = [], 72, len(f)
    while i < n - 1:
        if not is_signal(f, i):
            i += 1; continue
        e = i + 1; entry = f.open.iloc[e]; stop = entry - 1.5 * f.atr.iloc[i]
        pos, res = {"entry": entry, "stop": stop}, None
        for k in range(0, 60):
            if e + k >= n:
                break
            res = step_exit(pos, f.iloc[e + k], k)
            if res:
                x = e + k; break
        if not res:
            break
        px, why = res
        trades.append({"signal": f.index[i], "entry_t": f.index[e], "exit_t": f.index[x], "entry": entry, "exit": px,
                       "R": ((px - entry) - fee * entry) / (entry - stop), "why": why})
        i = x + 1
    return pd.DataFrame(trades)


class Rafaga:
    def __init__(self, cfg, state, broker, market, journal):
        self.cfg, self.st, self.b, self.m, self.j = cfg, state, broker, market, journal
        self.name = NAME
        self.sl = state.sleeve(NAME, cfg["capital"])

    def due(self, now):
        return True                                             # cada hora, con la vela de 1 h recién cerrada

    def run(self, now):
        risk = self.cfg.get("risk", 0.0025)
        for sym in self.cfg.get("symbols", ["BTCUSDT", "ETHUSDT", "SOLUSDT"]):
            df = self.m.candles(sym, 24 * 60)
            if df.empty or "count" not in df or df.index[-1] + H != now:
                continue
            f = features(df)
            pos = self.sl["positions"].get(sym)
            if pos:                                             # revisar todas las velas cerradas desde la última revisión
                done = pd.Timestamp(pos.get("checked", pos["entry_time"])) if pos.get("checked") else None
                for t, bar in f[f.index >= pd.Timestamp(pos["entry_time"])].iterrows():
                    if done is not None and t <= done:
                        continue
                    k = int((t - pd.Timestamp(pos["entry_time"])) / H)
                    res = step_exit(pos, bar, k)
                    pos["checked"] = str(t)
                    if res:
                        self._close(sym, pos, res[0], res[1], now)
                        self.sl.setdefault("busy_until", {})[sym] = str(t)
                        pos = None
                        break
            if pos is None:
                busy = self.sl.get("busy_until", {}).get(sym)
                i = len(f) - 1
                if (busy is None or f.index[i] > pd.Timestamp(busy)) and is_signal(f, i):
                    euf = self.cfg.get("filtro_euforia", 0.0003)     # Lección 45: no comprar con el mercado eufórico
                    if euf:
                        fz = self.m.funding(sym, now - pd.Timedelta("72h") + pd.Timedelta("1min"))
                        f3 = float(fz.sum()) / 9 if len(fz) else 0.0
                        if f3 > euf:
                            self.j.log(NAME, "omitida_euforia", sym, "BUY", 0, float(f.iloc[i].close),
                                       f"funding medio 3 días {100 * f3:.4f} % por 8 h", ts=str(now))
                            continue
                    self._open(sym, f.iloc[i], now, risk)

    def _open(self, sym, r, now, risk):
        px = self.m.price(sym)
        if not (px > 0):
            return
        R = 1.5 * float(r.atr)
        units = risk * self.sl["balance"] / R
        fl = self.b.execute(sym, units, "perp", tag="G")
        entry = fl.price if fl.price == fl.price else px
        stop = entry - R
        self.sl["positions"][sym] = {"side": 1, "entry": entry, "qty": fl.qty, "stop": stop, "R": R,
                                     "entry_time": str(now), "fees": fl.fee}
        self.j.log(NAME, "entrada", sym, "BUY", fl.qty, entry, f"stop={stop:.6g} z={float(r.z):.1f} ret3={100 * float(r.ret3):.2f}%",
                   ts=str(now))

    def _close(self, sym, pos, px, why, now):
        fl = self.b.execute(sym, -pos["qty"], "perp", tag="G")
        fee = fl.fee if fl.ok else abs(pos["qty"]) * px * 0.0007
        fund = self.m.funding(sym, pd.Timestamp(pos["entry_time"]))
        fund = fund[fund.index <= now]
        pnl = pos["qty"] * (px - pos["entry"]) - pos["fees"] - fee - pos["qty"] * float(fund.sum()) * pos["entry"]
        self.sl["balance"] += pnl; self.sl["pnl"] += pnl; self.sl["closed"] += 1
        self.sl.setdefault("trades", []).append({"symbol": sym, "entry_time": pos["entry_time"], "exit_time": str(now),
                                                 "entry": pos["entry"], "exit": px, "R": (px - pos["entry"]) / pos["R"], "pnl": pnl, "motivo": why})
        del self.sl["positions"][sym]
        self.j.log(NAME, "salida", sym, "SELL", pos["qty"], px, f"{why} pnl={pnl:.2f}", ts=str(now))
