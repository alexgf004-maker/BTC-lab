"""Pruebas de cordura del motor swing. Ejecutar: python -m pytest -q"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sclab import swing  # noqa: E402

def bars(prices, start="2024-01-01"):
    idx = pd.date_range(start, periods=len(prices), freq="4h", tz="UTC").as_unit("ms")
    p = np.array(prices, float)
    return pd.DataFrame({"open": p, "high": p * 1.001, "low": p * 0.999, "close": p}, index=idx)

def test_funding_solo_durante_el_trade():
    df = bars([100] * 3 + [100, 103, 103, 103] + [100] * 20)
    fidx = pd.date_range("2023-01-01", "2025-01-01", freq="8h", tz="UTC").as_unit("ms")
    fund = pd.Series(0.0001, index=fidx)
    side = np.zeros(len(df), int); side[2] = 1
    t = swing.simulate(df, side, np.full(len(df), 100.0), np.full(len(df), 1.0), rr=2.0,
                       max_bars=12, funding=fund, costs=swing.SwingCosts(0, 0, 0))
    assert len(t) == 1 and t.reason[0] == "tp"
    # TP a 102 desde 100 -> +2R brutos; el funding de ~1 día (3 pagos) cuesta ~0.03 de 1R
    assert abs(t.r_gross[0] - 2.0) < 1e-9
    assert 0 < t.r_gross[0] - t.r_net[0] < 0.1

def test_sin_mirar_al_futuro_y_stop_primero():
    df = bars([100] * 5)
    df.iloc[3, df.columns.get_loc("low")] = 98.0; df.iloc[3, df.columns.get_loc("high")] = 103.0
    side = np.zeros(5, int); side[1] = 1
    t = swing.simulate(df, side, np.full(5, 100.0), np.full(5, 1.0), rr=1.0, max_bars=12,
                       costs=swing.SwingCosts(0, 0, 0))
    assert t.reason[0] == "sl" and abs(t.r_gross[0] + 1) < 1e-9


def test_trend_trailing_sube_y_no_mira_futuro():
    from sclab import trend
    p = [100] * 20 + list(np.linspace(100, 130, 30)) + [130, 120, 110, 100]
    df = bars(p)
    df["atr"] = 1.0
    side = np.zeros(len(df), int); side[19] = 1
    t = trend.simulate(df, side, m=3, costs=swing.SwingCosts(0, 0, 0))
    assert len(t) == 1
    # el stop se ha ido subiendo: sale muy por encima de la entrada (100) y por debajo del máximo
    assert t.exit[0] == 120 and t.r_gross[0] > 6   # gap 130->120: sale a la apertura
