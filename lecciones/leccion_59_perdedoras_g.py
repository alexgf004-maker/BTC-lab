"""Lección 59 — Rasgos de las operaciones perdedoras del bloque G (docs/leccion_59.md).
Uso: python3 lecciones/leccion_59_perdedoras_g.py buscar
     python3 lecciones/leccion_59_perdedoras_g.py validar <variable> <bajo|alto>"""
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
from bot.patrones import bear_breaks  # noqa: E402
from bot.strategies.momentum import backtest, features  # noqa: E402

G3 = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
VARS = {"ret3": "subida de 3 h", "z": "pico de operaciones (z)", "ext_ema": "distancia sobre la EMA200", "atr_pct": "volatilidad (ATR horario / precio)",
        "f3": "funding 3 días", "btc_tr": "BTC frente a su media de 50 días", "ret24p": "rentabilidad de las 24 h previas",
        "vol24": "volumen 24 h / media de 7 días"}


def job(args):
    sym, mem = args
    try:
        h = data.load(sym, "1h")
    except Exception:
        return []
    if len(h) < 24 * 60 or "count" not in h:
        return []
    df = h[["open", "high", "low", "close", "count"]]
    T = backtest(df)
    if T.empty:
        return []
    f = features(df)
    fu = lab15._funding(sym)
    f3s = fu.rolling("72h").sum().div(9) if len(fu) else pd.Series(dtype=float)
    d4 = h[["open", "high", "low", "close"]].resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    bears = bear_breaks(d4)
    btc = data.load("BTCUSDT", "1h")["close"].resample("1D").last()
    btr = (btc / btc.ewm(span=50, adjust=False).mean() - 1).shift(1)
    qv = h["quote_volume"]
    rows = []
    pos = pd.Series(np.arange(len(f)), index=f.index)
    for _, r in T.iterrows():
        tdec = r.signal + pd.Timedelta("1h")
        if mem is not None and not universe.is_member(mem, sym, pd.DatetimeIndex([r.signal]))[0]:
            continue
        v = f3s.asof(tdec) if len(f3s) and tdec >= f3s.index[0] else 0.0
        if v == v and v > 0.0003:
            continue                                                     # filtro de euforia (L45)
        if len(bears) and ((bears > tdec - pd.Timedelta("120h")) & (bears <= tdec)).any():
            continue                                                     # filtro de figuras (L53)
        i = pos[r.signal]; row = f.iloc[i]
        rows.append({"t": tdec, "R": r.R, "ret3": row.ret3, "z": row.z, "ext_ema": row.close / row.ema200 - 1,
                     "atr_pct": row.atr / row.close, "f3": v if v == v else np.nan, "btc_tr": btr.asof(tdec.floor("1D")),
                     "ret24p": f.close.iloc[i - 3] / f.close.iloc[i - 27] - 1 if i >= 27 else np.nan,
                     "vol24": qv.iloc[max(0, i - 23):i + 1].sum() / (qv.iloc[max(0, i - 167):i + 1].sum() / 7)})
    return rows


def collect(syms, mem):
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem) for s in syms]))
    return pd.DataFrame([r for rr in res for r in rr])


def per(T):
    return T[T.t < pd.Timestamp("2023-01-01", tz="UTC")], T[T.t >= pd.Timestamp("2023-01-01", tz="UTC")]


if __name__ == "__main__":
    T = collect(G3, None)
    if sys.argv[1] == "buscar":
        print(f"Búsqueda (G en BTC, ETH, SOL): {len(T)} operaciones, acierto {100 * (T.R > 0).mean():.0f} %, media {T.R.mean():+.3f}R\n")
        for v, desc in VARS.items():
            X = T.dropna(subset=[v]); q = X[v].quantile([1 / 3, 2 / 3]).to_numpy()
            line = f"  {desc:36s}"
            for g, Y in (("bajo", X[X[v] <= q[0]]), ("medio", X[(X[v] > q[0]) & (X[v] <= q[1])]), ("alto", X[X[v] > q[1]])):
                line += f" | {g}: n {len(Y)}, acierto {100 * (Y.R > 0).mean():3.0f} %, media {Y.R.mean():+.3f}R"
            print(line + f" | cortes {q[0]:.4g} / {q[1]:.4g}", flush=True)
    else:
        v, side = sys.argv[2], sys.argv[3]
        q = T[v].quantile([1 / 3, 2 / 3]).to_numpy(); cut = q[1] if side == "alto" else q[0]
        keep = (lambda X: X[~(X[v] > cut)]) if side == "alto" else (lambda X: X[~(X[v] <= cut)])
        print(f"Filtro: quitar el tercil {side} de '{VARS[v]}' (corte fijo: {cut:.4g})")
        print("\n(2) G real (BTC, ETH, SOL):")
        for name, X in (("G actual", T), ("G con filtro", keep(T))):
            dev, exa = per(X); d0, e0 = per(T)
            print(f"  {name:13s} | desarrollo: n {len(dev)} ({100 * len(dev) / len(d0):.0f} %), {dev.R.mean():+.3f}R | "
                  f"examen: n {len(exa)} ({100 * len(exa) / len(e0):.0f} %), {exa.R.mean():+.3f}R")
        vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
        mem = universe.monthly_members(vol, 30)
        V = collect(sorted(set().union(*mem.values()) - set(G3)), mem)
        print(f"\n(1) Validación: misma regla en las demás monedas del top 30 ({len(V)} operaciones):")
        for name, X in (("sin filtro", V), ("con filtro", keep(V))):
            dev, exa = per(X)
            print(f"  {name:13s} | desarrollo: n {len(dev)}, {dev.R.mean():+.3f}R | examen: n {len(exa)}, {exa.R.mean():+.3f}R", flush=True)
