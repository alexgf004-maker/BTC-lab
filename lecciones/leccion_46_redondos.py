"""Lección 46 — Ruptura de números redondos (docs/leccion_46.md)."""
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
from sclab import data, lab15, universe  # noqa: E402

COST = 0.0007


def daily(sym):
    h = data.load(sym, "1h")
    d = h.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return d


def signals(d, side, shift):
    """Lista de (i, L, paso): señal al cierre del día i."""
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    out = []
    for i in range(4, len(d)):
        P = c[i - 1]
        if not P > 0:
            continue
        step = 5 * 10 ** (np.floor(np.log10(P)) - 1)
        if side == -1:
            top, bot = c[i - 3:i].min(), c[i]
            if not bot < top:
                continue
            k = np.floor((top - shift * step) / step)           # nivel más alto ≤ mínimo de los 3 cierres
            L = (k + shift) * step
            if L > bot and l[i - 3:i].min() <= L * 1.01:
                out.append((i, L, step))
        else:
            bot, top = c[i - 3:i].max(), c[i]
            if not top > bot:
                continue
            k = np.ceil((bot - shift * step) / step)
            L = (k + shift) * step
            if L < top and h[i - 3:i].max() >= L * 0.99:
                out.append((i, L, step))
    return out


def trades(d, fund, side, entry_mode, shift):
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    t = d.index
    rows, busy = [], -1
    for i, L, step in signals(d, side, shift):
        if i <= busy or i + 1 >= len(d):
            continue
        j = None
        if entry_mode == 1:
            j, px = i + 1, o[i + 1]
        else:
            for k in range(i + 1, min(i + 4, len(d))):
                if (side == -1 and h[k] >= L * 1.001) or (side == 1 and l[k] <= L * 0.999):
                    j, px = k, (o[k] if (side == -1 and o[k] > L) or (side == 1 and o[k] < L) else L)
                    break
            if j is None:
                continue
        tgt = L + side * step                                   # corto: L − paso; largo: L + paso
        ex, k = None, j
        for k in range(j, min(j + 20, len(d))):
            inval = (c[k] > L) if side == -1 else (c[k] < L)
            hit = (l[k] <= tgt) if side == -1 else (h[k] >= tgt)
            if inval:
                ex = c[k]; break
            if hit:
                ref = o[k] if k > j else px                     # si ya se pasó el objetivo, se sale al precio disponible
                ex = min(ref, tgt) if side == -1 else max(ref, tgt); break
        if ex is None:
            ex = c[k]
        f = fund[(fund.index > t[j]) & (fund.index <= t[k] + pd.Timedelta("1D"))].sum() if len(fund) else 0.0
        r = side * (ex / px - 1) - 2 * COST - side * f
        rows.append((t[j], t[k], side, px, ex, r))
        busy = k
    return pd.DataFrame(rows, columns=["entry_time", "exit_time", "side", "entry", "exit", "r"])


VARS = [(s, e) for s in (-1, 1) for e in (1, 2)]


def job(args):
    sym, mem = args
    try:
        d = daily(sym)
    except Exception:
        return sym, {}
    if len(d) < 200:
        return sym, {}
    fund = lab15._funding(sym)
    out = {}
    for s, e in VARS:
        for sh in (0.0, 0.37):
            T = trades(d, fund, s, e, sh)
            if len(T):
                T = T[universe.is_member(mem, sym, pd.DatetimeIndex(T.entry_time))]
                T["symbol"] = sym
            out[(s, e, sh)] = T
    return sym, out


def tstat(T):
    if len(T) < 3:
        return float("nan")
    wk = T.entry_time.dt.to_period("W")
    u = T.r - T.r.mean()
    g = u.groupby(wk.values).sum()
    se = np.sqrt((g ** 2).sum()) / len(T)
    return T.r.mean() / se if se > 0 else float("nan")


if __name__ == "__main__":
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    syms = sorted(set(OLD + NEW) | {"BTCUSDT", "ETHUSDT"})
    mem = universe.monthly_members(universe.daily_volume(syms), 30)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem) for s in syms]))
    names = {(-1, 1): "Corto, entrada al día siguiente", (-1, 2): "Corto, vender el rebote a L",
             (1, 1): "Largo, entrada al día siguiente", (1, 2): "Largo, comprar el retroceso a L"}
    for s, e in VARS:
        print(f"\n{names[(s, e)]}")
        for sh, lab in ((0.0, "redondos"), (0.37, "placebo ")):
            T = pd.concat([o[(s, e, sh)] for _, o in res if (s, e, sh) in o and len(o[(s, e, sh)])], ignore_index=True)
            T["entry_time"] = pd.to_datetime(T.entry_time)
            line = f"  {lab}:"
            for pl, a, b in (("desarrollo", "2020-01-01", "2022-12-31"), ("examen", "2023-01-01", "2026-12-31")):
                X = T[(T.entry_time >= pd.Timestamp(a, tz="UTC")) & (T.entry_time <= pd.Timestamp(b, tz="UTC"))]
                line += f" | {pl}: n {len(X):4d}, media {100 * X.r.mean():+.2f} %, t {tstat(X):+.2f}"
            line += f" | total t {tstat(T):+.2f}"
            bt = T[T.symbol.isin(["BTCUSDT", "ETHUSDT"])]
            line += f" | BTC+ETH: n {len(bt)}, media {100 * bt.r.mean():+.2f} %"
            print(line)
