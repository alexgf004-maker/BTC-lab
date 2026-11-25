"""Lección 49 — Segunda tanda de Gemini: Q5 y Q6 (sobre el bloque B), HL (Hyperliquid) y RF (resaca tras funding extremo).
Reglas en docs/leccion_49.md. Uso: python3 lecciones/leccion_49_gemini2.py [B|HL|RF]..."""
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
from sclab import data, lab15, universe  # noqa: E402
from leccion_22_validacion import st  # noqa: E402
from leccion_44_bloque_b import BAR, COST, frame  # noqa: E402

UTC = lambda s: pd.Timestamp(s, tz="UTC")
H1 = pd.Timedelta("1h")


# ------------------------------------------------------------------------------------------------ Q5 / Q6 sobre B
def oi_pct(sym, idx):
    """Percentil de interés abierto / volumen 24 h frente a los 90 días previos, al cierre de cada vela de 4 h (NaN sin datos)."""
    f = ROOT / "data" / "metrics" / f"{sym}.parquet"
    if not f.exists():
        return pd.Series(np.nan, index=idx)
    oi = pd.read_parquet(f, columns=["sum_open_interest_value"])["sum_open_interest_value"]
    qv = data.load(sym, "1h")["quote_volume"]
    qv24 = qv.rolling(24, min_periods=20).sum(); qv24.index = qv24.index + H1          # conocido al cerrar la vela
    oi_k = oi.copy(); oi_k.index = oi_k.index + H1                                       # margen de una hora
    R = (oi_k / qv24.reindex(oi_k.index)).dropna()
    R4 = R.resample("4h", label="right", closed="right").last().dropna()
    pct = R4.rolling(541, min_periods=180).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    return pct.reindex(idx + BAR)                                                        # valor al cierre de la vela de entrada


def trades_b(df, fund, fa, sym, bleed=False, oi=False, m=5.0):
    o, h, l, c, a = (df[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    t, tns = df.index, df.index.as_unit("ns").asi8
    f_t = fund.index.as_unit("ns").asi8; f_cum = np.concatenate([[0.0], np.cumsum(fund.to_numpy())])
    fa_t = fa.index.as_unit("ns").asi8 if len(fa) else np.array([], dtype="int64"); fa_v = fa.to_numpy() if len(fa) else np.array([])
    pct = oi_pct(sym, df.index) if oi else None
    n, rows, d = len(df), [], -1
    for i in np.flatnonzero(df["sig"].to_numpy()):
        if i + 1 >= n or not (a[i] > 0):
            continue
        size = 1.0
        if oi:
            p = pct.iloc[i]
            if p == p:
                size = 0.0 if p > 0.90 else (0.5 if p >= 0.75 else 1.0)
            if size == 0:
                continue
        j = i + 1; entry = o[j]; R = m * a[i]; stop = entry + R; ext = entry
        fa_ = np.searchsorted(f_t, tns[j], side="right")
        exit_px, k = None, j
        for k in range(j, n):
            if k > j and o[k] >= stop:
                exit_px = o[k]; break
            if h[k] >= stop:
                exit_px = stop; break
            if bleed:
                end = tns[k] + BAR.value
                paid = -(f_cum[np.searchsorted(f_t, end, side="right")] - f_cum[fa_])      # corto en el par: cobra fund; paga si < 0
                gain = (entry - c[k]) / entry
                q = np.searchsorted(fa_t, end, side="right") - 1
                last = fa_v[q] if q >= 0 and fa_t[q] > tns[j] else 0.0
                if (paid >= 0.006 and gain < 0.025) or last < -0.0008:
                    exit_px = c[k]; break
            ext = min(ext, l[k])
            stop = min(stop, ext + m * a[k])
        if exit_px is None:
            exit_px, k = c[n - 1], n - 1
        fb_ = np.searchsorted(f_t, tns[k] + BAR.value, side="right")
        fsum = f_cum[fb_] - f_cum[fa_]
        r = (d * (exit_px - entry) - (entry + exit_px) * COST - d * fsum * entry) / R
        rows.append((t[j], t[k] + BAR, d, entry, R, size * r))
    return pd.DataFrame(rows, columns=["entry_time", "exit_time", "side", "entry", "R", "r_net"])


VB = {"B actual": {}, "Q5 stop por sangrado de funding": {"bleed": True}, "Q6 tamaño por interés abierto/volumen": {"oi": True}}


def job_b(args):
    sym, months = args
    btc = data.load("BTCUSDT", "1h")["close"]; f_btc = lab15._funding("BTCUSDT")
    fr = frame(sym, btc, f_btc)
    if fr is None:
        return sym, None, {}
    df, fund = fr
    fa = lab15._funding(sym)
    out = {}
    for name, kw in VB.items():
        T = trades_b(df, fund, fa, sym, **kw)
        if len(T):
            T = T[universe.is_member(months, sym, pd.DatetimeIndex(T.entry_time))]
            T["symbol"] = sym
        out[name] = T
    return sym, df["close"], out


def run_B():
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    syms = sorted(set(OLD + NEW))
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    mem = universe.monthly_members(vol[[s for s in syms if s in vol]], 30)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_b, [(s, mem) for s in syms if s != "BTCUSDT"]))
    closes = {s: c for s, c, _ in res if c is not None}
    fmt = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+6.1f} % | caída {100 * d['DD']:5.1f} %"
    print("\n=== Q5 / Q6 sobre el bloque B (riesgo 1 %, máximo 10 posiciones, top 30)")
    for name in VB:
        cands = pd.concat([o[name] for _, c, o in res if c is not None and name in o and len(o[name])], ignore_index=True)
        daily, tk, _ = lab15._run_portfolio(cands, closes, 0.01, 10)
        line = f"  {name:40s}"
        for lab, a_, b_ in (("2020–22", "2020-03-01", "2022-12-31"), ("2023–26", "2023-01-01", "2026-10-31")):
            line += f" | {lab}: {fmt(st(daily.loc[a_:b_]))}"
        print(line + f" | operaciones {len(tk)} | E {tk.ret.mean():+.3f}R", flush=True)


# ------------------------------------------------------------------------------------------------ utilidades de eventos
def tcl(r, t):
    if len(r) < 3:
        return float("nan")
    u = r - r.mean()
    g = u.groupby(pd.DatetimeIndex(t).tz_localize(None).to_period("W").values).sum()
    se = np.sqrt((g ** 2).sum()) / len(r)
    return r.mean() / se if se > 0 else float("nan")


def report(name, T, periods):
    line = f"  {name:40s}"
    for lab, (a, b) in periods:
        X = T[(T.t >= UTC(a)) & (T.t < UTC(b))]
        line += f" | {lab}: n {len(X):4d}, media {100 * X.r.mean():+.3f} %, t {tcl(X.r, X.t):+.2f}"
    print(line + f" | total t {tcl(T.r, T.t):+.2f}", flush=True)


def members():
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    return universe.monthly_members(vol, 30)


def fsum(f, a, b):
    return float(f[(f.index > a) & (f.index <= b)].sum()) if len(f) else 0.0


def simulate(h, f, j, side, stop_px, hard_exit_k, extra_exit=None):
    """Recorre velas de 1 h desde j+1. Devuelve (k, precio de salida). Stop conservador dentro de la vela."""
    o, hi, lo, c = (h[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(h)
    for k in range(j + 1, min(hard_exit_k + 1, n)):
        if side > 0 and (o[k] <= stop_px or lo[k] <= stop_px):
            return k, min(o[k], stop_px)
        if side < 0 and (o[k] >= stop_px or hi[k] >= stop_px):
            return k, max(o[k], stop_px)
        if extra_exit is not None:
            px = extra_exit(k)
            if px is not None:
                return k, px
    k = min(hard_exit_k, n - 1)
    return k, c[k]


# ------------------------------------------------------------------------------------------------ HL
def binance_8h(fb: pd.Series, idx):
    """Último funding liquidado de Binance normalizado a 8 h (según el intervalo entre los dos últimos pagos)."""
    if not len(fb):
        return pd.Series(np.nan, index=idx)
    gap = fb.index.to_series().diff().dt.total_seconds().div(3600).fillna(8).clip(1, 8)
    f8 = fb * 8 / gap
    return f8.reindex(idx.union(f8.index)).ffill().reindex(idx)


def job_hl(args):
    sym, mem = args
    coin = sym[:-4]
    fh = ROOT / "data" / "hl" / f"{coin}-funding.parquet"
    if not fh.exists():
        return {}
    hl = pd.read_parquet(fh)["rate"] * 8
    h = data.load(sym, "1h")
    h = h[h.index >= UTC("2023-07-01")]
    if len(h) < 500:
        return {}
    idx = h.index + H1                                                  # cierre de cada vela (momento de decisión)
    fb = lab15._funding(sym)
    b8 = binance_8h(fb, idx).to_numpy()
    hlv = hl.reindex(idx.union(hl.index)).ffill().reindex(idx).to_numpy()
    tr = np.maximum(h.high - h.low, np.maximum((h.high - h.close.shift()).abs(), (h.low - h.close.shift()).abs()))
    atr = tr.rolling(24).mean().to_numpy()
    c = h.close.to_numpy()
    r6 = (h.close / h.close.shift(6) - 1).to_numpy()
    inmem = universe.is_member(mem, sym, idx)
    out = {}
    for key, dF in (("señal (Hyperliquid − Binance)", hlv - b8), ("placebo (solo Binance)", -b8)):
        rows, i, n = [], 3, len(h)
        while i < n - 1:
            w = dF[i - 2:i + 1]
            side = 0
            if inmem[i] and np.all(w >= 0.0004) and r6[i] < 0.04:
                side = 1
            elif inmem[i] and np.all(w <= -0.0004) and r6[i] > -0.04:
                side = -1
            if not side or not (atr[i] > 0):
                i += 1; continue
            e = c[i]
            dist = min(2.5 * atr[i], 0.05 * e)
            stop = e - side * dist
            k, x = simulate(h, None, i, side, stop, i + 24, lambda k: c[k] if abs(dF[k]) <= 0.0001 else None)
            r = side * (x / e - 1) - 2 * 0.0007 - side * fsum(fb, idx[i], idx[k])
            rows.append((idx[i], r))
            i = k + 1
        out[key] = rows
    return out


def run_HL():
    mem = members()
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_hl, [(s, mem) for s in syms]))
    print("\n=== HL — Funding de Hyperliquid frente a Binance (señal direccional en Binance)")
    for key in ("señal (Hyperliquid − Binance)", "placebo (solo Binance)"):
        T = pd.DataFrame([x for r in res for x in r.get(key, [])], columns=["t", "r"])
        report(key, T, (("desarrollo", ("2023-07-01", "2025-01-01")), ("examen", ("2025-01-01", "2026-11-01"))))


# ------------------------------------------------------------------------------------------------ RF
def job_rf(args):
    sym, mem = args
    fm = ROOT / "data" / "metrics" / f"{sym}.parquet"
    if not fm.exists():
        return {}
    oi = pd.read_parquet(fm, columns=["sum_open_interest"])["sum_open_interest"]
    h = data.load(sym, "1h")
    fb = lab15._funding(sym)
    if not len(fb):
        return {}
    pos = {t: i for i, t in enumerate(h.index)}
    out = {"señal (con caída del interés abierto)": [], "placebo (sin filtro de interés abierto)": []}
    o, hi, lo, c = (h[x].to_numpy() for x in ("open", "high", "low", "close"))
    for T, f in fb.items():
        T = T.floor("1h")
        if T.hour not in (0, 8, 16) or abs(f) < 0.0006 or T not in pos:
            continue
        i = pos[T]                                                       # vela T → T+1 h (la hora del cobro)
        if i + 1 >= len(h) or not universe.is_member(mem, sym, pd.DatetimeIndex([T]))[0]:
            continue
        side = -1 if f <= -0.0006 else 1
        candle_ok = (c[i] < o[i]) if side < 0 else (c[i] > o[i])
        if not candle_ok:
            continue
        a, b = oi.get(T), oi.get(T + H1)
        drop = (b / a - 1) <= -0.02 if (a and b and a > 0) else False
        e = c[i]
        stop = e * (1 + 0.025) if side < 0 else e * (1 - 0.025)
        opp = hi[i] if side < 0 else lo[i]                                # extremo opuesto de la vela del cobro
        ext = (lambda k: (max(o[k], opp) if hi[k] >= opp else None)) if side < 0 else (lambda k: (min(o[k], opp) if lo[k] <= opp else None))
        stop = min(stop, opp) if side < 0 else max(stop, opp)
        k, x = simulate(h, None, i, side, stop, i + 4)
        r = side * (x / e - 1) - 2 * 0.0007 - side * fsum(fb, T + H1, h.index[k] + H1)
        out["placebo (sin filtro de interés abierto)"].append((T + H1, r))
        if drop:
            out["señal (con caída del interés abierto)"].append((T + H1, r))
    return out


def run_RF():
    mem = members()
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_rf, [(s, mem) for s in syms]))
    print("\n=== RF — Resaca tras funding extremo (entrada a T+1 h)")
    for key in ("señal (con caída del interés abierto)", "placebo (sin filtro de interés abierto)"):
        T = pd.DataFrame([x for r in res for x in r.get(key, [])], columns=["t", "r"])
        report(key, T, (("desarrollo", ("2020-01-01", "2024-01-01")), ("examen", ("2024-01-01", "2026-11-01"))))


if __name__ == "__main__":
    for x in (sys.argv[1:] or ["HL", "RF", "B"]):
        {"B": run_B, "HL": run_HL, "RF": run_RF}[x]()
