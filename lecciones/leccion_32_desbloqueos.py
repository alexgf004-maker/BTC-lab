"""Lección 32 — Desbloqueos de tokens (docs/leccion_32.md)."""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data  # noqa: E402

U = ROOT / "data/unlocks"
TEAM = {"insiders", "privateSale"}
ECO = {"ecosystem", "farming", "airdrop", "staking"}
EXA0 = pd.Timestamp("2024-01-01", tz="UTC"); END = pd.Timestamp("2026-10-20", tz="UTC")


def daily(sym):
    h = data.load(sym, "1h")
    return h["close"].resample("1D").last(), h["quote_volume"].resample("1D").sum()


def circ_series(slug):
    f = U / f"proto/{slug}.json"
    if not f.exists():
        return None
    x = json.loads(f.read_text())
    tot = None
    for s in x["documentedData"]["data"]:
        d = pd.Series({p["timestamp"]: p["unlocked"] for p in s["data"]})
        tot = d if tot is None else tot.add(d, fill_value=0)
    if tot is None or tot.empty:
        return None
    tot.index = pd.to_datetime(tot.index, unit="s", utc=True).normalize()
    return tot[~tot.index.duplicated()].sort_index()


def build_events():
    idx = json.load(open(U / "emissionsIndex.json"))["data"]
    mp = json.load(open(U / "map.json"))
    btc, _ = daily("BTCUSDT")
    rows, rejected = [], []
    for e in idx:
        slug = e.get("protocolSlug") or e.get("gecko_id") or e.get("name")
        if slug not in mp:
            continue
        sym = mp[slug]
        c, v = daily(sym)
        tp = (e.get("tokenPrice") or [{}])[0].get("price")
        mult = 1000 if sym.startswith("1000") and not sym.startswith("1000000") else (1e6 if sym.startswith("1000000") else 1)
        if not tp or not (0.5 <= c.iloc[-1] / (tp * mult) <= 2.0):
            rejected.append(sym); continue
        circ = circ_series(slug) if (U / f"proto/{slug}.json").exists() else None
        if circ is None:
            rejected.append(sym + "(sin circulante)"); continue
        by_day = {}
        for ev in e.get("unlockEvents") or []:
            T = pd.Timestamp(ev["timestamp"], unit="s", tz="UTC").normalize()
            for a in ev["cliffAllocations"]:
                if a["amount"] > 0 and (a["category"] in TEAM or a["category"] in ECO):
                    k = "team" if a["category"] in TEAM else "eco"
                    by_day.setdefault((T, k), 0.0)
                    by_day[(T, k)] += a["amount"]
        for (T, k), amt in by_day.items():
            cs = circ.asof(T - pd.Timedelta("1D")) if T - pd.Timedelta("1D") >= circ.index[0] else np.nan
            if not (cs and cs > 0):
                continue
            rows.append((sym, T, k, amt / cs))
    E = pd.DataFrame(rows, columns=["symbol", "T", "kind", "s"])
    print(f"emparejamientos descartados por precio o sin circulante: {len(rejected)}")
    return E


def prices(syms):
    out = {s: daily(s) for s in set(syms) | {"BTCUSDT"}}
    fund = {}
    for s in out:
        try:
            fund[s] = data.load_funding(s)
        except Exception:
            fund[s] = pd.Series(dtype=float)
    return out, fund


def px(c, day):                                  # precio a las 00:00 UTC de `day` = cierre del día anterior
    return c.get(day - pd.Timedelta("1D"), np.nan)


def windows(E, P):
    btc = P["BTCUSDT"][0]
    W = {"[T-30,T-8]": (-30, -7), "[T-7,T-1]": (-7, 0), "[T,T+6]": (0, 7), "[T+7,T+30]": (7, 31)}
    res = []
    for r in E.itertuples():
        c = P[r.symbol][0]
        row = {"symbol": r.symbol, "T": r.T, "group": r.group}
        for k, (a, b) in W.items():
            d0, d1 = r.T + pd.Timedelta(f"{a}D"), r.T + pd.Timedelta(f"{b}D")
            row[k] = np.log(px(c, d1) / px(c, d0)) - np.log(px(btc, d1) / px(btc, d0))
        res.append(row)
    return pd.DataFrame(res)


def trade(sym, T, P, F):
    c, btc = P[sym][0], P["BTCUSDT"][0]
    d0, d1 = T - pd.Timedelta("7D"), T + pd.Timedelta("3D")
    a0, a1, b0, b1 = px(c, d0), px(c, d1), px(btc, d0), px(btc, d1)
    if not all(np.isfinite([a0, a1, b0, b1])) or a0 <= 0:
        return np.nan
    fa, fb = F[sym], F["BTCUSDT"]
    fs = lambda f: float(f[(f.index > d0) & (f.index <= d1)].sum()) if len(f) else 0.0
    return -(a1 / a0 - 1) + (b1 / b0 - 1) + fs(fa) - fs(fb) - 0.0028


def liquid(sym, T, P):
    v = P[sym][1]
    w = v[(v.index < T - pd.Timedelta("8D")) & (v.index >= T - pd.Timedelta("38D"))]
    return len(w) >= 20 and w.mean() >= 5e6


def summarize(df, col, label):
    x = df.dropna(subset=[col])
    wk = x.groupby(x["T"].dt.to_period("W"))[col].mean()
    t = wk.mean() / wk.std() * np.sqrt(len(wk)) if len(wk) > 2 else np.nan
    print(f"{label:46s} n {len(x):5d} | media {100 * x[col].mean():+6.2f} % | mediana {100 * x[col].median():+6.2f} % | "
          f"t (semanas) {t:+5.2f} | positivas {100 * (x[col] > 0).mean():4.0f} %")


if __name__ == "__main__":
    E = build_events()
    P, F = prices(E.symbol.unique())
    E = E[(E["T"] < END) & (E["T"] >= pd.Timestamp("2020-03-01", tz="UTC"))]
    E["group"] = np.select([(E.kind == "team") & (E.s >= 0.01), (E.kind == "eco") & (E.s >= 0.01), (E.kind == "team") & (E.s >= 0.001)],
                           ["(i) equipo/inversores ≥1 %", "(ii) ecosistema ≥1 %", "(iii) equipo/inversores 0,1–1 %"], "otro")
    E = E[E.group != "otro"]
    E = E[[liquid(r.symbol, r.T, P) for r in E.itertuples()]].reset_index(drop=True)
    print(f"eventos líquidos: {len(E)} | monedas {E.symbol.nunique()} |", E.group.value_counts().to_dict())
    # placebo: mismas monedas, fechas al azar sin desbloqueos de equipo/inversores en ±30 días
    rng = np.random.default_rng(0)
    team_days = {s: set(g["T"]) for s, g in E[E.group != "(ii) ecosistema ≥1 %"].groupby("symbol")}
    allT = {s: set(g["T"]) for s, g in E.groupby("symbol")}
    pl = []
    for r in E[E.group == "(i) equipo/inversores ≥1 %"].itertuples():
        c = P[r.symbol][0]
        for _ in range(50):
            d = c.index[rng.integers(40, len(c) - 10)]
            if all(abs((d - t).days) > 30 for t in team_days.get(r.symbol, ())) and liquid(r.symbol, d, P) and (d < EXA0) == (r.T < EXA0):
                pl.append((r.symbol, d, "placebo", 0.0, "placebo")); break
    E = pd.concat([E, pd.DataFrame(pl, columns=["symbol", "T", "kind", "s", "group"])], ignore_index=True)
    E["T"] = pd.to_datetime(E["T"], utc=True)
    Wd = windows(E, P)
    for per, sel in (("DESARROLLO (antes de 2024)", Wd["T"] < EXA0), ("EXAMEN (2024 → 2026-10)", Wd["T"] >= EXA0)):
        print(f"\n===== U1 {per}: rentabilidad anormal (altcoin/BTC)")
        for g, x in Wd[sel].groupby("group"):
            print(f"  {g}")
            for k in ["[T-30,T-8]", "[T-7,T-1]", "[T,T+6]", "[T+7,T+30]"]:
                summarize(x, k, f"     {k}")
    E["r"] = [trade(r.symbol, r.T, P, F) for r in E.itertuples()]
    E = E.sort_values("T")
    keep, last = [], {}
    for r in E.itertuples():                           # una posición por moneda a la vez (por grupo)
        key = (r.symbol, r.group)
        if key in last and (r.T - last[key]).days < 10:
            keep.append(False); continue
        last[key] = r.T; keep.append(True)
    E2 = E[keep]
    print("\n===== U2 corto altcoin / largo BTC de T−7 a T+3 (neto de costes y funding)")
    for per, sel in (("desarrollo", E2["T"] < EXA0), ("EXAMEN", E2["T"] >= EXA0)):
        for g in ["(i) equipo/inversores ≥1 %", "placebo", "(ii) ecosistema ≥1 %", "(iii) equipo/inversores 0,1–1 %"]:
            summarize(E2[sel & (E2.group == g)], "r", f"{per:10s} {g}")
    E2.to_csv(ROOT / "docs/l32_eventos.csv", index=False)
    big = E2[(E2.group == "(i) equipo/inversores ≥1 %")]
    print("\nPor tamaño (grupo i, todo el periodo):")
    for lo, hi in ((0.01, 0.02), (0.02, 0.05), (0.05, 1e9)):
        summarize(big[(big.s >= lo) & (big.s < hi)], "r", f"  s en [{lo:.0%}, {hi if hi < 1 else '∞'})")
    print("Por año (grupo i):", {y: f"{100 * g.r.mean():+.2f}% (n {len(g)})" for y, g in big.groupby(big["T"].dt.year)})
