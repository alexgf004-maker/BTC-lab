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


# ------------------------------------------------------------------ mejoras: Telegram, margen del carry y comparación con el exchange
from bot.notify import Telegram
from bot.reconcile import futures_margin_guard, reconcile


class FakeClient:
    def __init__(self, positions, orders=(), spot=None, margin=None, account=None):
        self._pos, self._orders, self._spot, self._margin, self._acc = positions, list(orders), spot or {}, margin or {}, account
        self._rules = {"BTCUSDT": {"step": 0.001}, "ETHUSDT": {"step": 0.001}, "XUSDT": {"step": 0.1}}
        self.transfers, self.stops = [], []
    def rules(self, s): return self._rules[s]
    def positions(self): return [{"symbol": k, "positionAmt": str(v)} for k, v in self._pos.items()]
    def open_orders(self, symbol=None): return [{"clientOrderId": c} for c in self._orders]
    def spot_balances(self): return self._spot
    def margin_account(self): return {"nivel": 3.0, "activos": self._margin}
    def account(self): return self._acc
    def transfer(self, asset, amount, kind): self.transfers.append((asset, round(amount, 2), kind)); return {"tranId": 1}


class FakeBroker:
    def __init__(self): self.protected = []
    def protect(self, sym, qty, stop): self.protected.append((sym, qty, stop))


def test_telegram_sin_configurar_no_falla_y_registra():
    t = Telegram(token="", chat_id="")
    assert not t.enabled and t.send("hola") is False and "hola" in t.sent[0]
    d = tempfile.mkdtemp(); j = Journal(f"{d}/j.csv", "paper", t)
    j.log("D_tendencia", "entrada", "BTCUSDT", "BUY", 0.01, 65000.0, "R=1000")
    j.log("D_tendencia", "detalle_menor", "BTCUSDT")                     # no importante: no se avisa
    assert len(t.sent) == 2 and "entrada BTCUSDT" in t.sent[1]


def test_comparacion_detecta_descuadre_y_bloquea():
    st, j = tmp_state()
    st.sleeve("D_tendencia", 100)["positions"]["BTCUSDT"] = {"qty": 0.010, "stop": 60000}
    st.sleeve("B_corto_alt_btc", 100)["positions"]["ETHUSDT"] = {"qty_alt": -1.0, "qty_btc": 0.005}
    ok = FakeClient({"BTCUSDT": 0.015, "ETHUSDT": -1.0}, orders=["btclab-stop-BTCUSDT"])
    assert reconcile(st, ok, j, FakeBroker(), check_spot=False) == [] and not st.d.get("bloqueados")
    bad = FakeClient({"BTCUSDT": 0.015, "ETHUSDT": -0.5, "XUSDT": 3.0})       # ETH a medias y una posición desconocida
    br = FakeBroker()
    issues = reconcile(st, bad, j, br, check_spot=False)
    assert {i[1] for i in issues} == {"ETHUSDT", "XUSDT"} and set(st.d["bloqueados"]) == {"ETHUSDT", "XUSDT"}
    assert br.protected == [("BTCUSDT", 0.010, 60000)]                   # faltaba el stop: repuesto


def test_guardia_de_margen_de_futuros():
    d = tempfile.mkdtemp(); j = Journal(f"{d}/j.csv", "live")
    c = FakeClient({}, spot={"USDT": 5000.0}, account={"totalMarginBalance": "1000", "totalMaintMargin": "500"})
    assert futures_margin_guard(c, j) == 1500.0 and c.transfers == [("USDT", 1500.0, "MAIN_UMFUTURE")]   # 500/0,2 − 1000
    c2 = FakeClient({}, spot={"USDT": 5000.0}, account={"totalMarginBalance": "1000", "totalMaintMargin": "100"})
    assert futures_margin_guard(c2, j) == 0.0 and c2.transfers == []


def test_carry_reajuste_usa_la_reserva_y_si_no_hay_reduce():
    t0 = T("2026-01-01 00:00", tz="UTC")
    pays = pd.Series(0.001, index=pd.DatetimeIndex([t0 + pd.Timedelta(hours=8 * k) + pd.Timedelta("3ms") for k in range(-9, 6)]))
    for slots, expect_reduce in [(1, False), (4, True)]:
        st, j = tmp_state()
        m = FakeMarket(t0, {"XUSDT": 10.0}, funding={"XUSDT": pays})
        cfg = {"capital": 1000.0, "slots": slots, "slot": 1.0 if slots == 1 else 0.25, "notional_frac": 2 / 3}
        if slots == 4:                                                      # bloque lleno: sin reserva
            cfg["slot"] = 1.0
        c = Carry(cfg, st, PaperBroker(m, slip=0), m, j, lambda now: ["XUSDT"], direction=1)
        c.run(t0); q0 = c.sl["positions"]["XUSDT"]["qty"]
        m.now = t0 + pd.Timedelta("8h"); m.prices["XUSDT"] = 12.5; m._s = {"XUSDT": 12.5}   # +25 %
        if slots == 1:
            c.sl["balance"] += 1000.0                                       # reserva disponible
        c.run(m.now)
        pos = c.sl["positions"]["XUSDT"]
        assert (pos["qty"] < q0) == expect_reduce and pos["ref"] == 12.5
        assert (pos.get("margen_extra", 0) > 0) == (not expect_reduce)
