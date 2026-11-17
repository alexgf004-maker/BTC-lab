"""Lección 27 — HOLD: gestión por volatilidad, filtro de 200 días, índice diversificado y DCA (pre-registro en docs/leccion_27.md)."""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sclab import data, universe  # noqa: E402
from sclab.portfolio import metrics  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
COST = 0.0012
DEV = ("2017-09-01", "2021-12-31")
EXA = ("2022-01-01", "2026-10-31")


def spot_daily(sym):
    parts = []
    for f in sorted((ROOT / "data/spot1d").glob(f"{sym}-1d-*.zip")):
        with zipfile.ZipFile(f) as z:
            d = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None)
        parts.append(d.iloc[:, [0, 4]])
    d = pd.concat(parts)
    t = d[0].astype("int64")
    t = np.where(t > 1e14, t // 1000, t)                       # desde 2025 el spot viene en microsegundos
    s = pd.Series(d[4].astype(float).to_numpy(), index=pd.to_datetime(t, unit="ms", utc=True).normalize())
    return s[~s.index.duplicated()].sort_index()


def weights_rule(px, rule):
    r = px.pct_change()
    vol = r.rolling(30).std() * np.sqrt(365)
    ma = px.rolling(200).mean()
    if rule == "hold":
        target = pd.Series(1.0, index=px.index)
    elif rule == "vol":
        target = np.minimum(1.0, 0.40 / vol)
    elif rule == "ma200":
        target = (px > ma).astype(float)
    elif rule == "vol+ma200":
        target = np.minimum(1.0, 0.40 / vol) * (px > ma)
    return target


def simulate(px, target, band=0.10):
    """Operación al cierre de t con la señal de t; rentabilidad desde t+1. Costes por nocional negociado."""
    r = px.pct_change().fillna(0).to_numpy()
    tg = target.to_numpy()
    eq, w, out, turn = 1.0, 0.0, [], 0.0
    for i in range(len(px)):
        eq *= 1 + w * r[i]                                         # rentabilidad del día con el peso de ayer
        w = w * (1 + r[i]) / (1 + w * r[i]) if (1 + w * r[i]) != 0 else w   # deriva del peso
        t = tg[i]
        if np.isfinite(t) and (abs(t - w) > band or (t == 0 and w > 0) or (t == 1 and w < 1 and abs(t - w) > band)):
            eq -= eq * abs(t - w) * COST; turn += abs(t - w); w = t
        out.append(eq)
    return pd.Series(out, index=px.index), turn


def basket(pxs, rule):
    """Cesta 50/50 con reequilibrio mensual; la regla se aplica a cada activo por separado (w_i/2)."""
    curves = []
    for p in pxs:
        c, _ = simulate(p, weights_rule(p, rule))
        curves.append(c)
    df = pd.concat(curves, axis=1).dropna()
    rets = df.pct_change().fillna(0)
    eq, out = 1.0, []
    for m, g in rets.groupby(rets.index.to_period("M")):
        wts = np.array([0.5, 0.5])
        for _, row in g.iterrows():
            gr = 1 + row.to_numpy()
            eq *= (wts * gr).sum(); wts = wts * gr / (wts * gr).sum(); out.append(eq)
        eq -= eq * np.abs(wts - 0.5).sum() * COST * 0.5
    return pd.Series(out, index=rets.index)


def boot_diff(c1, c0, n=4000, block=90, seed=0):
    a = c1.pct_change().dropna(); b = c0.pct_change().reindex(a.index).fillna(0)
    A, Bv = a.to_numpy(), b.to_numpy()
    rng = np.random.default_rng(seed); L = len(A); diffs = []
    for _ in range(n):
        idx = np.concatenate([np.arange(s, s + block) % L for s in rng.integers(0, L, L // block + 1)])[:L]
        x, y = A[idx], Bv[idx]
        diffs.append(x.mean() / x.std() * np.sqrt(365) - y.mean() / y.std() * np.sqrt(365))
    return float((np.array(diffs) <= 0).mean())


def fmt(m):
    return f"Sharpe {m['sharpe']:5.2f} | CAGR {100 * m['CAGR']:6.1f} % | DD {100 * m['maxDD']:5.1f} % | x{m['final_x']:7.2f} | peor mes {100 * m['peor_mes']:6.1f} %"


def section_rules():
    px = {"BTC": spot_daily("BTCUSDT"), "ETH": spot_daily("ETHUSDT")}
    print("Primer día:", {k: str(v.index[0].date()) for k, v in px.items()})
    res = {}
    for name in ["BTC", "ETH", "50/50"]:
        for rule in ["hold", "vol", "ma200", "vol+ma200"]:
            if name == "50/50":
                c = basket([px["BTC"], px["ETH"]], rule); turn = np.nan
            else:
                c, turn = simulate(px[name], weights_rule(px[name], rule))
            res[(name, rule)] = c
    for per, (a, b) in (("DESARROLLO", DEV), ("EXAMEN", EXA)):
        print(f"\n=== {per} {a} → {b}")
        for name in ["BTC", "ETH", "50/50"]:
            base = res[(name, "hold")].loc[a:b]
            mb = metrics(base / base.iloc[0])
            for rule in ["hold", "vol", "ma200", "vol+ma200"]:
                c = res[(name, rule)].loc[a:b]; c = c / c.iloc[0]
                m = metrics(c)
                extra = "" if rule == "hold" else (f" | mejora Sharpe {m['sharpe'] - mb['sharpe']:+.2f} (P≤0 {boot_diff(c, base):.2f})"
                                                   f" | DD {'menor' if m['maxDD'] < mb['maxDD'] else 'MAYOR'}")
                print(f"{name:5s} {rule:10s} {fmt(m)}{extra}")
    return res


STABLE = {"USDCUSDT", "BUSDUSDT", "TUSDUSDT", "FDUSDUSDT", "USDPUSDT", "DAIUSDT", "XAUUSDT", "XAGUSDT", "PAXGUSDT", "XAUTUSDT",
          "EURUSDT", "GBPUSDT", "USDEUSDT", "USD1USDT"}


def section_index():
    syms = sorted(p.name.replace("-1h.parquet", "") for p in (ROOT / "data/cache").glob("*USDT-1h.parquet"))
    syms = [s for s in syms if s not in STABLE and not s.startswith("q_")]
    vol = universe.daily_volume(syms)
    mem = universe.monthly_members(vol, 10)
    print("\nMiembros (muestra):", {str(k.date()): sorted(v) for k, v in list(mem.items())[::12]})
    closes, fund = {}, {}
    allm = set().union(*mem.values())
    for s in allm:
        closes[s] = data.load(s, "1h")["close"].resample("1D").last()
        try:
            fund[s] = data.load_funding(s).resample("1D").sum()
        except Exception:
            fund[s] = pd.Series(dtype=float)
    def run(member_fn):
        eq, out = 1.0, []
        for m in sorted(mem):
            members = member_fn(m)
            end = m + pd.offsets.MonthBegin(1)
            days = pd.date_range(m, end - pd.Timedelta("1D"), freq="D", tz="UTC")
            rets = []
            for s in members:
                c = closes[s].reindex(days.union([m - pd.Timedelta("1D")])).ffill()
                r = c.pct_change().iloc[1:]
                f = fund[s].reindex(days).fillna(0)
                rr = (r - f).fillna(-1.0 if c.iloc[1:].isna().all() else 0.0)  # deslistada a mitad: se asume pérdida hasta el último precio
                rets.append(rr.to_numpy())
            w = np.full(len(members), 1 / len(members))
            eq -= eq * COST * 0.5                                   # rotación mensual aproximada (50 % del nocional)
            for i in range(len(days)):
                g = np.array([x[i] for x in rets])
                eq *= 1 + (w * g).sum(); w = w * (1 + g) / max(1e-12, (w * (1 + g)).sum())
                out.append((days[i], eq))
        return pd.Series(dict(out))
    idx = run(lambda m: sorted(mem[m]))
    btc = run(lambda m: ["BTCUSDT"])
    for per, (a, b) in (("DESARROLLO", ("2020-03-01", "2022-12-31")), ("EXAMEN", ("2023-01-01", "2026-10-31"))):
        print(f"\n=== H5 {per}")
        for n, c in (("índice top-10", idx), ("BTC perpetuo", btc)):
            c = c.loc[a:b]; print(f"{n:14s} {fmt(metrics(c / c.iloc[0]))}")


def section_dca(btc):
    rows = []
    months = pd.date_range("2017-09-01", "2024-10-01", freq="MS", tz="UTC")
    for m in months:
        p = btc.loc[m:]
        if len(p) < 730:
            continue
        buys = [p.loc[m + pd.DateOffset(months=k):].iloc[0] for k in range(12)]
        units_dca = sum(1 / 12 / b for b in buys); units_ls = 1 / p.iloc[0]
        for h in (12, 24):
            v = p.loc[m + pd.DateOffset(months=h):].iloc[0]
            rows.append((m, h, units_dca * v, units_ls * v))
    d = pd.DataFrame(rows, columns=["inicio", "meses", "dca", "golpe"])
    print("\n=== H6 DCA (12 compras mensuales) frente a todo de golpe, BTC")
    for h, g in d.groupby("meses"):
        print(f"a {h} meses: DCA mejor en {100 * (g.dca > g.golpe).mean():.0f} % de los inicios | mediana DCA x{g.dca.median():.2f} "
              f"golpe x{g.golpe.median():.2f} | peor DCA x{g.dca.min():.2f} peor golpe x{g.golpe.min():.2f}")


if __name__ == "__main__" and "--corregido" not in sys.argv:
    res = section_rules()
    section_dca(spot_daily("BTCUSDT"))
    section_index()


def section_corrected():
    """Corrección declarada: el desarrollo empieza cuando existen todas las señales (200 días de historia) + historia larga (Coin Metrics)."""
    btc = spot_daily("BTCUSDT"); eth = spot_daily("ETHUSDT")
    cm = pd.read_parquet(ROOT / "data/cache/btc_onchain.parquet")["PriceUSD"].dropna()
    cm.index = cm.index.normalize()
    sets = [("BTC Binance", btc, ("2018-03-06", "2021-12-31")), ("ETH Binance", eth, ("2018-03-06", "2021-12-31")),
            ("BTC Coin Metrics", cm, ("2013-01-01", "2021-12-31")), ("BTC Coin Metrics", cm, ("2013-01-01", "2017-08-31")),
            ("BTC Coin Metrics", cm, ("2022-01-01", "2026-10-31"))]
    for name, px, (a, b) in sets:
        print(f"\n=== {name} {a} → {b}")
        res = {r: simulate(px, weights_rule(px, r))[0] for r in ["hold", "vol", "ma200", "vol+ma200"]}
        base = res["hold"].loc[a:b]; base = base / base.iloc[0]; mb = metrics(base)
        for r, c in res.items():
            c = c.loc[a:b]; c = c / c.iloc[0]; m = metrics(c)
            extra = "" if r == "hold" else f" | mejora Sharpe {m['sharpe'] - mb['sharpe']:+.2f} (P≤0 {boot_diff(c, base):.2f}) | DD {'menor' if m['maxDD'] < mb['maxDD'] else 'MAYOR'}"
            print(f"{r:10s} {fmt(m)}{extra}")


if __name__ == "__main__" and "--corregido" in sys.argv:
    section_corrected()
