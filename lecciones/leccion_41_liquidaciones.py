"""Lección 41 — Mapas de liquidaciones estimados (docs/leccion_41.md)."""
import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data, universe  # noqa: E402

STEP = np.log(1.0025)
LEV = [(10, 0.4), (25, 0.3), (50, 0.2), (100, 0.1)]
EXA0 = pd.Timestamp("2023-07-01", tz="UTC")


def coin(args):
    sym, months = args
    m = pd.read_parquet(ROOT / f"data/metrics/{sym}.parquet")["sum_open_interest"]
    h = data.load(sym, "1h")[["high", "low", "close"]]
    m.index = pd.DatetimeIndex(m.index).tz_convert("UTC") if m.index.tz else pd.DatetimeIndex(m.index).tz_localize("UTC")
    df = h.join(m.rename("oi"), how="inner").dropna()
    df = df[df.oi > 0]
    if len(df) < 24 * 60:
        return []
    lc = np.log(df.close.to_numpy()); lh = np.log(df.high.to_numpy()); ll = np.log(df.low.to_numpy())
    lo_k = int(np.floor((ll.min() + np.log(0.98)) / STEP)) - 5
    hi_k = int(np.ceil((lh.max() + np.log(1.02)) / STEP)) + 5
    nb = hi_k - lo_k + 1
    longs, shorts = np.zeros(nb), np.zeros(nb)        # masa de liquidaciones de largos / cortos por casilla
    oi = df.oi.to_numpy(); idx = df.index
    K = lambda x: int(np.floor(x / STEP)) - lo_k
    out = []
    hi_arr, lo_arr = df.high.to_numpy(), df.low.to_numpy()
    for t in range(1, len(df)):
        # 1) liquidaciones en la hora t
        kl = K(ll[t]); kh = K(lh[t])
        longs[max(kl, 0):] = 0.0                       # niveles de largos por encima del mínimo → liquidados
        shorts[:min(kh + 1, nb)] = 0.0                 # niveles de cortos por debajo del máximo → liquidados
        # 2) cambio del interés abierto
        d = oi[t] - oi[t - 1]
        if d < 0 and oi[t - 1] > 0:
            f = oi[t] / oi[t - 1]; longs *= f; shorts *= f
        elif d > 0:
            for L, w in LEV:
                kl_ = K(lc[t] + np.log(1 - 1 / L)); ks_ = K(lc[t] + np.log(1 + 1 / L))
                if 0 <= kl_ < nb: longs[kl_] += d * w
                if 0 <= ks_ < nb: shorts[ks_] += d * w
        # 3) medición diaria a las 00:00 (cierre de la vela de las 23:00)
        ts = idx[t] + pd.Timedelta("1h")
        if ts.hour != 0 or pd.Timestamp(ts.year, ts.month, 1, tz="UTC") not in months or t + 168 >= len(df):
            continue
        kp = K(lc[t])
        k5u, k5d = K(lc[t] + np.log(1.05)), K(lc[t] + np.log(0.95))
        S = shorts[kp + 1:k5u + 1].sum(); Lm = longs[max(k5d, 0):kp].sum()
        I = (S - Lm) / (S + Lm) if S + Lm > 0 else np.nan
        r24 = df.close.iloc[t + 24] / df.close.iloc[t] - 1
        # LM2
        k10u, k10d = K(lc[t] + np.log(1.10)), K(lc[t] + np.log(0.90))
        su, sd = shorts[kp + 1:k10u + 1], longs[max(k10d, 0):kp]
        rec = {"sym": sym, "t": ts, "I": I, "r24": r24}
        if su.size and sd.size and su.max() > 0 and sd.max() > 0:
            ku = kp + 1 + int(np.argmax(su)); kd = max(k10d, 0) + int(np.argmax(sd))
            pu, pdn = np.exp((ku + lo_k) * STEP), np.exp((kd + lo_k + 1) * STEP)
            first = None
            for j in range(t + 1, t + 169):
                up, dn = hi_arr[j] >= pu, lo_arr[j] <= pdn
                if up and dn:
                    first = None; break                    # ambos en la misma hora: se descarta
                if up or dn:
                    first = "up" if up else "dn"; break
            if first:
                du, dd = np.log(pu) - lc[t], lc[t] - np.log(pdn)
                big = "up" if su.max() > sd.max() else "dn"
                p_big = (dd / (du + dd)) if big == "up" else (du / (du + dd))
                rec.update({"big_first": float(first == big), "p_big": p_big, "mass_ratio": max(su.max(), sd.max()) / min(su.max(), sd.max())})
        out.append(rec)
    return out


def run(df, label):
    print(f"\n=== {label}: {df.sym.nunique()} monedas, {len(df)} observaciones diarias")
    x = df.dropna(subset=["I"])
    rho, p = stats.spearmanr(x.I, x.r24)
    print(f"LM1 correlación de rangos I vs rentabilidad 24 h: {rho:+.4f} (p {p:.3f})")
    s = x[x.I.abs() >= 0.5].copy()
    s["ret"] = np.sign(s.I) * s.r24 - 0.0014
    d = s.groupby(s.t.dt.floor("1D")).ret.mean()
    print(f"LM1 estrategia (|I| ≥ 0,5): n {len(s)} | media {100 * s.ret.mean():+.3f} % por operación | t (días) {d.mean() / d.std() * np.sqrt(len(d)):+.2f} | "
          f"aciertos {100 * (s.ret > 0).mean():.1f} %")
    for q in (0.5, 0.8):
        g = x[x.I >= q]; b = x[x.I <= -q]
        print(f"   I ≥ {q}: rentabilidad media 24 h {100 * g.r24.mean():+.3f} % (n {len(g)}) | I ≤ −{q}: {100 * b.r24.mean():+.3f} % (n {len(b)})")
    y = df.dropna(subset=["big_first"])
    if len(y):
        ex = y.big_first - y.p_big
        z = ex.mean() / np.sqrt((y.p_big * (1 - y.p_big)).sum()) * len(y)
        print(f"LM2 la zona MÁS GRANDE se toca primero: {100 * y.big_first.mean():.1f} % | esperado por distancia {100 * y.p_big.mean():.1f} % | "
              f"exceso {100 * ex.mean():+.2f} pts (z {z:+.2f}, n {len(y)})")
        big = y[y.mass_ratio >= 3]
        exb = big.big_first - big.p_big
        print(f"    cuando la zona grande es ≥ 3 veces la otra: {100 * big.big_first.mean():.1f} % vs {100 * big.p_big.mean():.1f} % "
              f"(exceso {100 * exb.mean():+.2f} pts, n {len(big)})")


if __name__ == "__main__":
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    have = {p.stem for p in (ROOT / "data/metrics").glob("*.parquet")}
    syms = sorted(set(OLD + NEW) & have)
    mem = universe.monthly_members(universe.daily_volume(syms), 20)
    by = {}
    for mth, ss in mem.items():
        for s in ss | {"BTCUSDT", "ETHUSDT"}:
            if s in have:
                by.setdefault(s, set()).add(mth)
    with ProcessPoolExecutor(4) as ex:
        rows = [r for part in ex.map(coin, [(s, by[s]) for s in sorted(by)]) for r in part]
    D = pd.DataFrame(rows)
    D.to_csv(ROOT / "docs/l41_observaciones.csv.gz", index=False)
    run(D[D.t < EXA0], "DESARROLLO 2020-09 → 2023-06")
    run(D[D.t >= EXA0], "EXAMEN 2023-07 → 2026-10")
    b = D[D.sym.isin(["BTCUSDT", "ETHUSDT"])]
    run(b[b.t >= EXA0], "Solo BTC y ETH, examen")
