"""Lección 2: retroceso dentro de la tendencia (swing 4h). Reglas: docs/leccion_02.md

Uso:
  python lecciones/leccion_02_pullback.py diseno      # SOLO datos en muestra (2020-2023)
  python lecciones/leccion_02_pullback.py validacion  # fuera de muestra, una vez, params congelados
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data, indicators as ind, swing  # noqa: E402

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
           "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT"]
IS_END = pd.Timestamp("2024-01-01", tz="UTC")
BAR = pd.Timedelta("4h")
OFFSET, RSI_N, MAX_BARS, EMA_D = 0.25, 3, 12, 50
GRID = {"umbral": [10, 15, 20, 25, 30], "m": [1.5, 2.0, 2.5, 3.0], "rr": [0.5, 0.75, 1.0, 1.5, 2.0]}
FROZEN = ROOT / "docs" / "l02_parametros_congelados.json"


def prepare(sym):
    h1 = data.load(sym, "1h")
    df = data.resample(h1, "4h")
    dd = data.resample(h1, "1D")
    trend = np.sign(dd["close"] - ind.ema(dd["close"], EMA_D))
    df["trend"] = ind.daily_on_intraday(trend, df.index, BAR)
    df["rsi"] = ind.rsi(df["close"], RSI_N)
    df["atr"] = ind.atr(df, 14)
    return df, data.load_funding(sym)


def signals(df, umbral, direction):
    if direction == 1:
        s = (df["trend"] > 0) & (df["rsi"] < umbral)
    else:
        s = (df["trend"] < 0) & (df["rsi"] > 100 - umbral)
    return s.to_numpy() * direction


def run(df, fund, side, m, rr):
    limit = (df["close"] - np.sign(side) * OFFSET * df["atr"]).to_numpy()
    limit = np.where(side == 0, np.nan, limit)
    return swing.simulate(df, side, limit, (m * df["atr"]).to_numpy(), rr, MAX_BARS, fund, bar=BAR)


def run_all(prepared, umbral, m, rr, direction, period, control_seed=None):
    trades = []
    for sym, (df, fund) in prepared.items():
        sub = df[df.index < IS_END] if period == "IS" else df[df.index >= IS_END]
        side = signals(sub, umbral, direction)
        if control_seed is not None:   # misma cantidad de señales, colocadas al azar dentro de la tendencia
            rng = np.random.default_rng(control_seed + hash(sym) % 1000)
            pool = np.flatnonzero((sub["trend"].to_numpy() * direction) > 0)
            k = int((side != 0).sum())
            side = np.zeros(len(sub), int)
            side[rng.choice(pool, size=min(k, len(pool)), replace=False)] = direction
        t = run(sub, fund, side, m, rr)
        t["symbol"] = sym
        trades.append(t)
    return pd.concat(trades, ignore_index=True)


def fmt(df, index=False):
    return df.to_string(index=index, float_format=lambda x: f"{x:.3f}")


def diseno(prepared):
    for direction, name in [(1, "LARGOS"), (-1, "CORTOS")]:
        rows = []
        for u, m, rr in itertools.product(*GRID.values()):
            t = run_all(prepared, u, m, rr, direction, "IS")
            rows.append({"umbral": u, "m": m, "rr": rr, **swing.stats(t["r_net"])})
        g = pd.DataFrame(rows)
        # robustez: media de E de la celda y sus vecinas inmediatas en la rejilla
        keys = {k: sorted(v) for k, v in GRID.items()}
        def neigh(r):
            ok = np.ones(len(g), bool)
            for k in keys:
                pos = keys[k].index(r[k])
                vals = keys[k][max(0, pos - 1): pos + 2]
                ok &= g[k].isin(vals).to_numpy()
            return g.loc[ok, "E_R"].mean()
        g["E_vecinas"] = g.apply(neigh, axis=1)
        g.to_csv(ROOT / f"docs/l02_rejilla_{name.lower()}.csv", index=False)
        print(f"\n=== {name} EN MUESTRA (2020-2023): {len(g)} combinaciones ===")
        print(f"Combinaciones con E neta > 0: {(g.E_R > 0).sum()} / {len(g)}")
        print("Mapa E neta media (filas umbral, columnas rr), promediando m:")
        print(g.pivot_table(index="umbral", columns="rr", values="E_R").round(3).to_string())
        print("Mapa win rate (promediando m):")
        print(g.pivot_table(index="umbral", columns="rr", values="win_rate").round(2).to_string())
        elig = g[g.trades >= 300].sort_values("E_vecinas", ascending=False)
        print("Top 5 por E de vecinas (robustez):")
        print(fmt(elig.head(5)))
        best = elig.iloc[0]
        t = run_all(prepared, best.umbral, best.m, best.rr, direction, "IS")
        ctrl = pd.concat([run_all(prepared, best.umbral, best.m, best.rr, direction, "IS", control_seed=s)
                          for s in range(5)])
        print("Elegida vs CONTROL (entradas aleatorias en tendencia, 5 semillas):")
        print(fmt(pd.DataFrame([{"serie": "estrategia", **swing.stats(t.r_net)},
                                {"serie": "control", **swing.stats(ctrl.r_net)}])))
        t["year"] = t.signal_time.dt.year
        print("Por año:"); print(fmt(t.groupby("year").r_net.apply(lambda r: pd.Series(swing.stats(r))).unstack(), index=True))
        print("Por activo:"); print(fmt(t.groupby("symbol").r_net.apply(lambda r: pd.Series(swing.stats(r))).unstack(), index=True))
        print("Salidas:", t.reason.value_counts(normalize=True).round(2).to_dict())
        yield name, best


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else "diseno"
    prepared = {s: prepare(s) for s in SYMBOLS}
    if fase == "diseno":
        chosen = {name: {k: float(b[k]) for k in GRID} for name, b in diseno(prepared)}
        print("\nParámetros elegidos (aún NO congelados):", chosen)
        json.dump(chosen, open(ROOT / "docs/l02_parametros_candidatos.json", "w"), indent=1)
    elif fase == "validacion":
        params = json.load(open(FROZEN))
        for name, p in params.items():
            d = 1 if name == "LARGOS" else -1
            t = run_all(prepared, p["umbral"], p["m"], p["rr"], d, "OOS")
            ctrl = pd.concat([run_all(prepared, p["umbral"], p["m"], p["rr"], d, "OOS", control_seed=s) for s in range(5)])
            print(f"\n=== {name} FUERA DE MUESTRA (2024-01 → 2026-10) {p} ===")
            print(fmt(pd.DataFrame([{"serie": "estrategia", **swing.stats(t.r_net)},
                                    {"serie": "control", **swing.stats(ctrl.r_net)}])))
            t["year"] = t.signal_time.dt.year
            print("Por año:"); print(fmt(t.groupby("year").r_net.apply(lambda r: pd.Series(swing.stats(r))).unstack(), index=True))
            print("Por activo:"); print(fmt(t.groupby("symbol").r_net.apply(lambda r: pd.Series(swing.stats(r))).unstack(), index=True))
            t.to_csv(ROOT / f"docs/l02_oos_trades_{name.lower()}.csv", index=False)
