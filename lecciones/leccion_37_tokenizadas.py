"""Lección 37 — Acciones tokenizadas en Binance (docs/leccion_37.md)."""
import io
import sys
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import carry, data  # noqa: E402

TICK = "AAPL AMZN COIN CRCL GOOGL HOOD META MSFT MSTR NVDA QQQ SPY TSLA".split()
SPOT_LEG, PERP_LEG = 0.0012, 0.0007


def spot(t):
    parts = []
    for f in sorted((ROOT / "data/tok").glob(f"{t}BUSDT-1h-*.zip")):
        with zipfile.ZipFile(f) as z:
            d = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None)
        parts.append(d.iloc[:, [0, 1, 4, 7]])
    if not parts:
        return None
    d = pd.concat(parts); ts = d[0].astype("int64").to_numpy(); ts = np.where(ts > 1e14, ts // 1000, ts)
    df = pd.DataFrame({"open": d[1].astype(float).values, "close": d[4].astype(float).values, "qv": d[7].astype(float).values},
                      index=pd.DatetimeIndex(pd.to_datetime(ts, unit="ms", utc=True)))
    return df[~df.index.duplicated()].sort_index()


def k1_funding():
    print("=== K1a funding de los perpetuos de acciones (toda su historia)")
    rows = []
    for t in TICK:
        f = data.load_funding(f"{t}USDT")
        d3 = f.rolling("72h").sum() / 9
        rows.append((t, str(f.index[0].date()), 100 * f.mean() * 3 * 365 if len(f) else np.nan, 100 * (f > 0).mean(), 100 * (d3 > 0.00015).mean()))
    T = pd.DataFrame(rows, columns=["acción", "desde", "funding anual medio %", "% pagos positivos", "% tiempo con señal K1"])
    print(T.round(1).to_string(index=False))


def k1_carry():
    perp, spt, fund = {}, {}, {}
    for t in TICK:
        s = spot(t)
        if s is None:
            continue
        sym = f"{t}USDT"
        perp[sym] = data.load(sym, "1h")["close"]; spt[sym] = s["close"]; fund[sym] = data.load_funding(sym)
    start = min(s.index[0] for s in spt.values())
    mem = {m: set(perp) for m in pd.date_range(start.normalize().replace(day=1), pd.Timestamp("2026-10-01", tz="UTC"), freq="MS")}
    cv, ep = carry.simulate(perp, spt, fund, mem, enter=0.00015, exit_=0.00005, max_pos=4, slot=0.25, notional_frac=2 / 3,
                            start=str(start.date()))
    eq = cv["equity"]
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    d = eq.resample("1D").last().pct_change().dropna()
    print(f"\n=== K1b carry completo con tokens spot ({start.date()} → 2026-10): x{eq.iloc[-1]:.4f} "
          f"({100 * (eq.iloc[-1] ** (1 / yrs) - 1):+.1f} % anual) | Sharpe {d.mean() / d.std() * np.sqrt(365):.2f} | episodios {len(ep)}")
    if len(ep):
        print(ep[["symbol", "entry", "exit", "ret_on_notional"]].tail(10).to_string(index=False) if "ret_on_notional" in ep else ep.tail())


def weekend(px_open, px_close, cost):
    out = []
    sundays = px_close.index[(px_close.index.dayofweek == 6) & (px_close.index.hour == 21)]
    for s in sundays:
        fri, mon = s - pd.Timedelta("2D"), s + pd.Timedelta("6h")
        if fri not in px_open.index or mon not in px_close.index:
            continue
        p0, p1, p2 = px_open[fri], px_close[s], px_close[mon]
        W = np.log(p1 / p0)
        if abs(W) >= 0.01:
            out.append((s, -np.sign(W) * (p2 / p1 - 1) - 2 * cost))
    return out


def k2():
    print("\n=== K2 reversión del fin de semana: tokens spot frente a perpetuos (mismas semanas)")
    rs, rp = [], []
    for t in TICK:
        s = spot(t)
        if s is None:
            continue
        p = data.load(f"{t}USDT", "1h")
        p = p[p.index >= s.index[0]]
        rs += weekend(s["open"], s["close"], SPOT_LEG)
        rp += weekend(p["open"], p["close"], PERP_LEG)
    for name, r in (("spot (tokens)", rs), ("perpetuos", rp)):
        x = pd.DataFrame(r, columns=["t", "r"])
        if x.empty:
            print(name, "sin operaciones"); continue
        w = x.groupby("t").r.mean()
        h1, h2 = w[w.index < "2026-09-01"], w[w.index >= "2026-09-01"]
        print(f"{name:14s} operaciones {len(x)} en {len(w)} fines de semana | media {100 * x.r.mean():+.2f} % neta | "
              f"t (semanas) {w.mean() / w.std() * np.sqrt(len(w)):+.2f} | jun–ago {100 * h1.mean():+.2f} % / sep–oct {100 * h2.mean():+.2f} %")


def k3():
    print("\n=== K3 diferencial spot–perpetuo")
    res, devs = [], []
    for t in TICK:
        s = spot(t)
        if s is None:
            continue
        p = data.load(f"{t}USDT", "1h")["close"]
        j = pd.concat([s["close"], p], axis=1, keys=["s", "p"]).dropna()
        b = j.s / j.p - 1
        devs.append((t, 1e4 * b.abs().median(), 1e4 * b.abs().quantile(0.99), 1e4 * b.mean(), s.qv.resample("1D").sum().median() / 1e3))
        i, idx = 0, b.index
        while i < len(b) - 1:
            if abs(b.iloc[i]) > 0.005:
                side = -np.sign(b.iloc[i])                         # comprar el barato, vender el caro
                k = i + 1
                while k < len(b) and abs(b.iloc[k]) >= 0.001 and (idx[k] - idx[i]) < pd.Timedelta("24h"):
                    k += 1
                k = min(k, len(b) - 1)
                gain = side * (b.iloc[k] - b.iloc[i]) / (1 + b.iloc[i])
                res.append((idx[i], t, gain - 2 * (SPOT_LEG + PERP_LEG)))
                i = k + 1
            else:
                i += 1
    D = pd.DataFrame(devs, columns=["acción", "|dif.| mediana pb", "|dif.| p99 pb", "dif. media pb", "vol. spot diario mediano k$"])
    print(D.round(1).to_string(index=False))
    x = pd.DataFrame(res, columns=["t", "acción", "r"])
    if len(x):
        d = x.groupby(x.t.dt.floor("1D")).r.mean()
        print(f"operaciones {len(x)} | media neta {100 * x.r.mean():+.3f} % | t (días) {d.mean() / d.std() * np.sqrt(len(d)):+.2f}")
    else:
        print("sin operaciones (el diferencial nunca supera 0,5 %)")


if __name__ == "__main__":
    k1_funding(); k1_carry(); k2(); k3()
