"""Simulador de creador de mercado con cola conservadora (Lección 29). Ver docs/leccion_29.md."""
from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import numba as nb
import numpy as np
import pandas as pd

TMP = Path("/tmp/claude-0/-home-user/e9703610-5c49-51c1-9f3f-bbe7221b21cd/scratchpad/ticks")
B = "https://data.binance.vision/data/futures/um/daily"


def fetch(kind, sym, day):
    TMP.mkdir(parents=True, exist_ok=True)
    f = TMP / f"{sym}-{kind}-{day}.zip"
    if not f.exists():
        urllib.request.urlretrieve(f"{B}/{kind}/{sym}/{sym}-{kind}-{day}.zip", f)
    with zipfile.ZipFile(f) as z:
        raw = z.read(z.namelist()[0])
    f.unlink()
    hdr = 0 if raw[:1].isalpha() else None
    return pd.read_csv(io.BytesIO(raw), header=hdr)


def load_day(sym, day):
    bt = fetch("bookTicker", sym, day)
    bt.columns = ["uid", "bid", "bidq", "ask", "askq", "tt", "et"][: bt.shape[1]]
    ag = fetch("aggTrades", sym, day)
    ag.columns = ["id", "p", "q", "f", "l", "t", "bm"][: ag.shape[1]]
    bm = ag["bm"].astype(str).str.lower().eq("true").to_numpy()
    return (bt["tt"].to_numpy(np.int64), bt["bid"].to_numpy(float), bt["bidq"].to_numpy(float), bt["ask"].to_numpy(float),
            bt["askq"].to_numpy(float), ag["t"].to_numpy(np.int64), ag["p"].to_numpy(float), ag["q"].to_numpy(float), bm)


@nb.njit(cache=True)
def simulate(bt_t, bid, bidq, ask, askq, tr_t, tr_p, tr_q, tr_bm, usd, max_inv_quotes, lat_ms, imb_lo=-1.0, imb_hi=2.0):
    # órdenes: [0]=bid, [1]=ask ; cada una: precio, cola delante, tamaño restante, hora de activación, viva(0/1)
    # pendientes de cancelar: precio/cola/tamaño de la orden vieja hasta hora_fin
    price = np.full(2, np.nan); queue = np.zeros(2); size = np.zeros(2); act = np.zeros(2, np.int64); live = np.zeros(2, np.int64)
    oprice = np.full(2, np.nan); oqueue = np.zeros(2); osize = np.zeros(2); oend = np.zeros(2, np.int64)
    inv = 0.0; cash = 0.0
    fills_t = np.zeros(2_000_000, np.int64); fills_p = np.zeros(2_000_000); fills_s = np.zeros(2_000_000); fills_q = np.zeros(2_000_000)
    nf = 0
    i = 0; j = 0; nb_ = len(bt_t); nt = len(tr_t)
    cb, cbq, ca, caq = np.nan, 0.0, np.nan, 0.0
    while i < nb_ or j < nt:
        if j < nt and (i >= nb_ or tr_t[j] <= bt_t[i]):
            t = tr_t[j]; p = tr_p[j]; q = tr_q[j]
            side = 0 if tr_bm[j] else 1          # vendedor agresor golpea compras (0); comprador agresor levanta ventas (1)
            # activar órdenes cuya latencia ha pasado
            for k in range(2):
                if live[k] == 2 and t >= act[k]:
                    live[k] = 1
            for which in range(2):               # 0 = orden actual, 1 = orden vieja pendiente de cancelar
                if which == 0:
                    if live[side] != 1:
                        continue
                    op, oq, os = price[side], queue[side], size[side]
                else:
                    if not (t < oend[side]) or osize[side] <= 0:
                        continue
                    op, oq, os = oprice[side], oqueue[side], osize[side]
                filled = 0.0
                through = (p < op) if side == 0 else (p > op)
                if through:
                    filled = os
                elif p == op:
                    if q > oq:
                        filled = min(os, q - oq); oq = 0.0
                    else:
                        oq -= q
                if filled > 0:
                    sgn = 1.0 if side == 0 else -1.0
                    inv += sgn * filled; cash -= sgn * filled * op
                    if nf < len(fills_t):
                        fills_t[nf] = t; fills_p[nf] = op; fills_s[nf] = sgn; fills_q[nf] = filled; nf += 1
                    os -= filled
                if which == 0:
                    queue[side] = oq; size[side] = os
                    if os <= 1e-12:
                        live[side] = 0; price[side] = np.nan
                else:
                    oqueue[side] = oq; osize[side] = os
            j += 1
        else:
            t = bt_t[i]; cb, cbq, ca, caq = bid[i], bidq[i], ask[i], askq[i]
            mid = 0.5 * (cb + ca)
            qty = usd / mid
            maxinv = max_inv_quotes * qty
            for k in range(2):
                if live[k] == 2 and t >= act[k]:
                    live[k] = 1
                want = cb if k == 0 else ca
                imb = cbq / (cbq + caq) if (cbq + caq) > 0 else 0.5
                allowed = (inv < maxinv - 1e-12 and imb >= imb_lo) if k == 0 else (inv > -maxinv + 1e-12 and imb <= imb_hi)
                if not allowed:
                    want = np.nan
                cur = price[k]
                same = (cur == want)
                if same and live[k] != 0:
                    continue
                # cancelar la actual (sigue viva lat_ms) y poner la nueva (activa tras lat_ms, al final de la cola)
                if live[k] != 0 and size[k] > 0:
                    oprice[k] = cur; oqueue[k] = queue[k]; osize[k] = size[k]; oend[k] = t + lat_ms
                if want == want:
                    price[k] = want; queue[k] = cbq if k == 0 else caq; size[k] = qty; act[k] = t + lat_ms; live[k] = 2
                else:
                    price[k] = np.nan; live[k] = 0; size[k] = 0.0
            i += 1
    return inv, cash, cb, ca, fills_t[:nf], fills_p[:nf], fills_s[:nf], fills_q[:nf]


def run_day(sym, day, usd=200.0, max_inv=3, lat=200, imb_lo=-1.0, imb_hi=2.0):
    bt_t, bid, bidq, ask, askq, tr_t, tr_p, tr_q, bm = load_day(sym, day)
    inv, cash, cb, ca, ft, fp, fs, fq = simulate(bt_t, bid, bidq, ask, askq, tr_t, tr_p, tr_q, bm, usd, max_inv, lat, imb_lo, imb_hi)
    mid_last = 0.5 * (cb + ca)
    notional = np.sum(fp * fq)
    close_cost = abs(inv) * (0.5 * (ca - cb) + 0.0005 * mid_last)
    gross = cash + inv * mid_last - close_cost                       # sin comisión maker
    # markouts
    mids = 0.5 * (bid + ask)
    mk = {}
    for h in (1000, 10000, 60000):
        idx = np.searchsorted(bt_t, ft + h, side="right") - 1
        idx = np.clip(idx, 0, len(mids) - 1)
        mk[h] = float(np.sum(fs * (mids[idx] - fp) * fq) / notional) if notional > 0 else np.nan
    i0 = np.clip(np.searchsorted(bt_t, ft, side="right") - 1, 0, len(mids) - 1)
    half_spread = float(np.sum(fs * (mids[i0] - fp) * fq) / notional) if notional > 0 else np.nan
    spread_bps = float(np.median((ask - bid) / mids) * 1e4)
    return dict(sym=sym, day=day, fills=len(ft), notional=notional, gross=gross, net_002=gross - 0.0002 * notional,
                spread_bps=spread_bps, half_spread_bps=1e4 * half_spread, mk1_bps=1e4 * mk[1000], mk10_bps=1e4 * mk[10000],
                mk60_bps=1e4 * mk[60000], inv_end=inv * mid_last)
