"""Lección 13: W1 pescar mechas, B1 carry con trimestrales, C1 valoración en cadena. Reglas: docs/leccion_13.md"""
from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import data, portfolio, universe
from .universe import is_member

ROOT = Path(__file__).resolve().parent.parent
MAKER, TAKER_SLIP, THROUGH = 0.0002, 0.0007, 0.0001


# ------------------------------------------------------------------ W1
def w1_candidates(sym, members, k_sigma=5.0, tp_frac=0.5, hold=24):
    b = data.load(sym, "1h")
    o, h, l, c = (b[x].to_numpy() for x in ("open", "high", "low", "close"))
    r = pd.Series(c).pct_change()
    sd = r.rolling(720, min_periods=360).std().shift(1).to_numpy()      # conocida al empezar la vela
    mem = is_member(members, sym, b.index)
    t, n = b.index, len(b)
    one = pd.Timedelta("1h")
    rows = []
    for i in range(361, n - 1):
        if not mem[i] or not (sd[i] > 0):
            continue
        L = c[i - 1] * (1 - k_sigma * sd[i])
        if l[i] > L * (1 - THROUGH):
            continue
        entry = min(L, o[i])
        D = c[i - 1] - L
        stop, tp = L - D, L + tp_frac * D
        R = entry - stop
        if R <= 0:
            continue
        px, why, j = None, "time", i
        if l[i] <= stop:
            px, why = stop, "sl"
        else:
            last = min(i + hold, n - 1)
            for j in range(i + 1, last + 1):
                if o[j] <= stop:
                    px, why = o[j], "sl"; break
                if l[j] <= stop:
                    px, why = stop, "sl"; break
                if h[j] >= tp * (1 + THROUGH):
                    px, why = max(tp, o[j]), "tp"; break
            if px is None:
                px, j = c[last], last
        fee = entry * MAKER + px * (MAKER if why == "tp" else TAKER_SLIP)
        rows.append((sym, t[i], t[j] + one, 1, entry, px, R, (px - entry - fee) / R, why, D / c[i - 1]))
    return pd.DataFrame(rows, columns=["symbol", "entry_time", "exit_time", "side", "entry", "exit", "R", "r_net", "reason", "dist"])


def w1(symbols, K=20, risk=0.005, max_pos=10):
    members = universe.monthly_members(universe.daily_volume(symbols), K)
    cands = pd.concat([w1_candidates(s, members) for s in symbols], ignore_index=True)
    closes = {s: data.load(s, "1h")["close"] for s in cands.symbol.unique()}
    curve, tk, lev = portfolio.run(cands, closes, risk, K=max_pos)
    daily = curve.resample("1D").last().pct_change().dropna()
    daily = daily[daily.index >= tk.entry_time.min().floor("1D")]
    tk["entry_time"] = pd.to_datetime(tk["entry_time"], utc=True); tk["exit_time"] = pd.to_datetime(tk["exit_time"], utc=True)
    key = cands[["symbol", "entry_time", "reason", "dist"]].copy()
    key["entry_time"] = pd.to_datetime(key["entry_time"], utc=True).astype(tk["entry_time"].dtype)
    tk = tk.merge(key, on=["symbol", "entry_time"], how="left")
    tk = tk.rename(columns={"r_net": "ret"}).assign(entry=lambda x: x.entry_time)
    extra = {"candidatas": len(cands), "tomadas": len(tk), "salidas": tk.reason.value_counts(normalize=True).round(2).to_dict(),
             "distancia_media": float(tk.dist.mean()), "apal_max": float(lev.max()), "E_R": float(tk.ret.mean())}
    return daily, tk, extra


def w1_minute_audit(sym, k_sigma=5.0, tp_frac=0.5, hold_h=24):
    """W1 con ejecución minuto a minuto. Devuelve, por trade, el resultado con stop ideal (al precio del stop) y con stop
    pesimista (al mínimo del minuto en que salta). La orden se coloca cada hora igual que en la versión de 1h."""
    m = data.load(sym, "1m")
    m = m[m.index >= pd.Timestamp("2024-01-01", tz="UTC")]
    hb = m.resample("1h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    hist = data.load(sym, "1h")["close"]
    sd = hist.pct_change().rolling(720, min_periods=360).std().shift(1).reindex(hb.index).to_numpy()
    pc = hist.shift(1).reindex(hb.index).to_numpy()
    mo, mh, ml, mc = (m[x].to_numpy() for x in ("open", "high", "low", "close"))
    pos = m.index.searchsorted(hb.index)
    lo_h = hb["low"].to_numpy()
    rows, busy = [], -1
    for i in range(len(hb) - 1):
        if not (sd[i] > 0) or not np.isfinite(pc[i]) or pos[i] <= busy:
            continue
        L = pc[i] * (1 - k_sigma * sd[i])
        if lo_h[i] > L * (1 - THROUGH):
            continue
        a, b = pos[i], pos[i + 1]
        f = np.flatnonzero(ml[a:b] <= L * (1 - THROUGH))
        if not len(f):
            continue
        q = a + f[0]
        entry = min(L, mo[q]); D = pc[i] - L; stop, tp = L - D, L + tp_frac * D; R = entry - stop
        end = min(q + hold_h * 60, len(mc) - 1)
        ideal = worst = None; why = "time"
        for j in range(q, end + 1):
            if ml[j] <= stop:                                    # el stop puede saltar en el mismo minuto de la entrada
                ideal, worst, why = min(stop, mo[j]) if j > q else stop, ml[j], "sl"; break
            if j > q and mh[j] >= tp * (1 + THROUGH):
                ideal = worst = max(tp, mo[j]); why = "tp"; break
        if ideal is None:
            ideal = worst = mc[end]; j = end
        fee = lambda px: entry * MAKER + px * (MAKER if why == "tp" else TAKER_SLIP)
        rows.append((sym, m.index[q], why, D / pc[i], (ideal - entry - fee(ideal)) / R, (worst - entry - fee(worst)) / R,
                     (j - q)))
        busy = j
    return pd.DataFrame(rows, columns=["symbol", "entry", "reason", "dist", "r_ideal", "r_pesimista", "minutos"])


# ------------------------------------------------------------------ B1 carry con trimestrales
def quarterly_expiries(first="2021-03", last="2026-12"):
    out = []
    for p in pd.period_range(first, last, freq="Q"):
        end = p.end_time.normalize()
        d = end - pd.Timedelta(days=(end.weekday() - 4) % 7)          # último viernes del trimestre
        out.append(pd.Timestamp(d.date(), tz="UTC") + pd.Timedelta("8h"))
    return out


def load_quarterly(base: str, expiry: pd.Timestamp):
    """Cierres de 1h del trimestral (indexados por la hora de cierre). Descarga y guarda en caché."""
    sym = f"{base}_{expiry:%y%m%d}"
    cache = ROOT / "data" / "cache" / f"q_{sym}.parquet"
    if cache.exists():
        s = pd.read_parquet(cache)["close"]
        return s if len(s) else None
    parts = []
    for m in pd.period_range(expiry - pd.Timedelta(days=215), expiry, freq="M").strftime("%Y-%m"):
        try:
            raw = urllib.request.urlopen(f"https://data.binance.vision/data/futures/um/monthly/klines/{sym}/1h/{sym}-1h-{m}.zip", timeout=40).read()
        except Exception:
            continue
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            b = z.read(z.namelist()[0])
        d = pd.read_csv(io.BytesIO(b), header=0 if b[:1].isalpha() else None, usecols=[0, 4])
        d.columns = ["t", "close"]
        parts.append(pd.Series(d.close.astype(float).to_numpy(), index=pd.to_datetime(d.t, unit="ms", utc=True) + pd.Timedelta("1h")))
    s = pd.concat(parts).sort_index() if parts else pd.Series(dtype=float)
    s = s[~s.index.duplicated()]
    pd.DataFrame({"close": s}).to_parquet(cache)
    return s if len(s) else None


def b1_quarterly_carry(threshold=0.08, min_days=20, assets=("BTCUSDT", "ETHUSDT")):
    import sys
    sys.path.insert(0, str(ROOT / "lecciones"))
    from leccion_06_universo import spot_close
    days = pd.date_range("2021-01-01", "2026-10-31", freq="1D", tz="UTC")
    curves, trades, basis_hist = [], [], {}
    for a in assets:
        sp = spot_close(a); sp.index = sp.index + pd.Timedelta("1h")
        S = sp.reindex(days, method="ffill")
        Q = {e: q.reindex(days, method="ffill", limit=2) for e in quarterly_expiries() if (q := load_quarterly(a, e)) is not None}
        eq, pos, slot = [], None, 0.5
        cap = slot                                            # capital asignado a este activo (parte de 1,0)
        best_hist = []
        for d in days:
            ann = {e: (q[d] / S[d] - 1) * 365 / max((e - d).days, 1) for e, q in Q.items()
                   if np.isfinite(q[d]) and (e - d).days >= min_days}
            best_hist.append(max(ann.values()) if ann else np.nan)
            if pos is not None:
                e = pos["exp"]
                if d >= e.normalize():                       # vencimiento: el futuro converge al spot
                    s_exp = sp.asof(e)
                    net = pos["basis"] - 0.0033 - 0.0010 * pos["steps"]
                    cap += pos["N"] * net
                    trades.append({"activo": a, "entrada": pos["d0"], "vencimiento": e, "días": (e - pos["d0"]).days,
                                   "base_anual": pos["ann"], "base": pos["basis"], "neto_sobre_nocional": net, "reposiciones": pos["steps"]})
                    pos = None
                    eq.append(cap); continue
                fq = Q[e][d]
                mtm = pos["N"] * ((S[d] / pos["S0"] - 1) - ((fq if np.isfinite(fq) else S[d]) / pos["F0"] - 1))
                up = int(np.floor(np.log(max(S[d] / pos["S0"], 1.0)) / np.log(1.2)))
                pos["steps"] = max(pos["steps"], up)
                eq.append(cap + mtm - pos["N"] * (0.0019 + 0.0010 * pos["steps"]))
                continue
            if ann:
                e = max(ann, key=ann.get)
                if ann[e] >= threshold:
                    pos = {"exp": e, "d0": d, "S0": S[d], "F0": Q[e][d], "N": cap * 2 / 3, "basis": Q[e][d] / S[d] - 1,
                           "ann": ann[e], "steps": 0}
            eq.append(cap)
        curves.append(pd.Series(eq, index=days))
        basis_hist[a] = pd.Series(best_hist, index=days)
    curve = sum(curves)
    return curve, pd.DataFrame(trades), pd.DataFrame(basis_hist)
