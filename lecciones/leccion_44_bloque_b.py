"""Lección 44 — Mejorar las salidas y entradas del bloque B (docs/leccion_44.md)."""
import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import data, indicators as ind, lab15, universe  # noqa: E402
from leccion_22_validacion import st  # noqa: E402

BAR = pd.Timedelta("4h")
COST = 0.0010 + 0.0004                                         # por lado, como lab15 (dos patas)
VARIANTS = {"B actual": {}, "Q1 filtro de cortos saturados": {"crowd": -0.0003}, "Q2 piramidación": {"pyramid": True},
            "Q3 stop a cero tras +1R": {"breakeven": True}, "Q4 salida por tiempo (5 días sin +0,5R)": {"timestop": True}}


def frame(sym, btc, f_btc):
    a = data.load(sym, "1h")["close"]
    r1 = (a / btc.reindex(a.index)).dropna()
    if len(r1) < 24 * 120:
        return None
    df = r1.resample("4h").agg(["first", "max", "min", "last"]).dropna()
    df.columns = ["open", "high", "low", "close"]
    df["atr"] = ind.atr(df, 14)
    dd = df["close"].resample("1D").last().dropna()
    tr = ind.daily_on_intraday(np.sign(dd - ind.ema(dd, 50)), df.index, BAR)
    df["sig"] = (tr < 0) & (df["close"] < df["low"].rolling(120).min().shift(1))
    fa = lab15._funding(sym)
    df["f3"] = fa.rolling("72h").sum().div(9).reindex(df.index, method="ffill").fillna(0) if len(fa) else 0.0
    fund = pd.concat([fa, -f_btc]).sort_index()
    return df, fund


def trades(df, fund, crowd=None, pyramid=False, breakeven=False, timestop=False, m=5.0):
    o, h, l, c, a = (df[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    t, tns = df.index, df.index.as_unit("ns").asi8
    f_t = fund.index.as_unit("ns").asi8; f_cum = np.concatenate([[0.0], np.cumsum(fund.to_numpy())])
    n, rows, d = len(df), [], -1
    for i in np.flatnonzero(df["sig"].to_numpy()):
        if i + 1 >= n or not (a[i] > 0):
            continue
        if crowd is not None and df["f3"].iloc[i] < crowd:
            continue
        j = i + 1; entry = o[j]; R = m * a[i]; stop = entry + R; ext = entry
        units = [(entry, 0.5 if pyramid else 1.0)]
        adds = [entry - a[i], entry - 2 * a[i]] if pyramid else []
        exit_px, k = None, j
        for k in range(j, n):
            if k > j and o[k] >= stop:
                exit_px = o[k]; break
            if h[k] >= stop:
                exit_px = stop; break
            if timestop and k == j + 29 and (entry - ext) < 0.5 * R:
                exit_px = c[k]; break
            for p in list(adds):
                if l[k] <= p:
                    units.append((p, 0.25)); adds.remove(p)
            ext = min(ext, l[k])
            stop = min(stop, ext + m * a[k])
            if breakeven and entry - ext >= R:
                stop = min(stop, entry)
        if exit_px is None:
            exit_px, k = c[n - 1], n - 1
        fa_ = np.searchsorted(f_t, tns[j], side="right"); fb_ = np.searchsorted(f_t, tns[k] + BAR.value, side="right")
        fsum = f_cum[fb_] - f_cum[fa_]
        r = sum(w * (d * (exit_px - p) - (p + exit_px) * COST - d * fsum * p) / R for p, w in units)
        rows.append((t[j], t[k] + BAR, d, entry, R, r))
    return pd.DataFrame(rows, columns=["entry_time", "exit_time", "side", "entry", "R", "r_net"])


def job(args):
    sym, months = args
    btc = data.load("BTCUSDT", "1h")["close"]; f_btc = lab15._funding("BTCUSDT")
    fr = frame(sym, btc, f_btc)
    if fr is None:
        return sym, None, {}
    df, fund = fr
    out = {}
    for name, kw in VARIANTS.items():
        T = trades(df, fund, **kw)
        if len(T):
            T = T[universe.is_member(months, sym, pd.DatetimeIndex(T.entry_time))]
            T["symbol"] = sym
        out[name] = T
    return sym, df["close"], out


if __name__ == "__main__":
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    syms = sorted(set(OLD + NEW))
    mem = universe.monthly_members(universe.daily_volume(syms), 30)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem) for s in syms if s != "BTCUSDT"]))
    closes = {s: c for s, c, _ in res if c is not None}
    fmt = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+6.1f} % | caída {100 * d['DD']:5.1f} %"
    print("Bloque B (riesgo 1 % por operación, máximo 10 posiciones, universo de las 30 más líquidas)")
    for name in VARIANTS:
        cands = pd.concat([o[name] for _, c, o in res if c is not None and name in o and len(o[name])], ignore_index=True)
        daily, tk, _ = lab15._run_portfolio(cands, closes, 0.01, 10)
        line = f"  {name:42s}"
        for lab, a_, b_ in (("2020–22", "2020-03-01", "2022-12-31"), ("2023–26", "2023-01-01", "2026-10-31")):
            line += f" | {lab}: {fmt(st(daily.loc[a_:b_]))}"
        print(line + f" | operaciones {len(tk)} | E {tk.ret.mean():+.3f}R")
