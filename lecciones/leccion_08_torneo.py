"""Lección 8: torneo de hipótesis. Reglas: docs/leccion_08.md

  python lecciones/leccion_08_torneo.py criba
  python lecciones/leccion_08_torneo.py examen     # UNA vez, solo las que pasan la criba
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import carry, data, lab, universe  # noqa: E402

HALVES = {"2020-2023": ("2020-01-01", "2024-01-01"), "2024-2026": ("2024-01-01", "2026-11-01")}
PASS = ROOT / "docs/l08_pasan_criba.json"


def tournament(symbols, K, with_h2=True, only=None):
    P = lab.panel(symbols)
    vol = universe.daily_volume(symbols)
    members = universe.monthly_members(vol, K)
    M = lab.member_frame(members, P["D"].index, list(P["D"].columns))
    btc = data.load("BTCUSDT", "1h")["close"]; btc_f = data.load_funding("BTCUSDT")
    if "BTCUSDT" not in P["H"]:
        P["H"]["BTCUSDT"] = btc.reindex(P["H"].index)
    tests = {
        "H1a carry transversal diario": lambda: lab.h1(P, M, weekly=False),
        "H1b carry transversal semanal": lambda: lab.h1(P, M, weekly=True),
        "H3a cascada, largo": lambda: lab.h3(P, M, +1),
        "H3b cascada, corto": lambda: lab.h3(P, M, -1),
        "H4 estacionalidad BTC 21-23h": lambda: lab.h4(P),
        "H6 ratio alt/BTC": lambda: lab.h6(P, M),
        "H9 reversión diaria": lambda: lab.h9(P, M),
        "H10 corto nuevos listados": lambda: lab.h10(P, btc, btc_f),
    }
    if with_h2:
        def h2():
            from leccion_06_universo import spot_close
            perp = {s: P["H"][s].dropna() for s in symbols}
            spot = {s: v for s in symbols if (v := spot_close(s)) is not None}
            cv, ep = carry.simulate(perp, spot, P["F"], members, enter=0.00015, exit_=0.00005, max_pos=4, slot=0.25,
                                    notional_frac=2 / 3, highs={s: P["HI"][s].dropna() for s in symbols}, liq_move=0.45)
            d = cv.equity.resample("1D").last().pct_change().dropna()
            tr = ep.rename(columns={"ret_on_notional": "ret"})[["symbol", "entry", "exit", "ret"]]
            return d, tr
        tests["H2 carry umbral bajo"] = h2
    res = {}
    for name, fn in tests.items():
        if only and name not in only:
            continue
        daily, tr = fn()
        daily = daily[daily.index >= pd.Timestamp("2020-03-01", tz="UTC")]
        r = {h: lab.metrics(daily, tr, a, b) for h, (a, b) in HALVES.items()}
        r["total"] = lab.metrics(daily, tr)
        res[name] = (r, daily, tr)
        t = r["total"]
        print(f"{name:<32} Sharpe {t['sharpe']:5.2f} ({r['2020-2023']['sharpe']:5.2f} / {r['2024-2026']['sharpe']:5.2f}) | "
              f"CAGR {t['CAGR']:6.1%} | DD {t['maxDD']:5.1%} | n {t['n']:5d} | WR {t['WR']:4.0%} | PF {t['PF']:5.2f} | media {t['media']:+.3%}")
    return res


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else "criba"
    if fase == "criba":
        DEV = json.load(open(ROOT / "docs/l06_division_activos.json"))["desarrollo"]
        print("CRIBA — desarrollo: 57 activos, top 20 point-in-time. Sharpe total (2020-23 / 2024-26)\n")
        res = tournament(DEV, 20)
        ok = [k for k, (r, _, _) in res.items() if r["total"]["sharpe"] >= 1.2 and r["total"]["PF"] >= 1.3
              and all(r[h]["sharpe"] > 0 for h in HALVES)]
        print("\nPasan la criba:", ok)
        json.dump(ok, open(PASS, "w"), indent=1, ensure_ascii=False)
        pd.DataFrame({k: v[1] for k, v in res.items()}).to_csv(ROOT / "docs/l08_diarios_criba.csv")

    if fase == "examen":
        from sclab.stats_tests import deflated_sharpe
        cand = [s for l in open(ROOT / "data/universo_examen2.txt") if not l.startswith("#") for s in l.split()]
        FRESH = [s for s in cand if list((ROOT / "data/raw").glob(f"{s}-1h-*.zip")) and list((ROOT / "data/funding").glob(f"{s}-fundingRate-*.zip"))]
        ok = json.load(open(PASS))
        print(f"EXAMEN — {len(FRESH)} símbolos nuevos, top 10 point-in-time. Estrategias: {ok}\n")
        res = tournament(FRESH, 10, only=ok)
        N = 342 + 9
        for k, (r, daily, tr) in res.items():
            ds = deflated_sharpe(daily.to_numpy(), N, 0.000328)
            t = r["total"]
            good = t["sharpe"] >= 0.5 and t["PF"] >= 1.3 and ds["DSR"] >= 0.90
            print(f"{k}: DSR {ds['DSR']:.3f} -> {'APROBADA' if good else 'NO aprobada'}")
            if tr is not None:
                print("  episodios por año:", tr.entry.dt.year.value_counts().sort_index().to_dict(), "| peor:", round(tr.ret.min(), 4))
