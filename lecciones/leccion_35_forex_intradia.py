"""Lección 35 — Estrategias intradía y de swing en forex con velas de 1 h (docs/leccion_35.md)."""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
FXH = ROOT / "data/fxd"
PAIRS = {"EURUSD": 0.5e-4, "USDJPY": 0.6e-4, "GBPUSD": 0.8e-4, "AUDUSD": 0.8e-4, "USDCAD": 0.8e-4, "USDCHF": 0.8e-4,
         "NZDUSD": 1.2e-4, "EURJPY": 1.0e-4, "EURGBP": 1.0e-4, "GBPJPY": 1.5e-4}      # coste por lado (diferencial + comisión)
SLIP = 0.3e-4                                                                         # deslizamiento extra en stops y salidas a mercado
DEV = ("2012-01-01", "2018-12-31")
EXA = ("2019-01-01", "2026-10-31")


def load(pair):
    df = pd.read_parquet(FXH / f"{pair}.parquet")
    return df[["open", "high", "low", "close"]]


def fx_open(idx):
    """True en horas con el mercado de divisas abierto (de domingo 22:00 a viernes 21:00 UTC, aprox.)."""
    d, h = idx.dayofweek, idx.hour
    return ~((d == 5) | ((d == 4) & (h >= 21)) | ((d == 6) & (h < 22)))


def bars(h1, rule):
    return h1.resample(rule, label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def walk(h1, t0, side, stop, target, t_end):
    seg = h1.loc[t0:t_end - pd.Timedelta("1h")]
    for hi, lo in zip(seg["high"].to_numpy(), seg["low"].to_numpy()):
        if (side == -1 and hi >= stop) or (side == 1 and lo <= stop):
            return stop, "stop"
        if target is not None and ((side == -1 and lo <= target) or (side == 1 and hi >= target)):
            return target, "objetivo"
    return (seg["close"].iloc[-1], "tiempo") if len(seg) else (np.nan, "nada")


def result(side, entry, exit_, kind, risk, c, maker_entry=False):
    cost = c * entry + (c if kind == "objetivo" else c + SLIP) * entry + (0 if maker_entry else SLIP * entry)
    return (side * (exit_ - entry) - cost) / risk


# ------------------------------------------------------------------ Y1–Y3: CRT y CRT + CISD (reglas de la Lección 33)
def crt(pair, h1, c, rule, ltf, minrisk):
    out = []
    H = bars(h1, rule)
    L = bars(h1, ltf) if ltf else None
    per = pd.Timedelta(rule)
    o, hi, lo, cl, idx = H.open.to_numpy(), H.high.to_numpy(), H.low.to_numpy(), H.close.to_numpy(), H.index
    for i in range(1, len(H) - 1):
        if idx[i] - idx[i - 1] != per or not (lo[i - 1] < cl[i] < hi[i - 1]):
            continue
        if hi[i] > hi[i - 1] and lo[i] >= lo[i - 1]:
            side, stop, target = -1, hi[i], lo[i - 1]
        elif lo[i] < lo[i - 1] and hi[i] <= hi[i - 1]:
            side, stop, target = 1, lo[i], hi[i - 1]
        else:
            continue
        c2 = idx[i] + per
        if L is None:
            t_entry, entry = c2, cl[i]
        else:
            lt = L[(L.index >= idx[i]) & (L.index < c2)]
            if lt.empty:
                continue
            k = int(np.argmax(lt.high.to_numpy())) if side == -1 else int(np.argmin(lt.low.to_numpy()))
            Lall = L[L.index < c2]
            p = len(Lall) - len(lt) + k
            run = (Lall.close > Lall.open).to_numpy() if side == -1 else (Lall.close < Lall.open).to_numpy()
            j = p if run[p] else p - 1
            if j < 0 or not run[j]:
                continue
            s = j
            while s - 1 >= 0 and run[s - 1] and j - s < 24:
                s -= 1
            level = Lall.open.iloc[s]
            if not ((side == -1 and target < level < stop) or (side == 1 and stop < level < target)):
                continue
            t_entry = None
            for t, row in L[(L.index >= c2) & (L.index < c2 + per)].iterrows():
                if (side == -1 and (row.high >= stop or row.low <= target)) or (side == 1 and (row.low <= stop or row.high >= target)):
                    break
                if (side == -1 and row.close < level) or (side == 1 and row.close > level):
                    t_entry, entry = t + pd.Timedelta(ltf), row.close
                    break
            if t_entry is None:
                continue
        risk = abs(stop - entry)
        if risk / entry < minrisk or (target - entry) * side <= 0:
            continue
        ex, kind = walk(h1, t_entry, side, stop, target, c2 + 3 * per)
        if np.isfinite(ex):
            out.append((pair, t_entry, result(side, entry, ex, kind, risk, c), kind))
    return out


# ------------------------------------------------------------------ Y4: reversión a la media 1:1 con órdenes limit
def mean_rev(pair, h1, c):
    out = []
    cl = h1.close
    sma, sd = cl.rolling(20).mean(), cl.rolling(20).std()
    z = (cl - sma) / sd
    open_ = fx_open(h1.index)
    busy = h1.index[0]
    for t in z.index[(z.abs() >= 2) & open_]:
        if t < busy:
            continue
        side = -1 if z[t] > 0 else 1
        entry = cl[t]; d = abs(entry - sma[t])
        stop, target = entry - side * d, sma[t]
        t0 = t + pd.Timedelta("1h")
        ex, kind = walk(h1, t0, side, stop, target, t0 + pd.Timedelta("24h"))
        if np.isfinite(ex) and d / entry > 0:
            out.append((pair, t0, result(side, entry, ex, kind, d, c, maker_entry=True), kind))
            busy = t0 + pd.Timedelta("24h") if kind == "tiempo" else t0 + pd.Timedelta("1h")
    return out


# ------------------------------------------------------------------ Y5: ruptura de Londres (rango asiático)
def london(pair, h1, c):
    out = []
    for day, g in h1.groupby(h1.index.floor("1D")):
        if day.dayofweek >= 5:
            continue
        asia = g[(g.index.hour >= 0) & (g.index.hour < 7)]
        sess = g[(g.index.hour >= 7) & (g.index.hour < 20)]
        if len(asia) < 6 or len(sess) < 10:
            continue
        hi, lo = asia.high.max(), asia.low.min()
        rng = hi - lo
        if rng <= 0:
            continue
        for t, row in sess[sess.index.hour < 12].iterrows():
            up, dn = row.high > hi, row.low < lo
            if up and dn:
                break
            if up or dn:
                side = 1 if up else -1
                entry = hi if up else lo
                stop = lo if up else hi
                target = entry + side * rng
                if row.close * side < stop * side:                     # stop tocado en la misma vela → pérdida
                    out.append((pair, t, result(side, entry, stop, "stop", rng, c), "stop")); break
                ex, kind = walk(h1, t + pd.Timedelta("1h"), side, stop, target, day + pd.Timedelta("20h"))
                if np.isfinite(ex):
                    out.append((pair, t, result(side, entry, ex, kind, rng, c), kind))
                break
    return out


# ------------------------------------------------------------------ Y6: bloque D (tendencia) en divisas
def trend_d(pair, h1, c, N=120, m=5.0):
    out = []
    H = bars(h1, "4h")
    tr = pd.concat([H.high - H.low, (H.high - H.close.shift()).abs(), (H.low - H.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    dd = H.close.resample("1D").last().dropna()
    ema = dd.ewm(span=50, adjust=False).mean()
    regime = np.sign(dd - ema).shift(1).reindex(H.index, method="ffill")
    hiN, loN = H.high.rolling(N).max().shift(1), H.low.rolling(N).min().shift(1)
    i, n = N + 1, len(H)
    while i < n - 1:
        side = 1 if (regime.iloc[i] > 0 and H.close.iloc[i] > hiN.iloc[i]) else (-1 if (regime.iloc[i] < 0 and H.close.iloc[i] < loN.iloc[i]) else 0)
        if side == 0:
            i += 1; continue
        entry = H.close.iloc[i]; R = m * atr.iloc[i]; stop = entry - side * R; ext = entry
        j = i + 1
        while j < n:
            if (side == 1 and H.low.iloc[j] <= stop) or (side == -1 and H.high.iloc[j] >= stop):
                ex = min(stop, H.open.iloc[j]) if side == 1 else max(stop, H.open.iloc[j]); break
            ext = max(ext, H.high.iloc[j]) if side == 1 else min(ext, H.low.iloc[j])
            stop = max(stop, ext - m * atr.iloc[j]) if side == 1 else min(stop, ext + m * atr.iloc[j])
            j += 1
        else:
            ex = H.close.iloc[-1]
        days = (H.index[min(j, n - 1)] - H.index[i]).days
        swap = 0.01 * days / 365 * entry                                   # margen del bróker en los swaps
        out.append((pair, H.index[i], (side * (ex - entry) - (2 * c + SLIP) * entry - swap) / R, "tendencia"))
        i = j + 1
    return out


# ------------------------------------------------------------------ Y7: números redondos (Osler), rebote 1:1 a 2 ATR
def round_numbers(pair, h1, c, placebo=False, seed=0):
    out = []
    step = 0.5 if "JPY" in pair else 0.005
    off = np.random.default_rng(seed).uniform(0.2, 0.8) * step if placebo else 0.0
    tr = pd.concat([h1.high - h1.low, (h1.high - h1.close.shift()).abs(), (h1.low - h1.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().to_numpy()
    hi, lo, cl, idx = h1.high.to_numpy(), h1.low.to_numpy(), h1.close.to_numpy(), h1.index
    last = {}
    for j in range(15, len(h1) - 1):
        k0, k1 = int(np.ceil((lo[j] - off) / step)), int(np.floor((hi[j] - off) / step))
        for k in range(k0, k1 + 1):
            v = k * step + off
            if j - last.get(k, -999) <= 24:
                last[k] = j; continue
            last[k] = j
            side = 1 if cl[j - 1] > v else (-1 if cl[j - 1] < v else 0)
            if not side or not atr[j - 1] > 0:
                continue
            d = 2 * atr[j - 1]
            stop, target = v - side * d, v + side * d
            if (side == 1 and lo[j] <= stop) or (side == -1 and hi[j] >= stop):
                out.append((pair, idx[j], result(side, v, stop, "stop", d, c, True), "stop")); continue
            ex, kind = walk(h1, idx[j] + pd.Timedelta("1h"), side, stop, target, idx[j] + pd.Timedelta("168h"))
            if np.isfinite(ex):
                out.append((pair, idx[j], result(side, v, ex, kind, d, c, True), kind))
    return out


def stats(T, label):
    if T.empty:
        print(f"{label}: sin operaciones"); return
    d = T.groupby(T.t.dt.floor("1D")).R.mean()
    t = d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan
    pf = T.R[T.R > 0].sum() / max(1e-12, -T.R[T.R < 0].sum())
    print(f"{label:46s} n {len(T):6d} | E {T.R.mean():+.3f}R (t {t:+5.1f}) | acierto {100 * (T.R > 0).mean():4.1f} % | PF {pf:.2f}")


if __name__ == "__main__":
    tests = {"Y1 CRT 4h": lambda p, h, c: crt(p, h, c, "4h", None, 0.001),
             "Y2 CRT 4h + CISD 1h": lambda p, h, c: crt(p, h, c, "4h", "1h", 0.001),
             "Y3 CRT diario": lambda p, h, c: crt(p, h, c, "1D", None, 0.002),
             "Y4 reversión a la media 1:1 (z ≥ 2)": mean_rev,
             "Y5 ruptura de Londres": london,
             "Y6 tendencia (bloque D)": trend_d,
             "Y7 números redondos": round_numbers,
             "   placebo números redondos": lambda p, h, c: round_numbers(p, h, c, placebo=True)}
    data_ = {p: load(p) for p in PAIRS if (FXH / f"{p}.parquet").exists()}
    print("pares:", list(data_))
    for name, fn in tests.items():
        rows = []
        for p, h in data_.items():
            rows += fn(p, h, PAIRS[p])
        T = pd.DataFrame(rows, columns=["pair", "t", "R", "kind"])
        T["t"] = pd.to_datetime(T.t, utc=True)
        print(f"\n=== {name}")
        stats(T[(T.t >= DEV[0]) & (T.t <= DEV[1])], f"desarrollo {DEV[0][:4]}–{DEV[1][:4]}")
        stats(T[(T.t >= EXA[0]) & (T.t <= EXA[1])], f"EXAMEN {EXA[0][:4]}–{EXA[1][:7]}")
        e = T[(T.t >= EXA[0])]
        stats(e[e.pair == "EURUSD"], "   solo EURUSD, examen")
