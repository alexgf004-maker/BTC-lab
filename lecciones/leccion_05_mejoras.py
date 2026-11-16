"""Lección 5: variantes de la literatura, adopción estricta y examen en 15 activos nuevos.
Reglas: docs/leccion_05.md

  python lecciones/leccion_05_mejoras.py desarrollo
  python lecciones/leccion_05_mejoras.py examen       # UNA vez, con docs/l05_config_congelada.json
"""
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import data, indicators as ind, portfolio, swing, trend  # noqa: E402
from leccion_02_pullback import SYMBOLS as DEV, BAR, prepare  # noqa: E402
from leccion_03_tendencia import signals  # noqa: E402

HOLDOUT = ["DOTUSDT", "LUNAUSDT", "MATICUSDT", "ATOMUSDT", "TRXUSDT", "ETCUSDT", "BCHUSDT", "FILUSDT",
           "UNIUSDT", "AAVEUSDT", "EOSUSDT", "XLMUSDT", "ALGOUSDT", "NEARUSDT", "FTTUSDT"]
LOOKS = [5, 10, 20, 30, 60, 90, 150, 250, 360]          # días (Zarattini et al. 2025)
M, RISK = 5.0, 0.01
HALVES = {"2020-2023": ("2020-01-01", "2024-01-01"), "2024-2026": ("2024-01-01", "2026-11-01")}
CONGELADA = ROOT / "docs/l05_config_congelada.json"


@dataclass(frozen=True)
class Cfg:
    ensemble: bool = False
    btc_regime: bool = False
    funding_filter: bool = False
    vol_target: bool = False
    pyramid: bool = False


def btc_regime_series():
    h1 = data.load("BTCUSDT", "1h")
    dd = data.resample(h1, "1D")
    return (dd["close"] > dd["close"].rolling(200).mean()).astype(float)


def build(prep, cfg: Cfg, btc_ok_daily):
    rows, cid = [], 0
    subs = [(n, 1 / len(LOOKS)) for n in LOOKS] if cfg.ensemble else [(20, 1.0)]
    for sym, (df, fund) in prep.items():
        ok = np.ones(len(df), bool)
        if cfg.btc_regime and sym != "BTCUSDT":
            ok &= ind.daily_on_intraday(btc_ok_daily, df.index, BAR).fillna(0).to_numpy() > 0
        if cfg.funding_filter:
            fm = fund.rolling(9).mean()
            f_at = fm.reindex(fm.index.union(df.index + BAR)).ffill().reindex(df.index + BAR).to_numpy()
            ok &= ~(f_at > 0.0003)
        for n_days, mult in subs:
            side = signals(df, n_days * 6, 1) * ok
            t = trend.simulate(df, side, M, fund, bar=BAR, one_at_a_time=False,
                               pyramid_at=2.0 if cfg.pyramid else None)
            if t.empty:
                continue
            key = f"{sym}-{n_days}"
            ids = np.arange(cid, cid + len(t)); cid += len(t)
            base = t.assign(symbol=sym, key=key, risk_mult=mult, cid=ids, parent=-1)
            rows.append(base)
            if cfg.pyramid:
                a = t[t.add_time.notna()]
                rows.append(pd.DataFrame({"symbol": sym, "key": key + "-add", "risk_mult": mult,
                                          "cid": np.arange(cid, cid + len(a)), "parent": ids[t.add_time.notna().to_numpy()],
                                          "entry_time": a.add_time, "exit_time": a.exit_time, "side": a.side,
                                          "entry": a.add_entry, "R": a.add_R, "r_net": a.add_r_net}))
                cid += len(a)
    return pd.concat(rows, ignore_index=True)


def evaluate(prep, cfg, btc_ok):
    cands = build(prep, cfg, btc_ok)
    closes = {s: df["close"] for s, (df, _) in prep.items()}
    curve, tk, lev = portfolio.run(cands, closes, RISK, vol_target=0.25 if cfg.vol_target else None)
    res = {}
    for h, (a, b) in HALVES.items():
        cv = curve[(curve.index >= a) & (curve.index < b)]
        m = portfolio.metrics(cv / cv.iloc[0])
        tt = tk[(tk.entry_time >= a) & (tk.entry_time < b)]
        res[h] = {**m, "trades": len(tt), "win_rate": (tt.r_net > 0).mean(), "PF": swing.stats(tt.r_net)["PF"]}
    res["total"] = {**portfolio.metrics(curve, lev), "trades": len(tk), "win_rate": (tk.r_net > 0).mean(),
                    "PF": swing.stats(tk.r_net)["PF"]}
    return res, curve, tk


def show(name, res):
    for h, m in res.items():
        print(f"  {name:<22} {h:<10} Sharpe {m['sharpe']:5.2f} | CAGR {m['CAGR']:6.1%} | DD {m['maxDD']:5.1%} | "
              f"MAR {m['MAR']:5.2f} | trades {m['trades']:4d} | WR {m['win_rate']:4.0%} | PF {m['PF']:4.2f}")


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else "desarrollo"
    btc_ok = btc_regime_series()
    if fase == "desarrollo":
        prep = {s: prepare(s) for s in DEV}
        variants = {"V0 base": Cfg(), "V1 conjunto periodos": Cfg(ensemble=True), "V2 régimen BTC": Cfg(btc_regime=True),
                    "V3 filtro funding": Cfg(funding_filter=True), "V4 objetivo vol": Cfg(vol_target=True),
                    "V5 piramidación": Cfg(pyramid=True)}
        results, curves = {}, {}
        for name, cfg in variants.items():
            results[name], curves[name], _ = evaluate(prep, cfg, btc_ok)
            show(name, results[name]); print()
        base = results["V0 base"]
        adopt = []
        for name in list(variants)[1:]:
            r = results[name]
            ok = all(r[h]["sharpe"] > base[h]["sharpe"] and r[h]["MAR"] > base[h]["MAR"] for h in HALVES)
            print(f"{name}: {'ADOPTADA' if ok else 'rechazada'}")
            if ok: adopt.append(name)
        if adopt:
            comb = Cfg(**{k: any(getattr(variants[n], k) for n in adopt) for k in asdict(Cfg())})
            rc, curves["combinada"], _ = evaluate(prep, comb, btc_ok)
            print("\nCombinación de las adoptadas:", asdict(comb)); show("combinada", rc)
            ok = all(rc[h]["sharpe"] > base[h]["sharpe"] and rc[h]["MAR"] > base[h]["MAR"] for h in HALVES)
            print("Combinación supera a V0 en ambas mitades:", ok)
            json.dump({"cfg": asdict(comb), "supera_V0": ok}, open(ROOT / "docs/l05_config_candidata.json", "w"), indent=1)
        pd.DataFrame({k: v.resample("1D").last() for k, v in curves.items()}).to_csv(ROOT / "docs/l05_curvas_desarrollo.csv")
        json.dump({k: {h: {kk: float(vv) for kk, vv in m.items()} for h, m in v.items()} for k, v in results.items()},
                  open(ROOT / "docs/l05_resultados_desarrollo.json", "w"), indent=1)

    if fase == "examen":
        from sclab.stats_tests import deflated_sharpe
        from leccion_03_tendencia import GRID
        cfg = Cfg(**json.load(open(CONGELADA))["cfg"])
        # Varianza del Sharpe entre pruebas: rejilla de la Lección 3 como cartera en desarrollo (conservador)
        dev = {s: prepare(s) for s in DEV}
        closes = {s: df["close"] for s, (df, _) in dev.items()}
        srs = []
        import itertools
        for n_, m_ in itertools.product(*GRID.values()):
            c = []
            for s, (df, fund) in dev.items():
                t = trend.simulate(df, signals(df, n_, 1), m_, fund, bar=BAR, one_at_a_time=False); t["symbol"] = s; c.append(t)
            cv, _, _ = portfolio.run(pd.concat(c), closes, RISK)
            d = cv.resample("1D").last().pct_change().dropna(); srs.append(d.mean() / d.std())
        var_sr = float(np.var(srs, ddof=1))
        N_TRIALS = 200 + 32 + 18 + 80 + 7
        hold = {}
        for s in HOLDOUT:
            hold[s] = prepare(s)
        print(f"Examen en {len(hold)} activos nuevos: {', '.join(hold)}")
        out = {}
        for name, c in [("V0 base", Cfg()), ("CONGELADA", cfg)]:
            res, curve, tk = evaluate(hold, c, btc_ok)
            show(name, res); print()
            d = curve.resample("1D").last().pct_change().dropna().to_numpy()
            ds = deflated_sharpe(d, N_TRIALS, var_sr)
            print(f"  {name}: lev máx {res['total']['lev_max']:.1f}x | Deflated Sharpe = {ds['DSR']:.3f} "
                  f"(SR diario {ds['SR_diario']:.3f} frente a {ds['SR0_azar']:.3f} esperable por azar con {N_TRIALS} pruebas)")
            print("  Por activo (beneficio en fracción del capital inicial):", tk.groupby("symbol").pnl.sum().round(3).sort_values().to_dict(), "\n")
            out[name] = (res, ds, tk)
        r, ds, tk = out["CONGELADA"]
        r0 = out["V0 base"][0]
        print("CRITERIOS: Sharpe > V0:", r["total"]["sharpe"] > r0["total"]["sharpe"],
              "| PF >= 1,3:", r["total"]["PF"] >= 1.3, "| DSR >= 0,90:", ds["DSR"] >= 0.90)
        tk.to_csv(ROOT / "docs/l05_examen_trades.csv", index=False)
