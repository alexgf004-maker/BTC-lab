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
    assert len(t.sent) == 2 and "Nueva operación" in t.sent[1] and "BTC" in t.sent[1]


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


def test_preflight_atr_and_report():
    from bot.preflight import Report, FAIL, OK, atr_frac
    kl = [[0, 100, 101, 99, 100, 0]] * 30
    assert abs(atr_frac(kl) - 0.02) < 1e-9
    r = Report(); r(OK, "a"); r(FAIL, "b")
    assert r.fails == 1


def test_trend_detects_exchange_stop_by_order(tmp_path):
    """Con B y D compartiendo BTCUSDT, la tendencia debe cerrarse por el estado de SU orden de stop, no por la posición neta."""
    from bot.broker import ExchangeBroker

    class C:
        def get_order(self, symbol, cid):
            assert cid == "btclab-stop-BTCUSDT"
            return {"status": "FILLED", "avgPrice": "61000"}
    b = ExchangeBroker.__new__(ExchangeBroker); b.c = C()
    assert b.stop_filled("BTCUSDT") == 61000.0


def test_panel_render(tmp_path):
    import json as _j
    from bot import panel
    st = {"sleeves": {"D_tendencia": {"balance": 2400.0, "positions": {"BTCUSDT": {"side": 1, "qty": 0.01, "entry": 60000.0, "stop": 55000.0}},
                                      "closed": 1}}, "drawdown": 0.02, "ultimo_ciclo": "2026-01-01T00:00:00+00:00"}
    (tmp_path / "estado.json").write_text(_j.dumps(st))
    (tmp_path / "diario.csv").write_text("ts,modo,bloque,evento,symbol,lado,cantidad,precio,detalle\n2026-01-01T00:00:00+00:00,paper,x,error,,,,,<script>\n")
    cfg = {"modo": "paper", "capital": 10000, "estado": str(tmp_path / "estado.json"), "diario": str(tmp_path / "diario.csv"),
           "bloques": {"D_tendencia": {"fraccion": 0.25}}}
    s = panel.snapshot(cfg)
    assert s["health"][0] == "bad"                      # el ciclo es antiguo (o no hay servicio)
    h = panel.render(s)
    assert "largo en BTC" in h and "<script>" not in h and "&lt;script&gt;" in h


def test_mensajes_claros():
    from bot.mensajes import formatear
    m = formatear("paper", "B_corto_alt_btc", "entrada", "ENAUSDT", "SELL", -2731.77, 0.112611, "ratio=1.73561e-06 R=1.34e-07 BTC +0.00476")
    assert "Corto en el futuro de ENA: 2.731,77" in m and "Largo en el futuro de BTC" in m and "7,7 %" in m and "0,121" in m
    r = formatear("paper", "cartera", "resumen", detail="capital 10,000.00 | caída 0.0 % · D_tendencia: 2,375.00 | abiertas 0 | cerradas 0 · "
                  "B_corto_alt_btc: 2,375.00 | abiertas 1 | cerradas 0")
    assert "Resumen diario" in r and "10.000,00 $" in r and "abiertas: 1" in r
    s = formatear("live", "D_tendencia", "salida", "BTCUSDT", "SELL", 0.01, 70000, "pnl=-23.50")
    assert "REAL" in s and "−23,50 $" in s and "❌" in s
    a = formatear("paper", "cartera", "arranque", detail="modo paper · bloques ['D_tendencia', 'A_carry'] · capital 10,000.00 · avisos de Telegram activos")
    assert "Bot encendido" in a and "A, D" in a


def test_bloque_g_en_prueba_no_cuenta_ni_se_concilia():
    import tempfile as _t
    from bot.main import equity
    from bot.reconcile import expected_positions
    from bot.state import State
    from bot.mensajes import formatear
    st = State(f"{_t.mkdtemp()}/s.json")
    st.d["sleeves"] = {"D_tendencia": {"balance": 2500.0, "positions": {}, "closed": 0},
                       "G_rafaga": {"balance": 2100.0, "positions": {"BTCUSDT": {"qty": 0.01, "entry": 60000.0, "stop": 59000.0}}, "closed": 0}}
    st.d["seguimiento"] = ["G_rafaga"]
    assert equity(st) == 2500.0
    perp, spot, borrowed = expected_positions(st)
    assert perp.get("BTCUSDT", 0) == 0
    m = formatear("live", "G_rafaga", "entrada", "BTCUSDT", "BUY", 0.01, 60000, "stop=59000 z=4.5 ret3=1.80%")
    assert "Ráfaga" in m and "1,8 %" in m


def test_rafaga_señal_y_salidas():
    import numpy as np
    import pandas as pd
    from bot.strategies.momentum import features, is_signal, step_exit
    n = 300
    idx = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")
    c = np.linspace(100, 110, n); c[-1] = c[-4] * 1.03
    df = pd.DataFrame({"open": c * 0.999, "high": c * 1.002, "low": c * 0.998, "close": c,
                       "count": np.r_[np.random.default_rng(0).normal(1000, 50, n - 1), 5000]}, index=idx)
    f = features(df)
    assert is_signal(f, n - 1)
    pos = {"entry": 100.0, "stop": 98.0}
    Bar = lambda o, h, l, c_: pd.Series({"open": o, "high": h, "low": l, "close": c_})
    assert step_exit(pos, Bar(97, 99, 96, 98), 3)[1] == "stop (hueco)"
    assert step_exit(pos, Bar(100, 101, 97.5, 99), 3)[0] == 98.0
    assert step_exit(pos, Bar(100, 101, 99, 99.5), 5)[1].startswith("control")
    assert step_exit(pos, Bar(100, 101, 99, 100.5), 5) is None


def test_g_en_cartera_capital_inicial_y_migracion(tmp_path):
    from bot.main import incorporate_g, initial_capital
    from bot.state import State
    cfg = {"capital": 10000, "estado": str(tmp_path / "estado.json"),
           "bloques": {"A_carry": {"activo": True, "fraccion": 0.2375}, "E_carry_inverso": {"activo": True, "fraccion": 0.2375},
                       "B_corto_alt_btc": {"activo": True, "fraccion": 0.2375}, "D_tendencia": {"activo": True, "fraccion": 0.2375},
                       "F_fin_de_semana": {"activo": True, "fraccion": 0.05}}}
    assert abs(initial_capital(cfg) - 12000) < 1e-6
    (tmp_path / "capital.csv").write_text("ts,capital,caida,bloques\n2026-11-18T00:00:00+00:00,10010.0,0.0,{}\n")
    st = State(cfg["estado"]); st.d["equity_peak"] = 10010.0
    incorporate_g(cfg, st); incorporate_g(cfg, st)                  # idempotente
    assert "12010.0" in (tmp_path / "capital.csv").read_text() and st.d["equity_peak"] == 12010.0


def test_panel_resultado_por_bloque_con_g(tmp_path):
    import json as _j
    from bot import panel
    st = {"sleeves": {"D_tendencia": {"balance": 2375.0, "positions": {}, "closed": 0},
                      "G_rafaga": {"balance": 2000.0, "positions": {}, "closed": 0}},
          "capital_inicial": 12000.0, "seguimiento": [], "ultimo_ciclo": "2026-01-01T00:00:00+00:00"}
    (tmp_path / "estado.json").write_text(_j.dumps(st))
    cfg = {"modo": "paper", "capital": 10000, "estado": str(tmp_path / "estado.json"), "diario": str(tmp_path / "d.csv"),
           "bloques": {"D_tendencia": {"activo": True, "fraccion": 0.2375}}}
    h = panel.render(panel.snapshot(cfg))
    assert "−16,67 %" not in h and "+0,00 %" in h


def test_bloque_h_prima_rapida():
    import tempfile as _t
    import pandas as pd
    from bot.journal import Journal
    from bot.state import State
    from bot.strategies.premium import PrimaRapida

    class M:
        def __init__(self): self.p = {"XUSDT": -0.008, "YUSDT": -0.002}
        def premiums(self): return self.p
        def spot_price(self, s): return 10.0
        def price(self, s): return 9.92
        def funding(self, s, since): return pd.Series([-0.001], index=[pd.Timestamp("2026-01-01 08:00", tz="UTC")])

    class Br:
        def execute(self, s, q, leg, tag=""):
            from bot.broker import Fill
            return Fill(s, q, 10.0 if leg == "margin" else 9.92, 0.0, leg)
    d = _t.mkdtemp(); st = State(f"{d}/s.json"); m = M()
    h = PrimaRapida({"capital": 1000.0}, st, Br(), m, Journal(f"{d}/j.csv", "paper"), lambda now: ["XUSDT", "YUSDT"])
    t0 = pd.Timestamp("2026-01-01 00:00", tz="UTC")
    h.run(t0)
    assert list(st.d["sleeves"]["H_prima"]["positions"]) == ["XUSDT"]       # solo la prima < −0,5 %
    m.p = {"XUSDT": -0.0005}
    h.run(t0 + pd.Timedelta("9h"))
    tr = st.d["sleeves"]["H_prima"]["trades"][0]
    assert not st.d["sleeves"]["H_prima"]["positions"] and tr["funding"] > 0 and tr["prestamo"] > 0


def test_rafaga_filtro_de_euforia(tmp_path):
    import numpy as np
    import pandas as pd
    from bot.journal import Journal
    from bot.state import State
    from bot.strategies.momentum import Rafaga
    n = 300
    idx = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")
    c = np.linspace(100, 110, n); c[-1] = c[-4] * 1.03
    df = pd.DataFrame({"open": c * 0.999, "high": c * 1.002, "low": c * 0.998, "close": c,
                       "count": np.r_[np.random.default_rng(0).normal(1000, 50, n - 1), 5000]}, index=idx)
    now = idx[-1] + pd.Timedelta("1h")

    class M:
        def __init__(self, rate): self.rate = rate
        def candles(self, sym, n_): return df
        def price(self, sym): return float(c[-1])
        def funding(self, sym, since, until=None):
            t = pd.date_range(now - pd.Timedelta("64h"), now, freq="8h")
            return pd.Series(self.rate, index=t[t > since])

    class B:
        def execute(self, sym, qty, kind, tag=""):
            return type("F", (), {"price": float(c[-1]), "qty": qty, "fee": 0.0, "ok": True})()

    for rate, abre in ((0.0005, False), (0.0001, True)):
        st = State(str(tmp_path / f"s{rate}.json"))
        j = Journal(tmp_path / f"d{rate}.csv", "paper")
        s = Rafaga({"capital": 2000.0, "symbols": ["BTCUSDT"], "filtro_euforia": 0.0003}, st, B(), M(rate), j)
        s.run(now)
        assert ("BTCUSDT" in s.sl["positions"]) == abre
        assert ("omitida_euforia" in open(tmp_path / f"d{rate}.csv").read()) == (not abre)


def test_bloques_en_prueba_i_j_k(tmp_path):
    import numpy as np
    import pandas as pd
    from bot.journal import Journal
    from bot.main import initial_capital
    from bot.state import State
    from bot.strategies.seguimiento import (ArbitrajeTokenizadas, PrimaCoinbase, RedondoFalla, coinbase_z, daily,
                                            round_break)
    # J: BTC defiende 60.000 tres días y cierra en 59.500 → ruptura bajista; el bloque apuesta a que falla (largo)
    idx = pd.date_range("2026-11-01", periods=24 * 6, freq="1h", tz="UTC")
    closes = np.r_[np.full(24, 61000.0), np.full(24, 60400.0), np.full(24, 60300.0), np.full(24, 60200.0), np.full(24, 59500.0),
                   np.full(24, 60800.0)]
    lows = closes - 100; lows[24 * 2 + 5] = 60050
    df = pd.DataFrame({"open": closes, "high": closes + 100, "low": lows, "close": closes}, index=idx)
    now = idx[24 * 5]                                            # 00:00 del sexto día
    d = daily(df[df.index < now], now)
    assert round_break(d) == (-1, 60000, 5000)
    st = State(str(tmp_path / "s.json")); j = Journal(tmp_path / "d.csv", "paper")

    class M:
        t = now
        def candles(self, sym, n): return df[df.index < self.t]
        def price(self, sym): return float(df.close[df.index < self.t].iloc[-1])
        def funding(self, sym, since, until=None): return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
    m = M()
    J = RedondoFalla({"capital": 1000.0, "slot": 0.10}, st, m, j, lambda now: ["BTCUSDT"])
    J.run(now)
    pos = J.sl["positions"]["BTCUSDT"]
    assert pos["lado"] == 1 and pos["L"] == 60000 and pos["stop"] == 55000
    m.t = now + pd.Timedelta("1D"); J.run(m.t)                  # el día siguiente cierra en 60.800 > 60.000: la ruptura falló
    assert "BTCUSDT" not in J.sl["positions"] and J.sl["closed"] == 1 and J.sl["pnl"] > 0
    # I: prima con un salto al final → z > 1 → largo
    h = pd.date_range("2026-10-01 01:00", periods=24 * 34, freq="1h", tz="UTC")   # índice = hora en que se conoce
    prem = pd.Series(np.random.default_rng(1).normal(0, 0.0003, len(h)), index=h); prem.iloc[-4:] = 0.003
    nowI = h[-1]
    assert coinbase_z(prem, nowI) > 1

    class MI(M):
        def coinbase_premium(self, days): return prem
        def price(self, sym): return 60000.0
    I = PrimaCoinbase({"capital": 1000.0}, st, MI(), j)
    I.run(nowI)
    assert I.sl["positions"]["BTCUSDT"]["qty"] > 0
    # K: token spot 1 % barato → compra token / corto en el futuro; al cerrarse la diferencia, gana
    gap = {"v": -0.01}

    class MK(M):
        def spot_price(self, tok): return 100 * (1 + gap["v"])
        def last_price(self, sym): return 100.0
    K = ArbitrajeTokenizadas({"capital": 1000.0}, st, MK(), j, lambda: ["TSLAUSDT"])
    K.run(now)
    assert K.sl["positions"]["TSLAUSDT"]["lado"] == 1
    gap["v"] = 0.0; K.run(now + pd.Timedelta("2h"))
    assert K.sl["closed"] == 1 and K.sl["pnl"] > 0
    # I, J y K nunca cuentan en el capital inicial
    cfg = {"capital": 10000, "bloques": {"D_tendencia": {"activo": True, "fraccion": 0.5}, "I_coinbase": {"activo": True, "fraccion": 0.1},
                                         "J_redondos": {"activo": True, "fraccion": 0.1}, "K_tokenizadas": {"activo": True, "fraccion": 0.1}}}
    assert abs(initial_capital(cfg) - 10000 * (0.5 + 0.20)) < 1e-6       # D + G (en cartera por defecto)
    assert "J_redondos" in open(tmp_path / "d.csv").read()


def test_panel_bloques_en_prueba(tmp_path):
    import json as _j
    from bot import panel
    st = {"sleeves": {"D_tendencia": {"balance": 2375.0, "positions": {}, "closed": 0},
                      "J_redondos": {"balance": 1000.0, "closed": 0, "positions": {"ETHUSDT": {
                          "qty": 0.06, "entry": 1650.0, "fees": 0.07, "entry_time": "2026-11-25T00:00:00+00:00", "lado": 1,
                          "L": 1500, "stop": 1000, "texto": "Largo a 1.650 $: apuesta a que la ruptura del número redondo falla."}}},
                      "K_tokenizadas": {"balance": 1000.0, "closed": 0, "positions": {"TSLAUSDT": {
                          "b": -0.01, "lado": 1, "notional": 250, "spot_px": 99, "perp_px": 100,
                          "entry_time": "2026-11-25T00:00:00+00:00", "texto": "El token spot de TSLA está un 1,00 % por debajo."}}}},
          "capital_inicial": 12000.0, "seguimiento": ["J_redondos", "K_tokenizadas"], "ultimo_ciclo": "2026-01-01T00:00:00+00:00"}
    (tmp_path / "estado.json").write_text(_j.dumps(st))
    cfg = {"modo": "paper", "capital": 10000, "estado": str(tmp_path / "estado.json"), "diario": str(tmp_path / "d.csv"),
           "bloques": {"D_tendencia": {"activo": True, "fraccion": 0.2375}}}
    h = panel.render(panel.snapshot(cfg))
    assert "J · Ruptura falsa de redondos" in h and "K · Arbitraje de tokenizadas" in h and "EN PRUEBA" in h
    assert "{&quot;" not in h                                   # sin volcados de JSON en bruto


def test_aviso_de_cierre_con_entrada_y_duracion():
    from bot.mensajes import formatear, tras
    pos = {"qty": 0.01, "entry": 60000.0, "entry_time": "2026-11-20 08:00:00+00:00"}
    m = formatear("paper", "D_tendencia", "salida", "BTCUSDT", "SELL", 0.01, 63000, "pnl=29.50" + tras(pos), ts="2026-11-23T08:00:00+00:00")
    assert "Entró el 20/11 08:00 UTC a 60.000,00 $ y salió a 63.000,00 $" in m and "duró 3,0 días" in m and "+29,50 $" in m
