"""Lección 10: cuatro hipótesis de scalping. Reglas: docs/leccion_10.md

  python lecciones/leccion_10_scalping.py criba
  python lecciones/leccion_10_scalping.py examen    # una vez, solo lo que pase la criba
"""
import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import scalp  # noqa: E402

DEV = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]
EXAM = ["ADAUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "DOTUSDT"]
MID = pd.Timestamp("2025-06-01", tz="UTC")
PASS = ROOT / "docs/l10_pasan_criba.json"


def st(r):
    if len(r) < 2:
        return {"n": len(r), "E": np.nan, "t": np.nan, "PF": np.nan, "WR": np.nan}
    return {"n": len(r), "E": r.mean(), "t": r.mean() / r.std() * np.sqrt(len(r)),
            "PF": r[r > 0].sum() / -r[r <= 0].sum() if (r <= 0).any() else np.inf, "WR": (r > 0).mean()}


def evaluate(symbols):
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(scalp.run_symbol, symbols))
    out = {}
    for name in scalp.HYP:
        tr = pd.concat([r[name][0] for r in res], ignore_index=True)
        sent = sum(r[name][1] for r in res)
        s, g = st(tr.r_net), st(tr.r_gross)
        h1, h2 = st(tr.r_net[tr.entry_time < MID]), st(tr.r_net[tr.entry_time >= MID])
        per = tr.groupby("symbol").r_net.mean()
        hold = (tr.exit_time - tr.entry_time).dt.total_seconds().median() / 60
        print(f"{name}\n   órdenes {sent} | ejecutadas {len(tr)} ({len(tr)/max(sent,1):.0%}) | stop medio {tr.stop_pct.mean():.2%} | duración mediana {hold:.0f} min")
        print(f"   BRUTO: E {g['E']:+.3f}R, WR {g['WR']:.0%}, PF {g['PF']:.2f}   →   NETO: E {s['E']:+.3f}R, WR {s['WR']:.0%}, PF {s['PF']:.2f}, t {s['t']:+.2f}")
        print(f"   mitades: {h1['E']:+.3f}R / {h2['E']:+.3f}R | activos positivos {int((per > 0).sum())}/{len(per)} | salidas {tr.reason.value_counts(normalize=True).round(2).to_dict()}\n")
        out[name] = {"tr": tr, "s": s, "h": (h1["E"], h2["E"]), "pos": int((per > 0).sum())}
    return out


if __name__ == "__main__":
    fase = sys.argv[1]
    if fase == "criba":
        print(f"CRIBA — {', '.join(DEV)} — 2024-01 → 2026-10\n")
        out = evaluate(DEV)
        ok = [k for k, v in out.items() if v["s"]["E"] > 0 and v["s"]["t"] >= 3 and v["s"]["PF"] >= 1.2
              and min(v["h"]) > 0 and v["pos"] >= 4]
        print("Pasan la criba:", ok)
        json.dump(ok, open(PASS, "w"), indent=1, ensure_ascii=False)
        for k, v in out.items():
            v["tr"].to_csv(ROOT / f"docs/l10_criba_{k[:2]}_trades.csv.gz", index=False)
