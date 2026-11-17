"""Lección 12: cuatro estrategias derivadas de hallazgos previos. Reglas: docs/leccion_12.md

  python lecciones/leccion_12_derivadas.py criba [N1 N2 N4 N3]
  python lecciones/leccion_12_derivadas.py examen
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import lab12  # noqa: E402

DIV = json.load(open(ROOT / "docs/l12_division.json"))
PASS = ROOT / "docs/l12_pasan_criba.json"
NAMES = {"N1": "N1 tendencia relativa alt/BTC", "N2": "N2 cesta contra la volatilidad",
         "N3": "N3 captura del pago de funding", "N4": "N4 rebote tras purga"}


def run(code, fase):
    dev = fase == "criba"
    if code == "N1":
        return lab12.n1_relative_trend(DIV["desarrollo_57"] if dev else DIV["resto_161"])
    if code == "N2":
        return lab12.n2_low_vol_basket(DIV["desarrollo_57"] if dev else DIV["resto_161"])
    if code == "N4":
        return lab12.n4_deleverage_rebound(DIV["desarrollo_57"] if dev else DIV["resto_161"])
    if code == "N3":
        return lab12.n3_funding_capture(DIV["n3_desarrollo"] if dev else DIV["n3_examen"])


def show(code, daily, tr, extra):
    s = lab12.summary(daily, tr)
    print(f"{NAMES[code]}\n   Sharpe {s['sharpe']:.2f} | CAGR {s['CAGR']:.1%} | DD {s['maxDD']:.1%} | n {s['n']} | WR {s['WR']:.0%} | PF {s['PF']:.2f} | "
          f"mitades (corte {s['corte']}): {s['mitad1']:+.1%} / {s['mitad2']:+.1%}")
    print(f"   por año: {s['por_año']} | {extra}\n")
    return s


if __name__ == "__main__":
    fase = sys.argv[1]
    codes = sys.argv[2:] or ["N1", "N2", "N4", "N3"]
    if fase == "criba":
        ok = json.load(open(PASS)) if PASS.exists() else []
        for c in codes:
            daily, tr, extra = run(c, fase)
            s = show(c, daily, tr, extra)
            tr.to_csv(ROOT / f"docs/l12_criba_{c}.csv", index=False)
            good = s["sharpe"] >= 1.2 and s["PF"] >= 1.3 and s["mitad1"] > 0 and s["mitad2"] > 0
            ok = [x for x in ok if x != c] + ([c] if good else [])
            print(f"   -> {'PASA la criba' if good else 'no pasa'}\n")
        json.dump(sorted(ok), open(PASS, "w"))
        print("Pasan la criba hasta ahora:", sorted(ok))

    if fase == "examen":
        from sclab.stats_tests import deflated_sharpe
        for c in json.load(open(PASS)):
            daily, tr, extra = run(c, fase)
            s = show(c, daily, tr, extra)
            ds = deflated_sharpe(daily.to_numpy(), 378, 0.000328)["DSR"]
            good = s["sharpe"] >= 1.0 and s["PF"] >= 1.3 and ds >= 0.90
            print(f"   Deflated Sharpe {ds:.3f} -> {'APROBADA' if good else 'NO aprobada'}")
            if "side" in tr:
                for d, nm in [(1, "ratio al alza (largo alt / corto BTC)"), (-1, "ratio a la baja (corto alt / largo BTC)")]:
                    x = tr[tr.side == d].ret
                    print(f"   {nm}: n {len(x)}, WR {(x > 0).mean():.0%}, E {x.mean():+.3f}R, PF {x[x > 0].sum() / -x[x <= 0].sum():.2f}")
            tr.to_csv(ROOT / f"docs/l12_examen_{c}.csv", index=False)
