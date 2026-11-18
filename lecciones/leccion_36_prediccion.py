"""Lección 36 — Polymarket: calibración y compra de favoritos (docs/leccion_36.md)."""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data/poly"
EXA0 = pd.Timestamp("2025-01-01", tz="UTC")


def ts(s):
    if not s:
        return None
    s = s.replace(" ", "T").replace("Z", "+00:00")
    if s.endswith("+00"):
        s += ":00"
    try:
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None


def price_at(hist, t, max_age):
    best = None
    for x in hist:
        if x["t"] <= t:
            best = x
        else:
            break
    if best is None or t - best["t"] > max_age:
        return None
    return float(best["p"])


def build():
    rows = []
    seen = set()
    for line in open(P / "markets.jsonl"):
        m = json.loads(line)
        if m["id"] in seen:
            continue
        seen.add(m["id"])
        try:
            if json.loads(m["outcomes"]) != ["Yes", "No"]:
                continue
            op = [float(x) for x in json.loads(m["outcomePrices"])]
            tok = json.loads(m["clobTokenIds"])[0]
        except Exception:
            continue
        if not (max(op) > 0.98 and min(op) < 0.02):
            continue
        T, S = ts(m.get("closedTime")), ts(m.get("startDate"))
        f = P / "hist" / f"{tok[:40]}.json"
        if T is None or S is None or not f.exists() or T - S < 8 * 86400:
            continue
        h = json.loads(f.read_text())
        d = sorted(h.get("d", []), key=lambda x: x["t"]); hh = sorted(h.get("h", []), key=lambda x: x["t"])
        yes = op[0] > 0.98
        rec = {"id": m["id"], "T": pd.Timestamp(T, unit="s", tz="UTC"), "yes": yes, "vol": m.get("volumeNum"),
               "tags": ",".join(m.get("tags") or []), "q": m["question"]}
        rec["p7"] = price_at(d, T - 7 * 86400, 2.5 * 86400)
        rec["p30"] = price_at(d, T - 30 * 86400, 2.5 * 86400)
        rec["p1"] = price_at(hh, T - 86400, 6 * 3600)
        rows.append(rec)
    return pd.DataFrame(rows)


def fav(df, col):
    x = df.dropna(subset=[col]).copy()
    x = x[(x[col] != 0.5)]
    x["qf"] = np.where(x[col] > 0.5, x[col], 1 - x[col])
    x["win"] = np.where(x[col] > 0.5, x.yes, ~x.yes)
    return x


def calib(x, label):
    print(f"\n--- Calibración {label} (n {len(x)})")
    bins = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0001]
    x = x.assign(b=pd.cut(x.qf, bins, right=False))
    for b, g in x.groupby("b", observed=True):
        w, q = g.win.mean(), g.qf.mean()
        se = np.sqrt(q * (1 - q) / len(g))
        print(f"  favorito a {b}: n {len(g):5d} | precio medio {100 * q:5.1f} % | gana {100 * w:5.1f} % | diferencia {100 * (w - q):+5.1f} pts (z {(w - q) / se:+.1f})")


def strat(x, lo, hi, cost, days, label):
    s = x[(x.qf >= lo) & (x.qf <= hi)].copy()
    if s.empty:
        print(f"{label}: sin operaciones"); return
    price = (s.qf + cost).clip(upper=0.999)
    s["r"] = np.where(s.win, (1 - price) / price, -1.0)
    w = s.groupby(s["T"].dt.to_period("W")).r.mean()
    t = w.mean() / w.std() * np.sqrt(len(w)) if len(w) > 2 else np.nan
    print(f"{label:42s} n {len(s):5d} | gana {100 * s.win.mean():5.1f} % | resultado medio {100 * s.r.mean():+6.2f} % "
          f"(t semanas {t:+5.2f}) | por día {100 * s.r.mean() / days:+.3f} % | peor semana {100 * w.min():+.1f} %")
    return s


if __name__ == "__main__":
    df = build()
    print(f"mercados binarios resueltos con historial: {len(df)} | desarrollo {int((df['T'] < EXA0).sum())} | examen {int((df['T'] >= EXA0).sum())}")
    for col, lab in (("p7", "T−7 días"), ("p1", "T−1 día"), ("p30", "T−30 días")):
        x = fav(df, col)
        calib(x[x["T"] < EXA0], f"{lab}, desarrollo")
        calib(x[x["T"] >= EXA0], f"{lab}, EXAMEN")
    print("\n=== P1 comprar el favorito a T−7 días (0,80–0,97; +1 céntimo)")
    x7 = fav(df, "p7")
    strat(x7[x7["T"] < EXA0], 0.80, 0.97, 0.01, 7, "desarrollo")
    s = strat(x7[x7["T"] >= EXA0], 0.80, 0.97, 0.01, 7, "EXAMEN")
    print("\n=== P2 casi seguros a T−1 día (0,95–0,995; +0,5 céntimos)")
    x1 = fav(df, "p1")
    strat(x1[x1["T"] < EXA0], 0.95, 0.995, 0.005, 1, "desarrollo")
    strat(x1[x1["T"] >= EXA0], 0.95, 0.995, 0.005, 1, "EXAMEN")
    if s is not None and len(s):
        print("\nP1 examen por categoría (informativo):")
        for tag in ["Sports", "Politics", "Crypto", "Elections", "Business", "Pop Culture", "Science"]:
            g = s[s.tags.str.contains(tag, na=False)]
            if len(g) >= 30:
                print(f"  {tag:12s} n {len(g):4d} | gana {100 * g.win.mean():.1f} % | resultado medio {100 * g.r.mean():+.2f} %")
    df.to_csv(ROOT / "docs/l36_mercados.csv.gz", index=False)
