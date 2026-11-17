"""Pruebas del bot. Ejecutar: python -m pytest -q tests"""
import hashlib, hmac, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bot.binance import Binance
from bot.broker import PaperBroker
from bot.journal import Journal
from bot.risk import RiskGuard
from bot.state import State
from bot.strategies.carry import Carry
from bot.strategies.common import chandelier_step
from bot.strategies.weekend import Weekend

T = pd.Timestamp


class FakeMarket:
    def __init__(self, now, prices, candles=None, funding=None, spot=None):
        self.now, self.prices, self._c, self._f, self._s = now, prices, candles or {}, funding or {}, spot or prices
    def price(self, s): return self.prices[s]
    def spot_price(self, s): return self._s[s]
    def candles(self, s, n): return self._c[s]
    def funding(self, s, since, until=None):
        f = self._f.get(s, pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC")))
        until = until or self.now + pd.Timedelta("1min")
        return f[(f.index > since) & (f.index <= until)]


def tmp_state():
    d = tempfile.mkdtemp(); return State(f"{d}/s.json"), Journal(f"{d}/j.csv", "test")


def test_chandelier_orden_hueco_toque_y_actualizacion():
    pos = {"side": 1, "stop": 95.0, "ext": 100.0}
    assert chandelier_step(dict(pos), pd.Series({"open": 94, "high": 99, "low": 93}), 1.0, 5, False) == 94     # hueco: apertura
    assert chandelier_step(dict(pos), pd.Series({"open": 94, "high": 99, "low": 93}), 1.0, 5, True) == 95      # vela de entrada: sin hueco
    p = dict(pos); assert chandelier_step(p, pd.Series({"open": 101, "high": 110, "low": 100}), 1.0, 5, False) is None
    assert p["ext"] == 110 and p["stop"] == 105                                                                # sube con el máximo
    p2 = dict(p); chandelier_step(p2, pd.Series({"open": 108, "high": 109, "low": 106}), 1.0, 5, False)
    assert p2["stop"] == 105                                                                                   # nunca baja


def test_freno_de_riesgo_revisar_y_parar_persistente():
    st, _ = tmp_state(); g = RiskGuard(st, 0.15, 0.25)
    assert g.update(100) == "ok" and g.update(84) == "revisar" and g.update(74) == "parar"
    assert g.update(120) == "parar"                     # una vez parado, solo una persona lo reactiva


def test_estado_persistente_y_sin_duplicar_ciclos():
    st, _ = tmp_state(); st.sleeve("X", 100.0)["positions"]["BTCUSDT"] = {"qty": 1}; st.d["last_run"]["X"] = "2026-01-01 00:00:00+00:00"; st.save()
    st2 = State(st.path); assert st2.d["sleeves"]["X"]["positions"]["BTCUSDT"]["qty"] == 1 and st2.d["last_run"]["X"]


def test_firma_hmac_y_redondeo():
    b = Binance("testnet", key="k", secret="s")
    q = "symbol=BTCUSDT&timestamp=1"
    assert hmac.new(b"s", q.encode(), hashlib.sha256).hexdigest() == hmac.new(b.secret, q.encode(), hashlib.sha256).hexdigest()
    b._rules["BTCUSDT"] = {"tick": 0.1, "step": 0.001, "mkt_step": 0.001, "min_qty": 0.001}
    assert b.round_qty("BTCUSDT", 0.0129) == 0.012 and b.round_qty("BTCUSDT", -0.0129) == 0.012
    assert abs(b.round_price("BTCUSDT", 100.04) - 100.0) < 1e-9


def test_fin_de_semana_signo_y_horario():
    sun = T("2026-10-25 21:00", tz="UTC"); fri = sun - pd.Timedelta("2D")
    idx = pd.date_range(fri - pd.Timedelta("10h"), sun - pd.Timedelta("1h"), freq="1h", tz="UTC")
    c = pd.DataFrame({"open": 100.0, "close": 100.0, "quote_volume": 1e6}, index=idx)
    st, j = tmp_state(); m = FakeMarket(sun, {"TSLAUSDT": 103.0}, {"TSLAUSDT": c})
    w = Weekend({"capital": 1000, "per_trade_usd": 100}, st, PaperBroker(m, slip=0), m, j, lambda: ["TSLAUSDT"])
    assert w.due(sun) and w.due(T("2026-10-26 03:00", tz="UTC")) and not w.due(T("2026-10-26 04:00", tz="UTC"))
    w.run(sun)
    assert w.sl["positions"]["TSLAUSDT"]["qty"] < 0       # subió un 3 % el fin de semana → corto


def test_carry_no_cuenta_dos_veces_el_funding():
    t0 = T("2026-01-01 00:00", tz="UTC")
    pays = pd.Series(0.001, index=pd.DatetimeIndex([t0 + pd.Timedelta(hours=8 * k) + pd.Timedelta("3ms") for k in range(-9, 4)]))
    st, j = tmp_state()
    m = FakeMarket(t0, {"XUSDT": 10.0}, funding={"XUSDT": pays})
    c = Carry({"capital": 1000.0}, st, PaperBroker(m, slip=0), m, j, lambda now: ["XUSDT"], direction=1)
    c.run(t0)                                                       # entra (rendimiento 0,1 % por 8h)
    assert "XUSDT" in c.sl["positions"]
    for k in (1, 2, 3):
        m.now = t0 + pd.Timedelta(hours=8 * k); c.run(m.now)
    pos = c.sl["positions"]["XUSDT"]
    assert abs(pos["funding"] - 3 * 0.001 * pos["qty"] * 10.0) < 1e-9   # exactamente 3 pagos tras la entrada
