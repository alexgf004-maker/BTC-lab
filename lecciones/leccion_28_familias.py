"""Lección 28 — Carry entre familias de perpetuos (USDT vs USDC, USDT vs COIN-M). Pre-registro en docs/leccion_28.md."""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SP = Path("/tmp/claude-0/-home-user/e9703610-5c49-51c1-9f3f-bbe7221b21cd/scratchpad")
ENTER, EXIT, SLOTS, SLOT, LEG = 0.00015, 0.00005, 5, 0.20, 0.0007


def read_zips(files):
    parts = []
    for f in files:
        with zipfile.ZipFile(f) as z:
            raw = z.read(z.namelist()[0])
        hdr = 0 if raw[:1].isalpha() else None
        parts.append(pd.read_csv(io.BytesIO(raw), header=hdr))
    return parts


def funding(sym, d):
    parts = read_zips(sorted(d.glob(f"{sym}-fundingRate-*.zip")))
    if not parts:
        return None
    x = pd.concat([p.iloc[:, [0, -1]].set_axis(["t", "r"], axis=1) for p in parts])
    s = pd.Series(x["r"].astype(float).to_numpy(), index=pd.DatetimeIndex(pd.to_datetime(x["t"].astype("int64"), unit="ms", utc=True)).floor("1h"))
    return s[~s.index.duplicated()].sort_index()


def closes(sym, d):
    parts = read_zips(sorted(d.glob(f"{sym}-1h-*.zip")))
    if not parts:
        return None
    x = pd.concat([p.iloc[:, [0, 4]].set_axis(["t", "c"], axis=1) for p in parts])
    s = pd.Series(x["c"].astype(float).to_numpy(), index=pd.DatetimeIndex(pd.to_datetime(x["t"].astype("int64"), unit="ms", utc=True)))
    return s[~s.index.duplicated()].sort_index()


def load_pairs(kind):
    other = open(SP / ("usdc.txt" if kind == "X1" else "cm.txt")).read().split()
    pairs = {}
    for o in other:
        u = o.replace("USDC", "USDT") if kind == "X1" else o.replace("USD_PERP", "USDT")
        fu, fo = funding(u, ROOT / "data/funding"), funding(o, ROOT / "data/fam/funding")
        pu, po = closes(u, ROOT / "data/raw"), closes(o, ROOT / "data/fam/raw")
        if any(x is None for x in (fu, fo, pu, po)):
            continue
        idx = pu.index.intersection(po.index)
        if len(idx) < 24 * 30:
            continue
        pairs[o] = dict(fu=fu, fo=fo, pu=pu.reindex(idx), po=po.reindex(idx))
    return pairs


def s3d(f, t):
    w = f[(f.index > t - pd.Timedelta("72h")) & (f.index <= t)]
    return w.sum() / 9 if len(w) else np.nan


def run(pairs, start, end):
    hours = pd.date_range(start, end, freq="1h", tz="UTC")
    eq, pos, rows, stats = 1.0, {}, [], {"fund": 0.0, "price": 0.0, "cost": 0.0, "n": 0}
    for t in hours:
        # 1) devengo de la hora que termina en t
        for o, p in list(pos.items()):
            P = pairs[o]
            if t not in P["pu"].index:
                continue
            pu, po = P["pu"].at[t], P["po"].at[t]
            dpx = p["d"] * (p["qo"] * (po - p["po"]) - p["qu"] * (pu - p["pu"]))
            fu, fo = P["fu"].get(t, 0.0), P["fo"].get(t, 0.0)
            dfund = p["d"] * (fu * p["qu"] * pu - fo * p["qo"] * po)
            eq += dpx + dfund; stats["price"] += dpx; stats["fund"] += dfund
            p["pu"], p["po"] = pu, po
        # 2) decisiones cada 8 h
        if t.hour % 8 == 0:
            sig = {}
            for o, P in pairs.items():
                if t in P["pu"].index:
                    a, b = s3d(P["fu"], t), s3d(P["fo"], t)
                    if np.isfinite(a) and np.isfinite(b):
                        sig[o] = a - b
            for o in list(pos):
                s = sig.get(o, np.nan)
                if not np.isfinite(s) or pos[o]["d"] * s < EXIT:
                    c = 2 * LEG * pos[o]["N"]; eq -= c; stats["cost"] += c; del pos[o]
            for o, s in sorted(sig.items(), key=lambda kv: -abs(kv[1])):
                if len(pos) >= SLOTS:
                    break
                if o in pos or abs(s) <= ENTER:
                    continue
                P = pairs[o]; N = SLOT * eq
                pu, po = P["pu"].at[t], P["po"].at[t]
                pos[o] = dict(d=1 if s > 0 else -1, N=N, qu=N / pu, qo=N / po, pu=pu, po=po)
                c = 2 * LEG * N; eq -= c; stats["cost"] += c; stats["n"] += 1
        rows.append((t, eq, len(pos)))
    c = pd.DataFrame(rows, columns=["t", "eq", "n"]).set_index("t")
    return c, stats


def report(name, c, st):
    d = c["eq"].resample("1D").last().pct_change().dropna()
    yrs = len(d) / 365
    tot = c["eq"].iloc[-1] / c["eq"].iloc[0] - 1
    t = d.mean() / d.std() * np.sqrt(len(d)) if d.std() > 0 else 0
    sh = d.mean() / d.std() * np.sqrt(365) if d.std() > 0 else 0
    dd = (1 - c["eq"] / c["eq"].cummax()).max()
    gross = (st["fund"] + st["price"]) / yrs
    print(f"{name}: anual {100 * ((1 + tot) ** (1 / yrs) - 1):6.2f} % | t {t:5.2f} | Sharpe {sh:5.2f} | DD {100 * dd:5.2f} % | "
          f"entradas {st['n']} | ocupación media {c['n'].mean():.2f}/5 | funding {100 * st['fund'] / yrs:+.2f} %/año | "
          f"precio {100 * st['price'] / yrs:+.2f} %/año | costes {100 * st['cost'] / yrs:.2f} %/año | bruto {100 * gross:+.2f} %/año")


def describe(pairs, start, end):
    rows = []
    for o, P in pairs.items():
        a = P["fu"].loc[start:end].resample("1D").sum() * 3 / 3; b = P["fo"].loc[start:end].resample("1D").sum()
        j = pd.concat([a, b], axis=1).dropna()
        if len(j) > 30:
            rows.append((o, 100 * 365 * (j.iloc[:, 0] - j.iloc[:, 1]).mean()))
    d = pd.DataFrame(rows, columns=["par", "dif_anual_%"]).sort_values("dif_anual_%")
    print(f"  diferencial medio de funding USDT − otro (%/año): mediana {d['dif_anual_%'].median():+.2f}, "
          f"{(d['dif_anual_%'] > 0).mean():.0%} de pares positivos; extremos {d.iloc[0].tolist()} / {d.iloc[-1].tolist()}")


if __name__ == "__main__":
    for kind, dev, exa in (("X1", ("2024-01-08", "2025-03-31"), ("2025-04-01", "2026-10-31")),
                           ("X2", ("2022-07-08", "2024-06-30"), ("2024-07-01", "2026-10-31"))):
        pairs = load_pairs(kind)
        print(f"\n===== {kind}: {len(pairs)} pares")
        for per, (a, b) in (("desarrollo", dev), ("EXAMEN", exa)):
            describe(pairs, a, b)
            c, st = run(pairs, a, b)
            report(f"{kind} {per} {a}→{b}", c, st)
