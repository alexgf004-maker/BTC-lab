"""Detector de figuras bajistas (doble techo y hombro-cabeza-hombro) en velas de 4 h — idéntico al de las Lecciones 52 y 53.

Giros: un máximo queda confirmado cuando el precio cae 3 × ATR(14) desde él (y al revés). Doble techo: M1, m2, M3 con
|M1 − M3| ≤ 0,15h; ruptura = cierre bajo m2. HCH: M1, m2, M3, m4, M5 con M3 por encima de los hombros, hombros y valles parecidos
(≤ 0,25h); ruptura = cierre bajo la línea de cuello. La ruptura cuenta si llega en las 30 velas siguientes al último giro.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

W4 = pd.Timedelta("4h")


def zigzag(df, k=3.0):
    h, l, c = df.high.to_numpy(float), df.low.to_numpy(float), df.close.to_numpy(float)
    prev = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    atr = pd.Series(tr).rolling(14).mean().to_numpy()
    piv, mode = [], 0
    hi, hi_i, lo, lo_i = h[0], 0, l[0], 0
    for i in range(1, len(df)):
        a = atr[i]
        if not a > 0:
            continue
        if mode >= 0:
            if h[i] > hi:
                hi, hi_i = h[i], i
            if l[i] < hi - k * a:
                piv.append(("H", hi, hi_i, i)); mode = -1; lo, lo_i = l[i], i
                continue
        if mode <= 0:
            if l[i] < lo:
                lo, lo_i = l[i], i
            if h[i] > lo + k * a:
                piv.append(("L", lo, lo_i, i)); mode = 1; hi, hi_i = h[i], i
    return piv


def _bear_setups(P):
    out = []
    t = "".join(p[0] for p in P[-5:]); v = [p[1] for p in P]; x = [p[2] for p in P]
    if len(P) >= 5 and t == "HLHLH":
        E1, E2, E3, E4, E5 = v[-5:]
        hgt = E3 - (E2 + E4) / 2
        if hgt > 0 and E3 > E1 and E3 > E5 and abs(E1 - E5) <= 0.25 * hgt and abs(E2 - E4) <= 0.25 * hgt:
            x2, x4 = x[-4], x[-2]
            s = (E4 - E2) / max(x4 - x2, 1)
            out.append(lambda i, c, E2=E2, x2=x2, s=s: c < E2 + s * (i - x2))
    if len(P) >= 3 and "".join(p[0] for p in P[-3:]) == "HLH":
        E1, E2, E3 = v[-3:]
        hgt = abs((E1 + E3) / 2 - E2)
        if hgt > 0 and abs(E1 - E3) <= 0.15 * hgt:
            out.append(lambda i, c, L=E2: c < L)
    return out


def bear_breaks(df4h: pd.DataFrame) -> pd.DatetimeIndex:
    """Momentos (cierre de la vela de 4 h) en que se rompe un doble techo o un HCH."""
    c = df4h.close.to_numpy(float); idx = df4h.index
    by_conf = {}
    for p in zigzag(df4h):
        by_conf.setdefault(p[3], []).append(p)
    confirmed, pending, out = [], [], []
    for i in range(len(df4h)):
        for p in by_conf.get(i, []):
            confirmed.append(p)
            pending = [(s, i) for s in _bear_setups(confirmed)]
        keep = []
        for s, born in pending:
            if i <= born:
                keep.append((s, born)); continue
            if i - born > 30:
                continue
            if s(i, c[i]):
                out.append(idx[i] + W4)
            else:
                keep.append((s, born))
        pending = keep
    return pd.DatetimeIndex(sorted(set(out)))


def recent_bear(df1h: pd.DataFrame, now, bars=30) -> bool:
    """¿Se rompió una figura bajista en las últimas `bars` velas de 4 h (con datos cerrados hasta `now`)?"""
    d4 = df1h[["open", "high", "low", "close"]].resample("4h").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    d4 = d4[d4.index + W4 <= now]
    b = bear_breaks(d4)
    return bool(len(b) and ((b > now - bars * W4) & (b <= now)).any())


def double_top_at_last(df4h: pd.DataFrame, k=3.0):
    """Si la última vela cerrada de 4 h rompe un doble techo, devuelve (stop, objetivo, altura); si no, None.
    Mismas reglas que la L52 (corto al cerrar bajo el valle; stop en el techo más alto; objetivo = entrada − altura)."""
    c = df4h.close.to_numpy(float)
    by_conf = {}
    for p in zigzag(df4h, k):
        by_conf.setdefault(p[3], []).append(p)
    confirmed, pending, last = [], [], len(df4h) - 1
    for i in range(len(df4h)):
        for p in by_conf.get(i, []):
            confirmed.append(p)
            pending = []
            if len(confirmed) >= 3 and "".join(q[0] for q in confirmed[-3:]) == "HLH":
                E1, E2, E3 = (q[1] for q in confirmed[-3:])
                hgt = (E1 + E3) / 2 - E2
                if hgt > 0 and abs(E1 - E3) <= 0.15 * hgt:
                    pending = [(E2, max(E1, E3), hgt, i)]
        keep = []
        for L, stop, hgt, born in pending:
            if i <= born:
                keep.append((L, stop, hgt, born)); continue
            if i - born > 30:
                continue
            if c[i] < L:
                if i == last:
                    return stop, c[i] - hgt, hgt
            else:
                keep.append((L, stop, hgt, born))
        pending = keep
    return None
