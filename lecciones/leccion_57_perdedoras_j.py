"""Lección 57 — Rasgos de las operaciones perdedoras del bloque J (docs/leccion_57.md).
Uso: python3 lecciones/leccion_57_perdedoras_j.py buscar
     python3 lecciones/leccion_57_perdedoras_j.py validar <variable> <bajo|alto>"""
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones")); sys.path.insert(0, str(ROOT / "sclab"))
from sclab import data, lab15, universe  # noqa: E402
from leccion_46_redondos import COST, signals  # noqa: E402
from rangos import monthly_rank_members  # noqa: E402

VARS = {"ruptura_pct": "tamaño de la ruptura (% más allá del nivel)", "ruptura_atr": "tamaño de la ruptura (en ATR)",
        "vol_pct": "volatilidad (ATR / precio)", "volumen": "volumen del día de ruptura / media 20 días",
        "tendencia": "cierre vs media 50 días, a favor de la ruptura", "ret30": "rentabilidad 30 días, a favor de la ruptura",
        "btc7": "BTC 7 días, a favor de la ruptura", "edad": "antigüedad de la moneda (días)",
        "funding": "funding 3 días, a favor de la ruptura", "alcista": "ruptura alcista (1) o bajista (0)"}


def job(args):
    sym, mem, extra = args
    try:
        h = data.load(sym, "1h")
    except Exception:
        return []
    d = h.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last", "quote_volume": "sum"}).dropna()
    if len(d) < 60:
        return []
    btc = data.load("BTCUSDT", "1h")["close"].resample("1D").last()
    b7 = (btc / btc.shift(7) - 1).reindex(d.index)
    o, hi, lo, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    prev = np.r_[c[0], c[:-1]]
    atr = pd.Series(np.maximum(hi - lo, np.maximum(np.abs(hi - prev), np.abs(lo - prev)))).rolling(14).mean().to_numpy()
    sma50 = d.close.rolling(50).mean().to_numpy(); ret30 = (d.close / d.close.shift(30) - 1).to_numpy()
    vrel = (d.quote_volume / d.quote_volume.shift(1).rolling(20).mean()).to_numpy()
    fund = lab15._funding(sym)
    f3 = fund.rolling("72h").sum().div(9) if len(fund) else None
    t, first = d.index, d.index[0]
    rows = []
    for brk in (-1, 1):
        busy = -1
        for i, L, step in signals(d, brk, 0.0):
            if i <= busy or i + 1 >= len(d) or not (atr[i] > 0):
                continue
            if not universe.is_member(mem, sym, pd.DatetimeIndex([t[i] + pd.Timedelta("1D")]))[0]:
                continue
            fd = -brk; j = i + 1; e = o[j]; stop = e - fd * 2 * atr[i]
            x, k = None, j
            for k in range(j, min(j + 20, len(d))):
                if fd > 0 and lo[k] <= stop:
                    x = min(o[k], stop); break
                if fd < 0 and hi[k] >= stop:
                    x = max(o[k], stop); break
                if (fd > 0 and c[k] > L) or (fd < 0 and c[k] < L):
                    x = c[k]; break
            if x is None:
                x = c[k]
            f = float(fund[(fund.index > t[j]) & (fund.index <= t[k] + pd.Timedelta("1D"))].sum()) if len(fund) else 0.0
            r = fd * (x / e - 1) - 2 * COST - fd * f - extra
            fv = f3.asof(t[i] + pd.Timedelta("1D")) if f3 is not None and len(f3) else np.nan
            rows.append({"t": t[j], "r": r, "ruptura_pct": abs(c[i] / L - 1), "ruptura_atr": abs(c[i] - L) / atr[i],
                         "vol_pct": atr[i] / c[i], "volumen": vrel[i], "tendencia": brk * (c[i] / sma50[i] - 1),
                         "ret30": brk * ret30[i], "btc7": brk * b7.iloc[i], "edad": (t[i] - first).days,
                         "funding": brk * fv if fv == fv else np.nan, "alcista": 1.0 if brk > 0 else 0.0})
            busy = k
    return rows


def collect(mem, extra=0.0):
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem, extra) for s in syms]))
    return pd.DataFrame([r for rr in res for r in rr])


def per(T):
    dev = T[T.t < pd.Timestamp("2023-01-01", tz="UTC")]; exa = T[T.t >= pd.Timestamp("2023-01-01", tz="UTC")]
    return dev, exa


if __name__ == "__main__":
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    if sys.argv[1] == "buscar":
        T = collect(universe.monthly_members(vol, 30))
        print(f"Búsqueda en el top 30: {len(T)} operaciones, acierto {100 * (T.r > 0).mean():.0f} %, media {100 * T.r.mean():+.2f} %\n")
        for v, desc in VARS.items():
            X = T.dropna(subset=[v])
            if v == "alcista":
                groups = [("bajista", X[X[v] == 0]), ("alcista", X[X[v] == 1])]
            else:
                q = X[v].quantile([1 / 3, 2 / 3]).to_numpy()
                groups = [("bajo", X[X[v] <= q[0]]), ("medio", X[(X[v] > q[0]) & (X[v] <= q[1])]), ("alto", X[X[v] > q[1]])]
            line = f"  {desc:48s}"
            for g, Y in groups:
                line += f" | {g}: acierto {100 * (Y.r > 0).mean():3.0f} %, media {100 * Y.r.mean():+.2f} %, pierde {100 * Y[Y.r <= 0].r.mean():+.1f} %"
            print(line, flush=True)
    else:
        v, side = sys.argv[2], sys.argv[3]
        for lab, mem, extra in (("top 30 (donde se buscó)", universe.monthly_members(vol, 30), 0.0),
                                ("puestos 31–100 (validación)", monthly_rank_members(vol, 30, 100), 2 * 0.0003)):
            T = collect(mem, extra)
            q = T[v].quantile([1 / 3, 2 / 3]).to_numpy()
            keep = T[~(T[v] > q[1])] if side == "alto" else T[~(T[v] <= q[0])]
            keep = pd.concat([keep, T[T[v].isna()]]) if v == "funding" else keep
            print(f"\n{lab} — filtro: quitar el tercil {side} de '{VARS[v]}' (corte {q[1] if side == 'alto' else q[0]:.4g})")
            for name, X in (("J sin filtro", T), ("J con filtro", keep)):
                dev, exa = per(X)
                print(f"  {name:14s} | desarrollo: n {len(dev)}, media {100 * dev.r.mean():+.3f} %, acierto {100 * (dev.r > 0).mean():.0f} % "
                      f"| examen: n {len(exa)}, media {100 * exa.r.mean():+.3f} %, acierto {100 * (exa.r > 0).mean():.0f} %", flush=True)
