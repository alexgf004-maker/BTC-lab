"""Lección 60 — Rasgos de las operaciones perdedoras del bloque D (docs/leccion_60.md).
Uso: python3 lecciones/leccion_60_perdedoras_d.py buscar
     python3 lecciones/leccion_60_perdedoras_d.py validar <variable> <bajo|alto>"""
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import data, universe  # noqa: E402
from leccion_22_validacion import st  # noqa: E402
from leccion_43_gestor import C, curve, fmt, prep  # noqa: E402

VARS = {"fuerza": "fuerza de la ruptura (ATR sobre el máximo)", "vol": "volatilidad (ATR 4 h / precio)", "f3": "funding 3 días",
        "ext": "extensión: cierre diario vs EMA50", "ret30": "rentabilidad 30 días", "vol24": "volumen 24 h / media 20 días",
        "btc_tr": "BTC vs su EMA50 diaria"}
EXA0 = pd.Timestamp("2023-07-01", tz="UTC")


def trades_D(b, f, X, keep=None, members=None, sym=None):
    """D actual (piramidación + euforia) con variables de entrada; `keep(row)` decide si se toma la señal."""
    o, h, l, c = b.open.to_numpy(), b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
    atr, reg, hi, f3, idx = b.atr.to_numpy(), b.reg.to_numpy(), b.hi.to_numpy(), b.f3.to_numpy(), b.index
    out, i, n = [], 121, len(b)
    while i < n - 1:
        ok = c[i] > hi[i] and reg[i] > 0 and not f3[i] > 0.0003
        if ok and members is not None and not universe.is_member(members, sym, pd.DatetimeIndex([idx[i]]))[0]:
            ok = False
        feats = {k: X[k].iloc[i] for k in VARS} if ok else None
        if ok and keep is not None and not keep(feats):
            ok = False
        if not ok:
            i += 1; continue
        e = i + 1; entry = o[e]; R = 5 * atr[i]; stop = entry - R; ext = entry
        units = [(entry, 0.5)]; adds = [entry + atr[i], entry + 2 * atr[i]]
        j = e
        while j < n:
            if l[j] <= stop:
                ex = min(stop, o[j]); break
            for a in list(adds):
                if h[j] >= a:
                    units.append((a, 0.25)); adds.remove(a)
            ext = max(ext, h[j]); stop = max(stop, ext - 5 * atr[j]); j += 1
        else:
            ex = c[-1]; j = n - 1
        fund = float(f[(f.index > idx[e]) & (f.index <= idx[j])].sum()) if len(f) else 0.0
        res = sum(w * ((ex - p) - (2 * C + fund) * p) / R for p, w in units)
        out.append({"t": idx[e], "exit": idx[j], "R": res, **feats})
        i = j + 1
    return pd.DataFrame(out)


def feats(sym, b):
    q = data.load(sym, "1h")["quote_volume"].resample("4h").sum().reindex(b.index).fillna(0)
    dd = b.close.resample("1D").last().dropna()
    ext = (dd / dd.ewm(span=50, adjust=False).mean() - 1).shift(1).reindex(b.index, method="ffill")
    btc = data.load("BTCUSDT", "1h")["close"].resample("1D").last()
    btr = (btc / btc.ewm(span=50, adjust=False).mean() - 1).shift(1).reindex(b.index.floor("1D")).to_numpy()
    X = pd.DataFrame(index=b.index)
    X["fuerza"] = (b.close - b.hi) / b.atr
    X["vol"] = b.atr / b.close
    X["f3"] = b.f3
    X["ext"] = ext
    X["ret30"] = b.close / b.close.shift(180) - 1
    X["vol24"] = q.rolling(6).sum() / (q.shift(6).rolling(120).sum() / 20)
    X["btc_tr"] = btr
    return X


def job(args):
    sym, mem, keep_spec = args
    try:
        b, f = prep(sym)
    except Exception:
        return pd.DataFrame()
    if len(b) < 300:
        return pd.DataFrame()
    X = feats(sym, b)
    keep = None
    if keep_spec:
        v, side, cut = keep_spec
        keep = (lambda r: not (r[v] > cut)) if side == "alto" else (lambda r: not (r[v] <= cut))
    T = trades_D(b, f, X, keep, mem, sym)
    return T.assign(sym=sym) if len(T) else T


def run(syms, mem, keep_spec=None):
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem, keep_spec) for s in syms]))
    res = [r for r in res if len(r)]
    return pd.concat(res, ignore_index=True) if res else pd.DataFrame()


def per(T):
    return T[T.t < EXA0], T[T.t >= EXA0]


if __name__ == "__main__":
    D2 = ["BTCUSDT", "ETHUSDT"]
    T = run(D2, None)
    if sys.argv[1] == "buscar":
        print(f"Búsqueda (D en BTC y ETH): {len(T)} operaciones, acierto {100 * (T.R > 0).mean():.0f} %, media {T.R.mean():+.3f}R\n")
        for v, desc in VARS.items():
            X = T.dropna(subset=[v]); q = X[v].quantile([1 / 3, 2 / 3]).to_numpy()
            line = f"  {desc:44s}"
            for g, Y in (("bajo", X[X[v] <= q[0]]), ("medio", X[(X[v] > q[0]) & (X[v] <= q[1])]), ("alto", X[X[v] > q[1]])):
                line += f" | {g}: n {len(Y)}, acierto {100 * (Y.R > 0).mean():3.0f} %, media {Y.R.mean():+.3f}R"
            print(line + f" | cortes {q[0]:.4g} / {q[1]:.4g}", flush=True)
    else:
        v, side = sys.argv[2], sys.argv[3]
        q = T[v].quantile([1 / 3, 2 / 3]).to_numpy(); cut = q[1] if side == "alto" else q[0]
        print(f"Filtro: quitar el tercil {side} de '{VARS[v]}' (corte fijo: {cut:.4g})")
        print("\n(2) D real (BTC + ETH):")
        for name, spec in (("D actual", None), ("D con filtro", (v, side, cut))):
            X = run(D2, None, spec)
            cv = (curve(X[X.sym == "BTCUSDT"]) + curve(X[X.sym == "ETHUSDT"])) / 2
            line = f"  {name:13s}"
            for lab, a_, b_ in (("desarrollo", "2020-03-01", "2023-06-30"), ("examen", "2023-07-01", "2026-10-31")):
                x = X[(X.t >= a_) & (X.t <= b_)]
                line += f" | {lab}: {fmt(st(cv.loc[a_:b_]))} | n {len(x)}"
            print(line, flush=True)
        vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
        mem = universe.monthly_members(vol, 30)
        others = sorted(set().union(*mem.values()) - set(D2))
        print("\n(1) Validación: misma regla en las demás monedas del top 30:")
        for name, spec in (("sin filtro", None), ("con filtro", (v, side, cut))):
            V = run(others, mem, spec); dev, exa = per(V)
            print(f"  {name:13s} | desarrollo: n {len(dev)}, {dev.R.mean():+.3f}R | examen: n {len(exa)}, {exa.R.mean():+.3f}R", flush=True)
