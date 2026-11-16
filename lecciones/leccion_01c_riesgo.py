"""Lección 1c: ¿qué significa arriesgar un 3 % por trade?

Dos perfiles de estrategia BUENOS (netos de costes, realistas en swing):
  - "alto WR":   58 % aciertos, gana +0,95R / pierde -1,05R  -> E ≈ +0,11R, PF ≈ 1,26
  - "tendencia": 38 % aciertos, gana +2,4R  / pierde -1,05R  -> E ≈ +0,26R, PF ≈ 1,49
Monte Carlo de 300 trades con interés compuesto para distintos riesgos por trade.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sclab.risk import monte_carlo  # noqa: E402

def profile(wr, win, loss, n=10000):
    k = int(wr * n)
    return np.array([win] * k + [loss] * (n - k))

profiles = {"alto WR 58%": profile(0.58, 0.95, -1.05), "tendencia 38%": profile(0.38, 2.4, -1.05)}
rows = []
for name, r in profiles.items():
    for risk in [0.005, 0.01, 0.02, 0.03]:
        m = monte_carlo(r, risk)
        rows.append({"perfil": name, "riesgo": f"{risk:.1%}", **m})
df = pd.DataFrame(rows)
pct = ["dd_p50", "dd_p95", "P(dd>30%)", "P(dd>50%)", "ret_p5", "ret_p50", "P(perder)"]
print(df.to_string(index=False, formatters={**{c: (lambda x: f"{x:.0%}") for c in pct}, "racha_p95": lambda x: f"{x:.0f}"}))
