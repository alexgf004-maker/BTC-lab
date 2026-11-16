"""Lección 1b: el mismo análisis de costes para horizontes más largos (intradía, swing, position).

Añade el coste de mantener la posición en perpetuos: el funding (cada 8h).
"""
import sys, glob, io, zipfile
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sclab import data, costs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FRAMES = {"5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}

def atr(df, n=14):
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

rows = []
for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
    b = data.load(s)
    for name, rule in FRAMES.items():
        df = data.resample(b, rule)
        a = (atr(df) / df["close"]).median()
        rows.append({"activo": s, "marco": name, "ATR14_%": a * 100,
                     "c_R taker/taker": costs.cost_in_r(a, costs.SCENARIOS["taker/taker"]),
                     "c_R maker/taker": costs.cost_in_r(a, costs.SCENARIOS["maker/taker"]),
                     "c_R spot 0.1%": 0.002 / a})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:.3f}"))

print("\nFunding (perpetuos): positivo = los LARGOS pagan a los cortos\n")
for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
    parts = []
    for f in sorted(glob.glob(str(ROOT / f"data/funding/{s}-*.zip"))):
        with zipfile.ZipFile(f) as z:
            parts.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0]))))
    fr = pd.concat(parts)["last_funding_rate"]
    per_day = fr.mean() * 3
    print(f"{s}: media por pago {fr.mean()*100:.4f} %  -> {per_day*100:.3f} %/día, "
          f"{per_day*365*100:.1f} %/año para un largo; pagos positivos {(fr>0).mean():.0%}")
