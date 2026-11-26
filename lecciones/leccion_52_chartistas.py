"""Lección 52 — Patrones chartistas detectados por ordenador (docs/leccion_52.md)."""
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

FX = ["AUDUSD", "EURGBP", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]
AGG = {"open": "first", "high": "max", "low": "min", "close": "last"}
PATS = ["HCH", "HCH invertido", "doble techo", "doble suelo", "triángulo ascendente", "triángulo descendente", "triángulo simétrico"]
PLAC = {"HCH": "placebo HCH (5 giros sin forma, techo)", "HCH invertido": "placebo HCH inv. (5 giros sin forma, suelo)",
        "doble techo": "placebo doble techo (3 giros sin forma)", "doble suelo": "placebo doble suelo (3 giros sin forma)",
        "triángulo ascendente": "placebo triángulos (4 giros sin forma)", "triángulo descendente": "placebo triángulos (4 giros sin forma)",
        "triángulo simétrico": "placebo triángulos (4 giros sin forma)"}


def zigzag(df, k=3.0):
    """Giros confirmados cuando el precio se aleja k·ATR(14). Devuelve lista de (tipo, precio, índice del extremo, índice de confirmación)."""
    h, l, c = df.high.to_numpy(), df.low.to_numpy(), df.close.to_numpy()
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.r_[c[0], c[:-1]]), np.abs(l - np.r_[c[0], c[:-1]])))
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


def setups(P):
    """Figuras (y placebos) que completa el último giro de P. Cada una: (nombre, lado, función de disparo(i, close), stop, altura)."""
    out = []
    t = [p[0] for p in P]; v = [p[1] for p in P]; x = [p[2] for p in P]
    if len(P) >= 5:
        s5, a = "".join(t[-5:]), v[-5:]
        xi = x[-5:]
        for top in (True, False):
            if s5 != ("HLHLH" if top else "LHLHL"):
                continue
            E1, E2, E3, E4, E5 = a
            sgn = 1 if top else -1
            hgt = sgn * (E3 - (E2 + E4) / 2)
            if hgt <= 0:
                continue
            slope = (E4 - E2) / max(xi[3] - xi[1], 1)
            neck = lambda i, E2=E2, x2=xi[1], s=slope: E2 + s * (i - x2)
            trig = (lambda i, c, n=neck: c < n(i)) if top else (lambda i, c, n=neck: c > n(i))
            side = -1 if top else 1
            name = "HCH" if top else "HCH invertido"
            out.append((PLAC[name], side, trig, E5, hgt))
            if sgn * (E3 - E1) > 0 and sgn * (E3 - E5) > 0 and abs(E1 - E5) <= 0.25 * hgt and abs(E2 - E4) <= 0.25 * hgt:
                out.append((name, side, trig, E5, hgt))
    if len(P) >= 3:
        s3, (E1, E2, E3) = "".join(t[-3:]), v[-3:]
        if s3 in ("HLH", "LHL"):
            top = s3 == "HLH"
            hgt = abs((E1 + E3) / 2 - E2)
            if hgt > 0:
                trig = (lambda i, c, L=E2: c < L) if top else (lambda i, c, L=E2: c > L)
                side, stop = (-1, max(E1, E3)) if top else (1, min(E1, E3))
                name = "doble techo" if top else "doble suelo"
                out.append((PLAC[name], side, trig, stop, hgt))
                if abs(E1 - E3) <= 0.15 * hgt:
                    out.append((name, side, trig, stop, hgt))
    if len(P) >= 4:
        s4, a = "".join(t[-4:]), v[-4:]
        if s4 in ("HLHL", "LHLH"):
            Ma, Mb = (a[0], a[2]) if s4 == "HLHL" else (a[1], a[3])
            ma, mb = (a[1], a[3]) if s4 == "HLHL" else (a[0], a[2])
            lastH, lastL = Mb, mb
            hp = lastH - lastL
            if hp > 0:
                out.append((PLAC["triángulo simétrico"], 1, lambda i, c, L=lastH: c > L, lastL, hp))
                out.append((PLAC["triángulo simétrico"], -1, lambda i, c, L=lastL: c < L, lastH, hp))
            h_as = max(Ma, Mb) - ma
            if h_as > 0 and abs(Ma - Mb) <= 0.15 * h_as and mb > ma + 0.25 * h_as:
                out.append(("triángulo ascendente", 1, lambda i, c, L=max(Ma, Mb): c > L, mb, h_as))
            h_de = Ma - min(ma, mb)
            if h_de > 0 and abs(ma - mb) <= 0.15 * h_de and Mb < Ma - 0.25 * h_de:
                out.append(("triángulo descendente", -1, lambda i, c, L=min(ma, mb): c < L, Mb, h_de))
            h_sy = Ma - ma
            if h_sy > 0 and Mb < Ma - 0.25 * h_sy and mb > ma + 0.25 * h_sy:
                out.append(("triángulo simétrico", 1, lambda i, c, L=Mb: c > L, mb, h_sy))
                out.append(("triángulo simétrico", -1, lambda i, c, L=mb: c < L, Mb, h_sy))
    return out


def trades(df, cost, fund=None, member=None):
    """Simula todas las figuras y placebos (cada nombre lleva su propio 'una operación a la vez')."""
    o, h, l, c = (df[k].to_numpy() for k in ("open", "high", "low", "close"))
    idx = df.index
    piv = zigzag(df)
    by_conf = {}
    for p in piv:
        by_conf.setdefault(p[3], []).append(p)
    confirmed, pending, busy, rows = [], [], {}, []
    for i in range(len(df)):
        for p in by_conf.get(i, []):
            confirmed.append(p)
            pending = [(s, i) for s in setups(confirmed)]               # un giro nuevo reemplaza las figuras pendientes
        keep = []
        for s, born in pending:
            name, side, trig, stop, hgt = s
            if i <= born or i - born > 30:
                if i - born <= 30:
                    keep.append((s, born))
                continue
            if busy.get(name, -1) >= i or not trig(i, c[i]):
                keep.append((s, born)); continue
            if member is not None and not member[i]:
                continue
            e = c[i]; risk = (stop - e) * -side
            if risk <= 0:
                continue
            tgt = e + side * hgt
            x, k = None, i
            for k in range(i + 1, min(i + 61, len(df))):
                if (side < 0 and h[k] >= stop) or (side > 0 and l[k] <= stop):
                    x = (max(o[k], stop) if side < 0 else min(o[k], stop)); break
                if (side < 0 and l[k] <= tgt) or (side > 0 and h[k] >= tgt):
                    x = (min(o[k], tgt) if side < 0 else max(o[k], tgt)) if k > i else tgt; break
            if x is None:
                k = min(i + 60, len(df) - 1); x = c[k]
            f = 0.0
            if fund is not None and len(fund):
                f = float(fund[(fund.index > idx[i] + pd.Timedelta("4h")) & (fund.index <= idx[k] + pd.Timedelta("4h"))].sum())
            net = side * (x / e - 1) - 2 * cost - side * f
            rows.append((name, idx[i] + pd.Timedelta("4h"), net, net * e / risk))
            busy[name] = k
        pending = keep
    return rows


def job_crypto(args):
    sym, mem = args
    try:
        df = data.load(sym, "1h").resample("4h").agg(AGG).dropna()
    except Exception:
        return []
    member = universe.is_member(mem, sym, df.index)
    if not member.any():
        return []
    return [("cripto",) + r for r in trades(df, 0.0007, lab15._funding(sym), member)]


def job_fx(name):
    if name == "XAUUSD":
        from leccion_51_oro_liquidez import load_m1
        df = load_m1().resample("4h").agg(AGG).dropna()
    else:
        df = pd.read_parquet(ROOT / "data" / "fxd" / f"{name}.parquet").resample("4h").agg(AGG).dropna()
    return [("oro y divisas",) + r for r in trades(df, 0.0002)]


def tcl(r, t):
    if len(r) < 3:
        return float("nan")
    u = r - r.mean()
    g = u.groupby(pd.DatetimeIndex(t).tz_localize(None).to_period("W").values).sum()
    se = np.sqrt((g ** 2).sum()) / len(r)
    return r.mean() / se if se > 0 else float("nan")


if __name__ == "__main__":
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    mem = universe.monthly_members(vol, 30)
    syms = sorted(set().union(*mem.values()))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job_crypto, [(s, mem) for s in syms])) + list(ex.map(job_fx, FX + ["XAUUSD"]))
    T = pd.DataFrame([r for rr in res for r in rr], columns=["clase", "fig", "t", "net", "R"])
    dev = ((T.clase == "cripto") & (T.t < pd.Timestamp("2023-01-01", tz="UTC"))) | \
          ((T.clase != "cripto") & (T.t < pd.Timestamp("2019-01-01", tz="UTC")))
    T["periodo"] = np.where(dev, "desarrollo", "examen")
    print("Patrones chartistas, velas de 4 h (cripto top 30 2020–26; oro + 10 divisas 2012–26). Resultado neto por operación en R.")
    for name in PATS + sorted(set(PLAC.values())):
        X = T[T.fig == name]
        line = f"  {name:44s}"
        for p in ("desarrollo", "examen"):
            Y = X[X.periodo == p]
            line += f" | {p}: n {len(Y):5d}, {Y.R.mean():+.3f}R, acierto {100 * (Y.net > 0).mean():3.0f} %"
        line += f" | total t {tcl(X.R, X.t):+.2f}"
        cr = X[X.clase == "cripto"]; fx = X[X.clase != "cripto"]
        line += f" | cripto {cr.R.mean():+.3f}R (n {len(cr)}) · oro/divisas {fx.R.mean():+.3f}R (n {len(fx)})"
        print(line, flush=True)
