"""Lección 1: ¿En qué marco temporal el scalping NO está condenado por los costes?

A) Volatilidad típica (ATR14 en %) por activo y marco -> coste en R si el stop = 1 ATR.
B) Perfil horario de volatilidad (UTC) -> cuándo merece la pena operar.
C) Hipótesis nula: entradas aleatorias. Debe dar E bruta ~ 0 y E neta ~ -coste.
   Si no, el motor de backtest tiene un error. Esta es nuestra línea base.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sclab import data, costs, backtest  # noqa: E402

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
FRAMES = {"1m": None, "3m": "3min", "5m": "5min", "15m": "15min"}


def atr(df, n=14):
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


pd.set_option("display.width", 160)
bars = {s: data.load(s) for s in SYMBOLS}
print("Datos:", {s: f"{d.index[0]:%Y-%m-%d} -> {d.index[-1]:%Y-%m-%d} ({len(d):,} velas)" for s, d in bars.items()})

# ---------- A) coste en R por marco temporal
rows = []
for s in SYMBOLS:
    for name, rule in FRAMES.items():
        df = bars[s] if rule is None else data.resample(bars[s], rule)
        a = (atr(df) / df["close"]).median()
        row = {"activo": s, "marco": name, "ATR14_%": a * 100}
        for sc, m in costs.SCENARIOS.items():
            row[f"c_R {sc}"] = costs.cost_in_r(a, m)
        row["W_min RR1 taker"] = costs.breakeven_winrate(1, row["c_R taker/taker"])
        rows.append(row)
A = pd.DataFrame(rows)
print("\nA) Coste por trade en R con stop = 1 ATR14 (mediana)\n")
print(A.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

# ---------- B) perfil horario
df5 = data.resample(bars["BTCUSDT"], "5min")
rng = (df5["high"] - df5["low"]) / df5["close"] * 100
vol = df5["quote_volume"] / 1e6
B = pd.DataFrame({"rango5m_%": rng.groupby(rng.index.hour).median(),
                  "vol_5m_MUSD": vol.groupby(vol.index.hour).median()})
B.index.name = "hora_UTC"
print("\nB) BTCUSDT: rango mediano de vela 5m y volumen por hora UTC\n")
print(B.to_string(float_format=lambda x: f"{x:.3f}"))

# ---------- C) hipótesis nula (entradas aleatorias)
rng_gen = np.random.default_rng(42)
rows = []
for s in SYMBOLS:
    for name in ["1m", "5m", "15m"]:
        rule = FRAMES[name]
        df = bars[s] if rule is None else data.resample(bars[s], rule)
        sig = pd.Series(rng_gen.choice([-1, 1], len(df)) * (rng_gen.random(len(df)) < 0.05), index=df.index)
        for sc in ["taker/taker", "maker/maker"]:
            t = backtest.simulate(df, sig, atr(df), rr=1.0, cost=costs.SCENARIOS[sc], max_bars=100)
            g, n_ = backtest.stats(t, "r_gross"), backtest.stats(t, "r_net")
            rows.append({"activo": s, "marco": name, "costes": sc, "trades": n_["trades"],
                         "WR bruto": g["win_rate"], "E bruta R": g["E_R"],
                         "WR neto": n_["win_rate"], "E neta R": n_["E_R"], "PF neto": n_["PF"]})
C = pd.DataFrame(rows)
print("\nC) Hipótesis nula: entradas aleatorias, stop 1 ATR, TP 1R\n")
print(C.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

out = Path(__file__).resolve().parent.parent / "docs"
A.to_csv(out / "l01_A_costes.csv", index=False); B.to_csv(out / "l01_B_horario.csv"); C.to_csv(out / "l01_C_nula.csv", index=False)
