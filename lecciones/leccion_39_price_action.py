"""Lección 39 — Ruptura, retroceso, pin bar y confluencias (docs/leccion_39.md)."""
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

FX_COST = {"EURUSD": 0.5e-4, "USDJPY": 0.6e-4, "GBPUSD": 0.8e-4, "AUDUSD": 0.8e-4, "USDCAD": 0.8e-4, "USDCHF": 0.8e-4,
           "NZDUSD": 1.2e-4, "EURJPY": 1.0e-4, "EURGBP": 1.0e-4, "GBPJPY": 1.5e-4}
TESTS = [("P1 conservadora 1:2", "P1", "cons", 2), ("P1 conservadora 1:5", "P1", "cons", 5),
         ("P2 conservadora 1:2", "P2", "cons", 2), ("P2 conservadora 1:5", "P2", "cons", 5), ("P1 agresiva 1:2", "P1", "agr", 2)]


def bars4(h1):
    return h1.resample("4h", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def setups(H):
    """Lista de pin bars válidas: (índice, lado, mínimo/máximo de la mecha, máximo/mínimo, cumple_P2)."""
    o, h, l, c = (H[x].to_numpy() for x in ("open", "high", "low", "close"))
    s21, s50 = H.close.rolling(21).mean().to_numpy(), H.close.rolling(50).mean().to_numpy()
    tr = np.maximum(h - l, np.maximum(abs(h - np.roll(c, 1)), abs(l - np.roll(c, 1))))
    atr = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()
    hi40, lo40 = H.high.rolling(40).max().shift(1).to_numpy(), H.low.rolling(40).min().shift(1).to_numpy()
    out, used = [], set()
    n = len(H)
    for b in range(60, n - 1):
        for side in (1, -1):
            lvl = hi40[b] if side == 1 else lo40[b]
            if not np.isfinite(lvl) or (side == 1 and not c[b] > lvl) or (side == -1 and not c[b] < lvl):
                continue
            if (side == 1 and c[b - 1] > hi40[b - 1]) or (side == -1 and c[b - 1] < lo40[b - 1]):
                continue                                         # solo la primera vela de la ruptura
            swing0 = lo40[b] if side == 1 else hi40[b]
            ext = h[b] if side == 1 else l[b]
            for k in range(b + 1, min(b + 21, n - 1)):
                trend = (c[k] > s21[k] > s50[k]) if side == 1 else (c[k] < s21[k] < s50[k])
                rng = h[k] - l[k]
                if rng <= 0 or not np.isfinite(atr[k]):
                    ext = max(ext, h[k]) if side == 1 else min(ext, l[k]); continue
                if side == 1:
                    wick, body_ok = min(o[k], c[k]) - l[k], c[k] >= l[k] + 2 / 3 * rng
                    touch = abs(l[k] - lvl) <= 0.5 * atr[k] and c[k] >= lvl - 0.5 * atr[k]
                else:
                    wick, body_ok = h[k] - max(o[k], c[k]), c[k] <= h[k] - 2 / 3 * rng
                    touch = abs(h[k] - lvl) <= 0.5 * atr[k] and c[k] <= lvl + 0.5 * atr[k]
                if trend and wick >= 2 / 3 * rng and body_ok and touch and (k, side) not in used:
                    tip = l[k] if side == 1 else h[k]
                    near_ma = abs(tip - s21[k]) <= atr[k]
                    imp = (ext - swing0) * side
                    depth = (ext - tip) * side / imp if imp > 0 else np.nan
                    p2 = bool(near_ma and 0.382 <= depth <= 0.786)
                    out.append((k, side, l[k], h[k], c[k], atr[k], p2))
                    used.add((k, side))
                    break
                ext = max(ext, h[k]) if side == 1 else min(ext, l[k])
                if (side == 1 and c[k] < lvl - 0.5 * atr[k]) or (side == -1 and c[k] > lvl + 0.5 * atr[k]):
                    break                                        # la ruptura falló
    return out


def trade(H, k, side, lo, hi, cl, atr, mode, tgt, c_side, c_mkt):
    h, l, c = H.high.to_numpy(), H.low.to_numpy(), H.close.to_numpy()
    stop = lo - 0.1 * atr if side == 1 else hi + 0.1 * atr
    if mode == "agr":
        entry, start, cost_in = cl, k + 1, c_mkt
    else:
        entry = (lo + hi) / 2; start = None; cost_in = c_side
        for j in range(k + 1, min(k + 4, len(H))):
            if (side == 1 and l[j] <= entry) or (side == -1 and h[j] >= entry):
                start = j; break
        if start is None:
            return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    target = entry + side * tgt * risk
    for j in range(start, min(start + 60, len(H))):
        if (side == 1 and l[j] <= stop) or (side == -1 and h[j] >= stop):
            ex, cout = stop, c_mkt; break
        if j > start or mode == "agr":
            if (side == 1 and h[j] >= target) or (side == -1 and l[j] <= target):
                ex, cout = target, c_side; break
    else:
        ex, cout = c[min(start + 59, len(H) - 1)], c_mkt
    return (side * (ex - entry) - (cost_in + cout) * entry) / risk


def run_symbol(args):
    name, h1, c_side, c_mkt, months = args
    H = bars4(h1)
    rows = []
    for k, side, lo, hi, cl, atr, p2 in setups(H):
        t = H.index[k]
        if months is not None and pd.Timestamp(t.year, t.month, 1, tz="UTC") not in months:
            continue
        for label, kind, mode, tgt in TESTS:
            if kind == "P2" and not p2:
                continue
            r = trade(H, k, side, lo, hi, cl, atr, mode, tgt, c_side, c_mkt)
            if r is not None:
                rows.append((label, name, t, r))
    return rows


def fx_job(p):
    h = pd.read_parquet(ROOT / f"data/fxd/{p}.parquet")
    return run_symbol((p, h, FX_COST[p], FX_COST[p] + 0.3e-4, None))


def crypto_job(a):
    s, months = a
    h = data.load(s, "1h")[["open", "high", "low", "close"]]
    return run_symbol((s, h, 0.0002, 0.0007, months))


def stats(T, label):
    if T.empty:
        print(f"   {label:28s} sin operaciones"); return
    d = T.groupby(T.t.dt.floor("1D")).R.mean()
    t = d.mean() / d.std() * np.sqrt(len(d)) if len(d) > 2 else np.nan
    pf = T.R[T.R > 0].sum() / max(1e-12, -T.R[T.R < 0].sum())
    print(f"   {label:28s} n {len(T):5d} | E {T.R.mean():+.3f}R (t {t:+5.2f}) | acierto {100 * (T.R > 0).mean():4.1f} % | PF {pf:.2f}")


if __name__ == "__main__":
    with ProcessPoolExecutor(4) as ex:
        fx = [r for part in ex.map(fx_job, list(FX_COST)) for r in part]
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    mem = universe.monthly_members(universe.daily_volume(sorted(set(OLD + NEW))), 20)
    by = {}
    for m, ss in mem.items():
        for s in ss | {"BTCUSDT", "ETHUSDT"}:
            by.setdefault(s, set()).add(m)
    with ProcessPoolExecutor(4) as ex:
        cr = [r for part in ex.map(crypto_job, [(s, by[s]) for s in sorted(by)]) for r in part]
    for market, rows, dev_end, exa0 in (("FOREX (10 pares)", fx, "2018-12-31", "2019-01-01"),
                                         ("CRIPTO (BTC, ETH y top 20)", cr, "2023-06-30", "2023-07-01")):
        T = pd.DataFrame(rows, columns=["test", "sym", "t", "R"])
        T["t"] = pd.to_datetime(T.t, utc=True)
        print(f"\n===== {market}")
        for label, *_ in TESTS:
            x = T[T.test == label]
            print(f"  {label}")
            stats(x[x.t <= dev_end], "desarrollo")
            stats(x[x.t >= exa0], "EXAMEN")
        T.to_csv(ROOT / f"docs/l39_{'fx' if 'FOREX' in market else 'cripto'}.csv.gz", index=False)
