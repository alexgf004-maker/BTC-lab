"""Lección 32 — U4: factor de emisión programada (docs/leccion_32.md, sección 2b)."""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import data  # noqa: E402
import leccion_32_desbloqueos as L  # noqa: E402

LEG = 0.0014


def main():
    idx = json.load(open(L.U / "emissionsIndex.json"))["data"]
    mp = json.load(open(L.U / "map.json"))
    coins = {}
    for e in idx:
        slug = e.get("protocolSlug") or e.get("gecko_id") or e.get("name")
        if slug not in mp:
            continue
        sym = mp[slug]
        c, v = L.daily(sym)
        tp = (e.get("tokenPrice") or [{}])[0].get("price")
        mult = 1000 if sym.startswith("1000") and not sym.startswith("1000000") else (1e6 if sym.startswith("1000000") else 1)
        if not tp or not (0.5 <= c.iloc[-1] / (tp * mult) <= 2.0):
            continue
        circ = L.circ_series(slug)
        if circ is None:
            continue
        try:
            f = data.load_funding(sym).resample("1D").sum()
        except Exception:
            f = pd.Series(dtype=float)
        coins[sym] = (c, v, circ, f)
    btc, _ = L.daily("BTCUSDT"); fb = data.load_funding("BTCUSDT").resample("1D").sum()
    print("monedas:", len(coins))
    months = pd.date_range("2021-01-01", "2026-10-01", freq="MS", tz="UTC")
    res = {"alto": [], "bajo": [], "medio": []}
    prev = {"alto": set(), "bajo": set(), "medio": set()}
    ns = []
    for m in months:
        end = m + pd.offsets.MonthBegin(1)
        cand = []
        for s, (c, v, circ, f) in coins.items():
            w = v[(v.index < m) & (v.index >= m - pd.Timedelta("30D"))]
            if len(w) < 20 or w.mean() < 5e6 or (m - pd.Timedelta("1D")) not in c.index:
                continue
            c0 = circ.asof(m - pd.Timedelta("1D")); c1 = circ.asof(m + pd.Timedelta("89D"))
            if not (c0 and c0 > 0 and c1 == c1):
                continue
            cand.append((s, c1 / c0 - 1))
        if len(cand) < 9:
            continue
        cand.sort(key=lambda x: x[1]); k = len(cand) // 3
        groups = {"bajo": [s for s, _ in cand[:k]], "medio": [s for s, _ in cand[k:-k]], "alto": [s for s, _ in cand[-k:]]}
        ns.append((m, len(cand), np.median([e for _, e in cand[-k:]]), np.median([e for _, e in cand[:k]])))
        b0, b1 = btc.get(m - pd.Timedelta("1D")), btc.get(end - pd.Timedelta("1D"))
        rb = b1 / b0 - 1 - fb[(fb.index >= m) & (fb.index < end)].sum()
        for g, ss in groups.items():
            rs = []
            for s in ss:
                c, _, _, f = coins[s]
                a0 = c.get(m - pd.Timedelta("1D")); a1 = c[:end - pd.Timedelta("1D")].iloc[-1]   # deslistada: último precio
                rs.append(-(a1 / a0 - 1) + f[(f.index >= m) & (f.index < end)].sum())
            turn = len(set(ss) ^ prev[g]) / max(1, len(ss))
            cost = LEG * min(2, turn) + 0.0                      # rotación de la pata corta (BTC no rota)
            res[g].append((m, 0.5 * (np.mean(rs) + rb) - 0.5 * cost))   # 50 % corto cesta + 50 % largo BTC, sobre el capital
            prev[g] = set(ss)
    N = pd.DataFrame(ns, columns=["mes", "n", "E_alto", "E_bajo"])
    print(f"monedas por mes: mediana {N.n.median():.0f} | emisión 90 d mediana del tercio alto {100 * N.E_alto.median():.1f} % / bajo {100 * N.E_bajo.median():.1f} %")
    for per, (a, b) in (("desarrollo 2021-2023", ("2021-01-01", "2023-12-31")), ("EXAMEN 2024-2026", ("2024-01-01", "2026-10-31"))):
        print(f"\n=== {per}")
        for g in ("alto", "medio", "bajo"):
            r = pd.Series(dict(res[g])).loc[a:b]
            eq = (1 + r).cumprod()
            print(f"corto tercio {g:5s} / largo BTC: anual {100 * (eq.iloc[-1] ** (12 / len(r)) - 1):+6.1f} % | Sharpe {r.mean() / r.std() * np.sqrt(12):5.2f} | "
                  f"DD {100 * (1 - eq / eq.cummax()).max():5.1f} % | meses + {100 * (r > 0).mean():.0f} % | peor mes {100 * r.min():+.1f} %")
    r = pd.Series(dict(res["alto"]))
    print("\npor año (tercio alto):", {y: f"{100 * ((1 + g).prod() - 1):+.0f}%" for y, g in r.groupby(r.index.year)})
    r.to_csv(ROOT / "docs/l32_U4_mensual.csv")


if __name__ == "__main__":
    main()
