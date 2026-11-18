"""Lección 33 — CRT y CRT + CISD (docs/leccion_33.md)."""
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
from sclab import data, universe  # noqa: E402

EXA0 = pd.Timestamp("2023-07-01", tz="UTC")
START, END = pd.Timestamp("2020-03-01", tz="UTC"), pd.Timestamp("2026-10-31", tz="UTC")
TAKER, MAKER = 0.0007, 0.0002
CFG = {"T1 CRT 4h": ("4h", None, 0.005), "T2 CRT diario": ("1D", None, 0.01),
       "T3 CRT 4h + CISD 1h": ("4h", "1h", 0.005), "T4 CRT diario + CISD 4h": ("1D", "4h", 0.01)}
if "--t5" in sys.argv:
    CFG = {"T5 CRT 4h + CISD 1h, objetivo 2R": ("4h", "1h", 0.005)}


def bars(h, rule):
    return h.resample(rule, label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def path(h1, t_entry, side, entry, stop, target, expiry):
    """Recorre velas de 1h desde t_entry hasta expiry. Devuelve (salida, tipo)."""
    seg = h1.loc[t_entry:expiry - pd.Timedelta("1h")]
    for hi, lo, cl in zip(seg["high"].to_numpy(), seg["low"].to_numpy(), seg["close"].to_numpy()):
        if (side == -1 and hi >= stop) or (side == 1 and lo <= stop):
            return stop, "stop"
        if (side == -1 and lo <= target) or (side == 1 and hi >= target):
            return target, "objetivo"
    return (seg["close"].iloc[-1], "tiempo") if len(seg) else (np.nan, "nada")


def run_symbol(args):
    sym, months, = args
    h1 = data.load(sym, "1h")[["open", "high", "low", "close"]]
    h1 = h1[(h1.index >= START) & (h1.index < END)]
    if len(h1) < 24 * 30:
        return []
    out = []
    for name, (rule, ltf, minrisk) in CFG.items():
        H = bars(h1, rule)
        L = bars(h1, ltf) if ltf else None
        per = pd.Timedelta(rule)
        o, hi, lo, cl, idx = H.open.to_numpy(), H.high.to_numpy(), H.low.to_numpy(), H.close.to_numpy(), H.index
        for i in range(1, len(H) - 1):
            t2 = idx[i]
            if pd.Timestamp(t2.year, t2.month, 1, tz="UTC") not in months:
                continue
            if idx[i] - idx[i - 1] != per:
                continue
            inside = lo[i - 1] < cl[i] < hi[i - 1]
            if not inside:
                continue
            if hi[i] > hi[i - 1] and lo[i] >= lo[i - 1]:
                side, stop, target = -1, hi[i], lo[i - 1]
            elif lo[i] < lo[i - 1] and hi[i] <= hi[i - 1]:
                side, stop, target = 1, lo[i], hi[i - 1]
            else:
                continue
            c2_close = t2 + per
            expiry = c2_close + 3 * per
            if L is None:
                t_entry, entry = c2_close, cl[i]
            else:
                lt = L[(L.index >= t2) & (L.index < c2_close)]
                if lt.empty:
                    continue
                k = int(np.argmax(lt.high.to_numpy())) if side == -1 else int(np.argmin(lt.low.to_numpy()))
                Lall = L[L.index < c2_close]
                pos = len(Lall) - len(lt) + k
                bull = (Lall.close > Lall.open).to_numpy() if side == -1 else (Lall.close < Lall.open).to_numpy()
                j = pos if bull[pos] else pos - 1
                if j < 0 or not bull[j]:
                    continue
                s = j
                while s - 1 >= 0 and bull[s - 1] and j - s < 24:
                    s -= 1
                level = Lall.open.iloc[s]
                if not ((side == -1 and target < level < stop) or (side == 1 and stop < level < target)):
                    continue
                win = L[(L.index >= c2_close) & (L.index < c2_close + per)]
                t_entry, entry = None, None
                for t, row in win.iterrows():
                    if (side == -1 and row.high >= stop) or (side == 1 and row.low <= stop):
                        break
                    if (side == -1 and row.low <= target) or (side == 1 and row.high >= target):
                        break
                    if (side == -1 and row.close < level) or (side == 1 and row.close > level):
                        t_entry, entry = t + pd.Timedelta(ltf), row.close
                        break
                if t_entry is None:
                    continue
            risk = abs(stop - entry)
            if name.startswith("T5"):
                target = entry + side * 2 * risk
            if risk / entry < minrisk or (target - entry) * side <= 0:
                continue
            ex, kind = path(h1, t_entry, side, entry, stop, target, expiry)
            if not np.isfinite(ex):
                continue
            cost = (TAKER + (MAKER if kind == "objetivo" else TAKER)) * entry
            R = (side * (ex - entry) - cost) / risk
            out.append((name, sym, t_entry, side, R, kind, abs(target - entry) / risk))
    return out


def stats(x, label):
    if x.empty:
        print(f"{label}: sin operaciones"); return
    d = x.groupby(x.t.dt.floor("1D")).R.mean()
    t = d.mean() / d.std() * np.sqrt(len(d))
    pf = x.R[x.R > 0].sum() / -x.R[x.R < 0].sum()
    print(f"{label:44s} n {len(x):6d} | E {x.R.mean():+.3f}R (t {t:+5.1f}) | acierto {100 * (x.R > 0).mean():4.1f} % | "
          f"objetivo/riesgo medio {x.rr.median():.2f} | PF {pf:.2f} | salidas: obj {100 * (x.kind == 'objetivo').mean():.0f} % "
          f"stop {100 * (x.kind == 'stop').mean():.0f} % tiempo {100 * (x.kind == 'tiempo').mean():.0f} %")


if __name__ == "__main__":
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    syms = sorted(set(OLD + NEW))
    mem = universe.monthly_members(universe.daily_volume(syms), 20)
    by = {}
    for m, ss in mem.items():
        for s in ss | {"BTCUSDT", "ETHUSDT"}:
            by.setdefault(s, set()).add(m)
    with ProcessPoolExecutor(4) as ex:
        rows = [r for part in ex.map(run_symbol, [(s, by[s]) for s in sorted(by)]) for r in part]
    T = pd.DataFrame(rows, columns=["test", "symbol", "t", "side", "R", "kind", "rr"])
    T.to_csv(ROOT / ("docs/l33_T5.csv.gz" if "--t5" in sys.argv else "docs/l33_operaciones.csv.gz"), index=False)
    for name in CFG:
        print(f"\n=== {name}")
        x = T[T.test == name]
        stats(x[x.t < EXA0], "desarrollo 2020-03 → 2023-06")
        stats(x[x.t >= EXA0], "EXAMEN 2023-07 → 2026-10")
        b = x[x.symbol.isin(["BTCUSDT", "ETHUSDT"])]
        stats(b[b.t < EXA0], "  solo BTC y ETH, desarrollo")
        stats(b[b.t >= EXA0], "  solo BTC y ETH, examen")
        y = x[x.t >= EXA0]
        print(f"  examen con acierto ≥ 60 % en algún año: {[(yr, round(100 * (gg.R > 0).mean(), 1)) for yr, gg in y.groupby(y.t.dt.year)]}")
