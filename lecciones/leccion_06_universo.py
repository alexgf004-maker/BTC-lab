"""Lección 6: universo point-in-time + S1 tendencia, S2 momentum relativo, S3 carry. Reglas: docs/leccion_06.md

  python lecciones/leccion_06_universo.py desarrollo
  python lecciones/leccion_06_universo.py examen   # UNA vez (solo estrategias aprobadas en desarrollo)
"""
import json
import warnings
warnings.filterwarnings("ignore")
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import carry, data, portfolio, swing, trend, universe, xsmom  # noqa: E402
from sclab.universe import is_member  # noqa: E402
from leccion_02_pullback import BAR, prepare  # noqa: E402
from leccion_03_tendencia import signals  # noqa: E402

DIV = json.load(open(ROOT / "docs/l06_division_activos.json"))
HALVES = {"2020-2023": ("2020-01-01", "2024-01-01"), "2024-2026": ("2024-01-01", "2026-11-01")}


def spot_close(sym):
    files = sorted((ROOT / "data/spot").glob(f"{sym}-1h-*.zip"))
    if not files:
        return None
    parts = []
    for f in files:
        d = data._read_zip(f)
        t = d["open_time"].astype("int64")
        t = np.where(t > 1e14, t // 1000, t)        # spot desde 2025 viene en microsegundos
        parts.append(pd.Series(d["close"].astype(float).to_numpy(), index=pd.to_datetime(t, unit="ms", utc=True)))
    s = pd.concat(parts).sort_index()
    return s[~s.index.duplicated()]


def curve_metrics(curve, per_year):
    r = curve.pct_change().dropna()
    yrs = (curve.index[-1] - curve.index[0]).days / 365.25
    dd = (1 - curve / curve.cummax()).max()
    cagr = (curve.iloc[-1] / curve.iloc[0]) ** (1 / yrs) - 1
    return {"sharpe": r.mean() / r.std() * np.sqrt(per_year) if r.std() > 0 else np.nan,
            "CAGR": cagr, "maxDD": dd, "MAR": cagr / dd if dd > 0 else np.nan}


def by_halves(curve, per_year, extra=None):
    out = {}
    for h, (a, b) in HALVES.items():
        cv = curve[(curve.index >= a) & (curve.index < b)]
        out[h] = {**curve_metrics(cv, per_year), **(extra(a, b) if extra else {})}
    out["total"] = {**curve_metrics(curve, per_year), **(extra("2000", "2100") if extra else {})}
    return out


def show(name, res):
    for h, m in res.items():
        extra = " | ".join(f"{k} {v:.2f}" if isinstance(v, float) else f"{k} {v}" for k, v in m.items()
                           if k not in ("sharpe", "CAGR", "maxDD", "MAR"))
        print(f"  {name:<26} {h:<10} Sharpe {m['sharpe']:5.2f} | CAGR {m['CAGR']:6.1%} | DD {m['maxDD']:5.1%} | "
              f"MAR {m['MAR']:5.2f} | {extra}")


def run_set(symbols, K, label):
    print(f"\n######## {label}: {len(symbols)} activos, universo point-in-time top {K} ########")
    vol = universe.daily_volume(symbols)
    members = universe.monthly_members(vol, K)
    results = {}

    # ---- S1 tendencia
    prep = {s: prepare(s) for s in symbols}
    cands = []
    for s, (df, fund) in prep.items():
        t = trend.simulate(df, signals(df, 120, 1), 5.0, fund, bar=BAR, one_at_a_time=False)
        t["symbol"] = s
        t = t[is_member(members, s, pd.DatetimeIndex(t.entry_time))]
        cands.append(t)
    cands = pd.concat(cands, ignore_index=True)
    curve, tk, lev = portfolio.run(cands, {s: df["close"] for s, (df, _) in prep.items()}, 0.01, K=10)
    curve = curve.resample("1D").last()
    tstats = lambda a, b: (lambda x: {"trades": len(x), "WR": float((x.r_net > 0).mean()), "PF": float(swing.stats(x.r_net)["PF"])})(
        tk[(tk.entry_time >= pd.Timestamp(a, tz="UTC")) & (tk.entry_time < pd.Timestamp(b, tz="UTC"))])
    results["S1 tendencia"] = (by_halves(curve, 365, tstats), curve)

    # ---- S2 momentum relativo
    closes_d = pd.DataFrame({s: data.load(s, "1h")["close"].resample("1D").last() for s in symbols})
    fund_d = pd.DataFrame({s: data.load_funding(s).resample("1D").sum() for s in symbols})
    for mode, name in [("long", "S2a momentum largo"), ("longshort", "S2b momentum largo-corto"), ("market", "  control: mercado")]:
        w = xsmom.weekly_returns(closes_d, fund_d, members, mode=mode)
        cv = (1 + w.ret).cumprod()
        def wstats(a, b, w=w):
            x = w.ret[(w.index >= pd.Timestamp(a, tz="UTC")) & (w.index < pd.Timestamp(b, tz="UTC"))]
            return {"semanas": len(x), "WR": float((x > 0).mean()), "PF": float(x[x > 0].sum() / -x[x <= 0].sum()),
                    "rotación": float(w.turnover.mean())}
        results[name] = (by_halves(cv, 52, wstats), cv)

    # ---- S3 carry de funding
    perp = {s: data.load(s, "1h")["close"] for s in symbols}
    spot = {s: v for s in symbols if (v := spot_close(s)) is not None}
    fund = {s: data.load_funding(s) for s in symbols}
    highs = {s: data.load(s, "1h")["high"] for s in symbols}
    cv, ep = carry.simulate(perp, spot, fund, members, highs=highs)
    print(f"  carry: liquidaciones simuladas {int(ep.liq.sum())}, reequilibrios {int(ep.rebal.sum())}")
    eq = cv.equity.resample("1D").last()
    def cstats(a, b):
        x = ep[(ep.entry >= pd.Timestamp(a, tz="UTC")) & (ep.entry < pd.Timestamp(b, tz="UTC"))]
        return {"episodios": len(x), "WR": float((x.pnl > 0).mean()), "PF": float(x.pnl[x.pnl > 0].sum() / -x.pnl[x.pnl <= 0].sum()),
                "días_med": float(((x.exit - x.entry).dt.total_seconds() / 86400).median()), "ocupación": float(cv.n_pos.mean() / 5)}
    results["S3 carry funding"] = (by_halves(eq, 365, cstats), eq)
    ep.to_csv(ROOT / f"docs/l06_carry_episodios_{label.lower()}.csv", index=False)

    for name, (res, _) in results.items():
        show(name, res); print()
    curves = pd.DataFrame({k: v[1] for k, v in results.items()})
    curves.to_csv(ROOT / f"docs/l06_curvas_{label.lower()}.csv")
    return results


def passes_dev(res):
    return all(res[h]["sharpe"] > 0 for h in HALVES) and res["total"]["sharpe"] >= 1.0 and res["total"]["PF"] >= 1.3


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else "desarrollo"
    if fase == "desarrollo":
        res = run_set(DIV["desarrollo"], 20, "DESARROLLO")
        ok = {k: bool(passes_dev(v[0])) for k, v in res.items() if not k.startswith("  ")}
        print("Aprueban desarrollo:", ok)
        json.dump(ok, open(ROOT / "docs/l06_aprobadas_desarrollo.json", "w"), indent=1)

    if fase == "examen":
        from sclab.stats_tests import deflated_sharpe
        res = run_set(DIV["examen"], 10, "EXAMEN")
        var_sr = 0.000328   # varianza del Sharpe diario entre las 16 combinaciones de la rejilla L3 (misma medida que en L5)
        N = 337 + 5
        for k in ["S1 tendencia", "S3 carry funding"]:
            r, cv = res[k]
            d = cv.pct_change().dropna().to_numpy()
            ds = deflated_sharpe(d, N, var_sr)
            t = r["total"]
            ok = t["sharpe"] >= 0.5 and t["PF"] >= 1.3 and ds["DSR"] >= 0.90
            print(f"{k}: Sharpe {t['sharpe']:.2f} | PF {t['PF']:.2f} | WR {t['WR']:.0%} | DSR {ds['DSR']:.3f} -> {'APROBADA' if ok else 'NO aprobada'}")
