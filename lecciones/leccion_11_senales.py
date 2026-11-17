"""Lección 11: investigación sistemática de señales. Reglas: docs/leccion_11.md  (una sola ejecución)"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import features, research, universe  # noqa: E402
from sclab.stats_tests import deflated_sharpe  # noqa: E402

SMOKE = len(sys.argv) > 1 and sys.argv[1] == "humo"

if __name__ == "__main__":
    U = json.load(open(ROOT / "docs/l11_universo.json"))
    vol = pd.read_parquet(ROOT / "data/cache/vol_diario_218.parquet")
    members = universe.monthly_members(vol, 25)
    syms = U["miembros"][::4] if SMOKE else U["miembros"]
    cache = ROOT / "data/cache/panel_l11.parquet"
    if cache.exists() and not SMOKE:
        P = pd.read_parquet(cache)
    else:
        P = features.build_panel(syms, members)
        if not SMOKE:
            P.to_parquet(cache)
    M = P[P.miembro]
    print(f"Panel: {len(P):,} filas, {P.index.get_level_values('symbol').nunique()} monedas; en el universo: {len(M):,} filas, "
          f"{M.index.get_level_values('time').min():%Y-%m-%d} → {M.index.get_level_values('time').max():%Y-%m-%d}")
    A, B = features.feature_names(P, False), features.feature_names(P, True)
    cov = M[features.POS].notna().groupby(M.index.get_level_values("time").year).mean().mean(axis=1)
    print("Cobertura de datos de posicionamiento por año:", cov.round(2).to_dict())

    # ---------------- Paso A
    T = research.ic_table(P, B, features.HORIZONS)
    if SMOKE:
        print("humo paso A ok:", T.shape); 
    else:
        T.to_csv(ROOT / "docs/l11_ic.csv", index=False)
        print(f"\nPASO A — {len(T)} pruebas (variable × horizonte). Significativas tras Benjamini-Hochberg al 5 %: {int(T.significativa.sum())}; "
              f"además estables en las dos mitades: {int((T.significativa & T.estable).sum())}")
        fmt = {"IC": "{:+.4f}".format, "t": "{:+.1f}".format, "IC_1a_mitad": "{:+.4f}".format, "IC_2a_mitad": "{:+.4f}".format, "p": "{:.1e}".format}
        for h in features.HORIZONS:
            print(f"\nHorizonte {h}: las 12 variables con mayor |t|")
            print(T[T.horizonte == h].head(12).drop(columns=["horizonte", "n"]).to_string(index=False, formatters=fmt))

    # ---------------- Paso B
    print("\nPASO B — modelos con validación hacia delante (neto de costes y funding)")
    rows, series = [], {}
    for setname, feats, y0 in [("A", A, 2021), ("B", B, 2022)]:
        for mode in ["neutral", "direccional"]:
            fs = feats if mode == "neutral" else feats + features.MKT
            for h in ["24h", "72h"]:
                k = features.HORIZONS[h]
                for kind in ["ridge", "lgbm"]:
                    res, turn = research.walk_forward(P, fs, h, k, kind, mode, y0)
                    if SMOKE:
                        print("humo", setname, mode, h, kind, len(res)); continue
                    pf = research.perf(res, k)
                    ds = deflated_sharpe(res["net"].to_numpy(), 374, 0.000328 * k / 6)["DSR"]
                    ok = pf["sharpe"] >= 1.0 and pf["años_pos"] >= 0.75 and ds >= 0.90
                    name = f"{setname} {mode} {h} {kind}"
                    series[name] = res["net"]
                    rows.append({"juego": setname, "cartera": mode, "horizonte": h, "modelo": kind, "Sharpe bruto": pf["sharpe_bruto"],
                                 "Sharpe neto": pf["sharpe"], "CAGR": pf["CAGR"], "DD": pf["maxDD"], "años +": pf["años_pos"],
                                 "rotación": turn, "DSR": ds, "aprueba": "SÍ" if ok else "no", "por_año": pf["por_año"]})
                    print(f"{name:<28} Sharpe bruto {pf['sharpe_bruto']:5.2f} | neto {pf['sharpe']:5.2f} | CAGR {pf['CAGR']:6.1%} | DD {pf['maxDD']:5.1%} | "
                          f"años + {pf['años_pos']:.0%} | rotación {turn:.2f} | DSR {ds:.2f} | {'APRUEBA' if ok else 'no'}")
    if not SMOKE:
        R = pd.DataFrame(rows)
        R.to_csv(ROOT / "docs/l11_modelos.csv", index=False)
        pd.DataFrame(series).to_csv(ROOT / "docs/l11_series.csv")
        print("\nRentabilidad neta por año de los que aprueban:")
        for r in R[R.aprueba == "SÍ"].itertuples():
            print(" ", r.juego, r.cartera, r.horizonte, r.modelo, r.por_año)
