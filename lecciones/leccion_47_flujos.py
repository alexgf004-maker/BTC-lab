"""Lección 47 — Indicadores de flujo de dinero (docs/leccion_47.md)."""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data, lab15  # noqa: E402

F = ROOT / "data" / "flujos"
COST = 0.0007
PERIODS = (("desarrollo", "2020-01-01", "2022-12-31"), ("examen", "2023-01-01", "2026-10-31"))


def nw_t(x, y, lags=5):
    """t de la pendiente de rango(y) sobre rango(x), con errores de Newey-West."""
    d = pd.concat([x, y], axis=1).dropna()
    a, b = d.iloc[:, 0].rank().to_numpy(), d.iloc[:, 1].rank().to_numpy()
    a = (a - a.mean()) / a.std(); b = (b - b.mean()) / b.std()
    beta = (a * b).mean()
    u = a * (b - beta * a)
    n = len(u); s = (u ** 2).sum()
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * (u[L:] * u[:-L]).sum()
    return beta, beta / (np.sqrt(s) / n)


def zscore(x, win):
    m = x.rolling(win, min_periods=win // 2).mean().shift(1)
    s = x.rolling(win, min_periods=win // 2).std().shift(1)
    return (x - m) / s


def strategy(z, sign, px, fund, freq):
    """Posición decidida al cierre de cada barra y mantenida la barra siguiente. Devuelve PnL diario neto."""
    pos = pd.Series(np.where(sign * z > 1, 1.0, np.where(sign * z < -1, -1.0, 0.0)), index=z.index).fillna(0)
    nxt = px.reindex(z.index).pct_change().shift(-1)
    f = fund.resample(freq, label="left", closed="right").sum().reindex(z.index).shift(-1).fillna(0)
    pnl = pos * nxt - pos * f - COST * pos.diff().abs().fillna(0)
    return pnl.dropna().resample("1D").sum(), pos


def sharpe(d):
    return d.mean() / d.std() * np.sqrt(365) if d.std() > 0 else float("nan")


if __name__ == "__main__":
    perp = data.load("BTCUSDT", "1h")["close"]
    fund = lab15._funding("BTCUSDT")
    cb = pd.read_parquet(F / "coinbase.parquet")["close"]
    bs = pd.read_parquet(F / "binance_spot.parquet").iloc[:, 0]
    up = pd.read_parquet(F / "upbit.parquet")["close"]
    krw = pd.read_parquet(F / "krw.parquet").iloc[:, 0]
    sc = pd.read_parquet(F / "stablecoins.parquet").iloc[:, 0]

    # Las velas de 1 h están indexadas por su apertura: el cierre de la vela h se conoce en h + 1 h.
    prem_h = (cb / bs.reindex(cb.index) - 1).dropna()
    prem_h.index = prem_h.index + pd.Timedelta("1h")              # índice = momento en que se conoce
    px_d = perp.copy(); px_d.index = px_d.index + pd.Timedelta("1h")
    day_px = px_d.resample("1D", label="right", closed="right").last()   # precio a las 00:00 UTC (cierre del día anterior)

    ind = {}
    cp = prem_h.resample("1D", label="right", closed="right").mean()
    ind["CP prima de Coinbase (diaria)"] = (zscore(cp, 90), +1, day_px, "1D", cp)
    bs_close = bs.copy(); bs_close.index = bs_close.index + pd.Timedelta("1h")
    bs_d = bs_close.resample("1D", label="right", closed="right").last()
    up_d = up.copy(); up_d.index = up_d.index + pd.Timedelta("1D")       # el cierre de Upbit del día d se conoce a las 00:00 de d+1
    krw_prev = krw.copy(); krw_prev.index = krw_prev.index + pd.Timedelta("1D")   # dato del día hábil anterior
    krw_d = krw_prev.reindex(pd.date_range(krw_prev.index[0], up_d.index[-1], freq="1D")).ffill()
    kp = (up_d / (bs_d.reindex(up_d.index) * krw_d.reindex(up_d.index)) - 1).dropna()
    kp = kp.where(kp.index > up_d.index[0])
    ind["KP prima kimchi (diaria)"] = (zscore(kp.dropna(), 90), -1, day_px, "1D", kp)
    sc_k = sc.copy(); sc_k.index = sc_k.index + pd.Timedelta("1D")       # foto de las 00:00 del día anterior
    g = sc_k / sc_k.shift(7) - 1
    ind["SC emisión de stablecoins (7 días)"] = (zscore(g.dropna(), 90), +1, day_px, "1D", g)
    cp4 = prem_h.resample("4h", label="right", closed="right").mean()
    px4 = px_d.resample("4h", label="right", closed="right").last()
    ind["CP4 prima de Coinbase (4 h)"] = (zscore(cp4, 180), +1, px4, "4h", cp4)

    rows = []
    for name, (z, sign, px, freq, raw) in ind.items():
        z = z[(z.index >= "2020-01-01") & (z.index <= "2026-11-01")].dropna()
        d, pos = strategy(z, sign, px, fund, freq)
        nxt = px.reindex(z.index).pct_change().shift(-1)
        beta, t = nw_t(sign * z, nxt, lags=5 if freq == "1D" else 30)
        line = f"{name:38s} | IC (signo esperado) {beta:+.3f}, t {t:+.2f}"
        for lab, a, b in PERIODS:
            x = d[a:b]
            line += f" | {lab}: Sharpe {sharpe(x):+.2f}, anual {100 * x.mean() * 365:+.1f} %"
        line += f" | tiempo invertido {100 * (pos != 0).mean():.0f} %"
        print(line)
    print("\nComparación: BTC comprado siempre — Sharpe", " / ".join(
        f"{lab} {sharpe(day_px.pct_change().shift(-1)[a:b].dropna()):+.2f}" for lab, a, b in PERIODS))
