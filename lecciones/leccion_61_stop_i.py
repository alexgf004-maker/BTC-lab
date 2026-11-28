"""Lección 61 — Stop de emergencia en el bloque I (docs/leccion_61.md)."""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import data, lab15  # noqa: E402
from leccion_47_flujos import F, zscore  # noqa: E402

H1 = pd.Timedelta("1h"); COST = 0.0007


def run(z4, h, fund, stop_pct):
    """Recorre las decisiones de 4 h; dentro de cada tramo revisa el stop con velas de 1 h. Devuelve PnL diario."""
    pnl = pd.Series(0.0, index=pd.date_range(z4.index[0].floor("1D"), z4.index[-1].ceil("1D"), freq="1D"))
    pos, e, blocked = 0, None, 0
    hi, lo, op, cl = (h[k] for k in ("high", "low", "open", "close"))
    for t, z in z4.items():
        want = 1 if z > 1 else (-1 if z < -1 else 0)
        if blocked and want != blocked:
            blocked = 0
        if blocked:
            want = 0
        px = op.get(t)
        if px is None or not px > 0:
            continue
        if want != pos:
            if pos:
                pnl[t.floor("1D")] += pos * (px / e - 1) - COST
            if want:
                e = px; pnl[t.floor("1D")] -= COST
            pos = want
        if not pos:
            continue
        seg = h[(h.index >= t) & (h.index < t + 4 * H1)]
        f = fund[(fund.index > t) & (fund.index <= t + 4 * H1)].sum() if len(fund) else 0.0
        pnl[t.floor("1D")] -= pos * f
        if stop_pct:
            sp = e * (1 - pos * stop_pct)
            for tt, bar in seg.iterrows():
                if (pos > 0 and bar.low <= sp) or (pos < 0 and bar.high >= sp):
                    x = min(bar.open, sp) if pos > 0 else max(bar.open, sp)
                    pnl[tt.floor("1D")] += pos * (x / e - 1) - COST
                    blocked, pos = pos, 0
                    break
        if pos:                                                          # marcar a mercado al final del tramo
            end = seg.close.iloc[-1] if len(seg) else px
            pnl[t.floor("1D")] += pos * (end / e - 1)
            e = end
    return pnl


if __name__ == "__main__":
    perp = data.load("BTCUSDT", "1h")
    fund = lab15._funding("BTCUSDT")
    cb = pd.read_parquet(F / "coinbase.parquet")["close"]; bs = pd.read_parquet(F / "binance_spot.parquet").iloc[:, 0]
    prem = (cb / bs.reindex(cb.index) - 1).dropna(); prem.index = prem.index + H1
    cp4 = prem.resample("4h", label="right", closed="right").mean()
    z4 = zscore(cp4, 180)
    z4 = z4[(z4.index >= "2020-01-01") & (z4.index <= "2026-10-31")].dropna()
    print("Bloque I (prima de Coinbase 4 h) con y sin stop de emergencia")
    for name, sp in (("I sin stop (actual)", 0), ("S2 stop −2 %", 0.02), ("S3 stop −3 %", 0.03), ("S5 stop −5 %", 0.05)):
        d = run(z4, perp, fund, sp)
        line = f"  {name:22s}"
        for lab, a, b in (("desarrollo", "2020-01-01", "2022-12-31"), ("examen", "2023-01-01", "2026-10-31")):
            x = d[a:b]; eq = (1 + x).cumprod(); dd = (1 - eq / eq.cummax()).max()
            line += f" | {lab}: Sharpe {x.mean() / x.std() * np.sqrt(365):+.2f}, anual {100 * x.mean() * 365:+.1f} %, caída {100 * dd:.1f} %"
        print(line, flush=True)
