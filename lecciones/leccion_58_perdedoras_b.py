"""Lección 58 — Rasgos de las operaciones perdedoras del bloque B (docs/leccion_58.md).
Uso: python3 lecciones/leccion_58_perdedoras_b.py buscar
     python3 lecciones/leccion_58_perdedoras_b.py validar <variable> <bajo|alto>"""
import json
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
from leccion_22_validacion import st  # noqa: E402
from leccion_44_bloque_b import BAR, COST, frame  # noqa: E402
from rangos import monthly_rank_members  # noqa: E402

VARS = {"prof": "profundidad de la ruptura (ATR bajo el mínimo de 120)", "vol_alt": "volatilidad de la altcoin (ATR diario / precio)",
        "f3": "funding 3 días de la altcoin", "caida30": "caída del ratio en 30 días", "dist50": "distancia bajo la media 50 del ratio",
        "btc7": "BTC 7 días", "volumen": "volumen del día / media 20 días", "edad": "antigüedad de la moneda (días)"}


def trades(df, fund, feats, extra=0.0, m=5.0):
    """B actual (stop 5 ATR que se aprieta a 2,5 ATR tras +2R) con las variables de entrada."""
    o, h, l, c, a = (df[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    t, tns = df.index, df.index.as_unit("ns").asi8
    f_t = fund.index.as_unit("ns").asi8; f_cum = np.concatenate([[0.0], np.cumsum(fund.to_numpy())])
    n, rows, d = len(df), [], -1
    for i in np.flatnonzero(df["sig"].to_numpy()):
        if i + 1 >= n or not (a[i] > 0):
            continue
        j = i + 1; entry = o[j]; R = m * a[i]; stop = entry + R; ext = entry; mult = m
        exit_px, k = None, j
        for k in range(j, n):
            if k > j and o[k] >= stop:
                exit_px = o[k]; break
            if h[k] >= stop:
                exit_px = stop; break
            ext = min(ext, l[k])
            if entry - ext >= 2 * R:
                mult = 2.5
            stop = min(stop, ext + mult * a[k])
        if exit_px is None:
            exit_px, k = c[n - 1], n - 1
        fa_ = np.searchsorted(f_t, tns[j], side="right"); fb_ = np.searchsorted(f_t, tns[k] + BAR.value, side="right")
        fsum = f_cum[fb_] - f_cum[fa_]
        r = (d * (exit_px - entry) - (entry + exit_px) * (COST + extra) - d * fsum * entry) / R
        row = {"entry_time": t[j], "exit_time": t[k] + BAR, "side": d, "entry": entry, "R": R, "r_net": r}
        row.update({v: feats[v].iloc[i] for v in VARS})
        rows.append(row)
    return pd.DataFrame(rows)


def job(args):
    sym, months, extra = args
    btc = data.load("BTCUSDT", "1h")["close"]; f_btc = lab15._funding("BTCUSDT")
    fr = frame(sym, btc, f_btc)
    if fr is None:
        return sym, None, None
    df, fund = fr
    h = data.load(sym, "1h")
    dU = h.resample("1D").agg({"high": "max", "low": "min", "close": "last", "quote_volume": "sum"}).dropna()
    prev = dU.close.shift(1)
    atrd = pd.concat([dU.high - dU.low, (dU.high - prev).abs(), (dU.low - prev).abs()], axis=1).max(axis=1).rolling(14).mean()
    t_end = df.index + BAR
    asof = lambda s: s.shift(1).reindex(t_end.floor("1D"), method="ffill").to_numpy()      # día anterior completo
    dd = df.close.resample("1D").last().dropna(); ema50 = dd.ewm(span=50, adjust=False).mean()
    bd = btc.resample("1D").last()
    feats = pd.DataFrame(index=df.index)
    feats["prof"] = ((df.low.rolling(120).min().shift(1) - df.close) / df.atr).to_numpy()
    feats["vol_alt"] = asof(atrd / dU.close)
    feats["f3"] = df["f3"].to_numpy()
    feats["caida30"] = -(df.close / df.close.shift(180) - 1).to_numpy()
    feats["dist50"] = -(asof(dd / ema50 - 1))
    feats["btc7"] = asof(bd / bd.shift(7) - 1)
    feats["volumen"] = asof(dU.quote_volume / dU.quote_volume.shift(1).rolling(20).mean())
    feats["edad"] = ((df.index - h.index[0]).days).to_numpy()
    T = trades(df, fund, feats, extra)
    if len(T):
        T = T[universe.is_member(months, sym, pd.DatetimeIndex(T.entry_time))]
        T["symbol"] = sym
    return sym, df["close"], T


def collect(mem, extra=0.0, syms=None):
    if syms is None:
        OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]; NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
        syms = sorted(set(OLD + NEW) | set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem, extra) for s in syms if s != "BTCUSDT"]))
    closes = {s: c for s, c, T in res if c is not None}
    T = pd.concat([T for _, c, T in res if T is not None and len(T)], ignore_index=True)
    return T, closes


def per(T):
    return T[T.entry_time < pd.Timestamp("2023-01-01", tz="UTC")], T[T.entry_time >= pd.Timestamp("2023-01-01", tz="UTC")]


if __name__ == "__main__":
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]; NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    s30 = sorted(set(OLD + NEW))
    mem30 = universe.monthly_members(vol[[s for s in s30 if s in vol]], 30)
    if sys.argv[1] == "buscar":
        T, _ = collect(mem30, syms=s30)
        print(f"Búsqueda en el top 30: {len(T)} operaciones candidatas, acierto {100 * (T.r_net > 0).mean():.0f} %, media {T.r_net.mean():+.3f}R\n")
        for v, desc in VARS.items():
            X = T.dropna(subset=[v])
            q = X[v].quantile([1 / 3, 2 / 3]).to_numpy()
            line = f"  {desc:52s}"
            for g, Y in (("bajo", X[X[v] <= q[0]]), ("medio", X[(X[v] > q[0]) & (X[v] <= q[1])]), ("alto", X[X[v] > q[1]])):
                line += f" | {g}: acierto {100 * (Y.r_net > 0).mean():3.0f} %, media {Y.r_net.mean():+.3f}R"
            print(line + f" | cortes {q[0]:.4g} / {q[1]:.4g}", flush=True)
    else:
        v, side = sys.argv[2], sys.argv[3]
        T, closes = collect(mem30, syms=s30)
        q = T[v].quantile([1 / 3, 2 / 3]).to_numpy(); cut = q[1] if side == "alto" else q[0]
        keep = (lambda X: X[~(X[v] > cut)]) if side == "alto" else (lambda X: X[~(X[v] <= cut)])
        print(f"Filtro: quitar el tercil {side} de '{VARS[v]}' (corte fijo del top 30: {cut:.4g})")
        fmt = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+6.1f} % | caída {100 * d['DD']:5.1f} %"
        print("\n(2) Cartera B real, top 30:")
        for name, X in (("B actual", T), ("B con filtro", keep(T))):
            daily, tk, _ = lab15._run_portfolio(X[["entry_time", "exit_time", "side", "entry", "R", "r_net", "symbol"]], closes, 0.01, 10)
            line = f"  {name:14s}"
            for lab, a_, b_ in (("2020–22", "2020-03-01", "2022-12-31"), ("2023–26", "2023-01-01", "2026-10-31")):
                line += f" | {lab}: {fmt(st(daily.loc[a_:b_]))}"
            print(line + f" | operaciones {len(tk)}", flush=True)
        V, _ = collect(monthly_rank_members(vol, 30, 100), extra=0.0003)
        print("\n(1) Validación en los puestos 31–100 (operaciones candidatas, resultado medio):")
        for name, X in (("B sin filtro", V), ("B con filtro", keep(V))):
            dev, exa = per(X)
            print(f"  {name:14s} | desarrollo: n {len(dev)}, {dev.r_net.mean():+.3f}R | examen: n {len(exa)}, {exa.r_net.mean():+.3f}R", flush=True)
