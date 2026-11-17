"""Lección 17: piezas para las caídas. Reglas: docs/leccion_17.md"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import carry, data, lab14, lab15, portfolio, trend, universe  # noqa: E402
from leccion_02_pullback import BAR, prepare  # noqa: E402
from leccion_03_tendencia import signals  # noqa: E402
from leccion_06_universo import spot_close  # noqa: E402

OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
NEW = json.load(open(ROOT / "docs/l17_nuevas_top30.json"))


def spot_ohlc(sym, col):
    files = sorted((ROOT / "data/spot").glob(f"{sym}-1h-*.zip"))
    if not files:
        return None
    parts = []
    for f in files:
        d = data._read_zip(f)
        t = d["open_time"].astype("int64"); t = np.where(t > 1e14, t // 1000, t)
        parts.append(pd.Series(d[col].astype(float).to_numpy(), index=pd.to_datetime(t, unit="ms", utc=True)))
    s = pd.concat(parts).sort_index()
    return s[~s.index.duplicated()]


def r1_reverse_carry(symbols, K, borrow_apr=0.15, realista=False):
    syms = [s for s in symbols if list((ROOT / "data/spot").glob(f"{s}-1h-*.zip"))]
    members = universe.monthly_members(universe.daily_volume(syms), K)
    if realista:      # spot líquido (préstamo disponible) y nada de entrar cerca de una retirada
        sv = {}
        for s in syms:
            q = spot_ohlc(s, "quote_volume")
            if q is not None:
                sv[s] = q.resample("1D").sum().rolling(30, min_periods=20).mean()
        end = {s: data.load(s, "1h").index[-1] for s in syms}
        last = pd.Timestamp("2026-10-25", tz="UTC")
        members = {m: {x for x in ss if x in sv and sv[x].asof(m - pd.Timedelta("1D")) >= 5e6
                       and not (end[x] < last and end[x] - m < pd.Timedelta("45D"))} for m, ss in members.items()}
    long_leg, short_leg, short_hi, fund = {}, {}, {}, {}
    grid = pd.date_range(pd.Timestamp("2020-03-01", tz="UTC"), pd.Timestamp("2026-11-01", tz="UTC"), freq="8h")
    borrow = pd.Series(-borrow_apr / (365 * 3), index=grid)          # coste del préstamo, cobrado cada 8h
    for s in syms:
        sc, sh = spot_close(s), spot_ohlc(s, "high")
        if sc is None or len(sc) < 24 * 30:
            continue
        long_leg[s] = data.load(s, "1h")["close"]        # se COMPRA el perpetuo
        short_leg[s], short_hi[s] = sc, sh               # se VENDE el spot prestado
        try:
            f = data.load_funding(s)
        except Exception:
            continue
        b = borrow[(borrow.index >= sc.index[0]) & (borrow.index <= sc.index[-1])]
        fund[s] = pd.concat([-f, b]).sort_index()
    cv, ep = carry.simulate(short_leg, long_leg, fund, members, enter=0.00015, exit_=0.00005, max_pos=4, slot=0.25,
                            notional_frac=2 / 3, highs=short_hi, liq_move=0.45, ffill_limit=1 if realista else 8)
    d = cv.equity.resample("1D").last().pct_change().dropna()
    return d, ep.rename(columns={"ret_on_notional": "ret"}), cv


def r2_bear_trend_majors():
    prep = {s: prepare(s) for s in ["BTCUSDT", "ETHUSDT"]}
    cands = []
    for s, (df, f) in prep.items():
        t = trend.simulate(df, signals(df, 120, -1), 5.0, f, bar=BAR); t["symbol"] = s; cands.append(t)
    tc, tk, _ = portfolio.run(pd.concat(cands, ignore_index=True), {s: df["close"] for s, (df, _) in prep.items()}, 0.05)
    return tc.resample("1D").last().pct_change().dropna(), tk.rename(columns={"r_net": "ret"})


def stats(r):
    eq = (1 + r).cumprod(); yrs = len(r) / 365.25
    mes = (1 + r).resample("ME").prod() - 1
    return {"Sharpe": r.mean() / r.std() * np.sqrt(365), "CAGR": eq.iloc[-1] ** (1 / yrs) - 1, "DD": (1 - eq / eq.cummax()).max(),
            "peor_mes": mes.min()}


def yearly(r):
    return {k: f"{v:+.1%}" for k, v in ((1 + r).groupby(r.index.year).prod() - 1).items()}


def complement(name, r, P):
    r = r.reindex(P.index).fillna(0.0)
    mp, mr = (1 + P).resample("ME").prod() - 1, (1 + r).resample("ME").prod() - 1
    worst = mp.nsmallest(12).index
    mix = 0.75 * P + 0.25 * r
    sp, sm = stats(P), stats(mix)
    print(f"  {name}: corr. mensual con P {mp.corr(mr):+.2f} | en los 12 peores meses de P: P {mp[worst].mean():+.1%}/mes, pieza {mr[worst].mean():+.1%}/mes "
          f"(positiva en {(mr[worst] > 0).sum()} de 12) | 2022: {(1 + r['2022']).prod() - 1:+.1%} | 2026: {(1 + r['2026']).prod() - 1:+.1%}")
    print(f"     P sola: Sharpe {sp['Sharpe']:.2f}, CAGR {sp['CAGR']:.1%}, DD {sp['DD']:.1%}  →  P 75 % + pieza 25 %: Sharpe {sm['Sharpe']:.2f}, "
          f"CAGR {sm['CAGR']:.1%}, DD {sm['DD']:.1%} | 2026 de la mezcla: {(1 + mix['2026']).prod() - 1:+.1%}")
    return mix


if __name__ == "__main__":
    from sclab.stats_tests import deflated_sharpe
    P = pd.read_csv(ROOT / "docs/l16_cartera_diaria.csv", index_col=0, parse_dates=True)["cartera, pesos iguales"]
    out = {}
    print("R1 — CARRY INVERSO (largo perpetuo + corto spot prestado)\n")
    for apr in [0.15, 0.30, 0.50]:
        d, ep, cv = r1_reverse_carry(OLD, 20, apr)
        s = lab15.summary(d, ep)
        occ = cv.n_pos.groupby(cv.index.year).mean() / 4
        print(f"  DESARROLLO (antiguas), interés {apr:.0%}: Sharpe {s['sharpe']:.2f} | CAGR {s['CAGR']:.1%} | DD {s['maxDD']:.1%} | episodios {s['n']} | "
              f"WR {s['WR']:.0%} | PF {s['PF']:.2f} | mitades {s['mitad1']:+.1%} / {s['mitad2']:+.1%} | liquidaciones {int(ep.liq.sum())}")
        print(f"     por año: {yearly(d)} | ocupación: {occ.round(2).to_dict()}")
        if apr == 0.15:
            base_ok = s["sharpe"] >= 1.2 and s["PF"] >= 1.3 and s["mitad1"] > 0 and s["mitad2"] > 0
            out["R1 desarrollo"] = d; ep.to_csv(ROOT / "docs/l17_R1_dev.csv", index=False)
    print(f"  -> criba (15 %): {'PASA' if base_ok else 'no pasa'}")
    if base_ok:
        for apr in [0.15, 0.30]:
            d, ep, cv = r1_reverse_carry(NEW, 30, apr)
            s = lab15.summary(d, ep)
            ds = deflated_sharpe(d.to_numpy(), 396, 0.000328)["DSR"]
            print(f"  EXAMEN (nuevas con spot), interés {apr:.0%}: Sharpe {s['sharpe']:.2f} | CAGR {s['CAGR']:.1%} | DD {s['maxDD']:.1%} | episodios {s['n']} | "
                  f"WR {s['WR']:.0%} | PF {s['PF']:.2f} | liquidaciones {int(ep.liq.sum())} | DSR {ds:.3f}"
                  + (f" -> {'APROBADA' if s['sharpe'] >= 1.0 and s['PF'] >= 1.3 and ds >= 0.90 else 'NO aprobada'}" if apr == 0.15 else ""))
            print(f"     por año: {yearly(d)}")
            if apr == 0.15:
                out["R1 examen"] = d; ep.to_csv(ROOT / "docs/l17_R1_examen.csv", index=False)
    print("\nR2 — TENDENCIA BAJISTA EN BTC Y ETH")
    d2, t2 = r2_bear_trend_majors(); s = stats(d2)
    print(f"  Sharpe {s['Sharpe']:.2f} | CAGR {s['CAGR']:.1%} | DD {s['DD']:.1%} | trades {len(t2)} | WR {(t2.ret > 0).mean():.0%} | "
          f"PF {t2.ret[t2.ret > 0].sum() / -t2.ret[t2.ret <= 0].sum():.2f}\n     por año: {yearly(d2)}")
    out["R2 tendencia bajista BTC/ETH"] = d2
    print("\nR3 — MECHAS SIN STOP EN MONEDAS CONSOLIDADAS (218 antiguas, top 20, 0,25 %)")
    d3, t3, _ = lab14.w_portfolio(OLD, K=20, use_stop=False, risk=0.0025); s = stats(d3)
    print(f"  Sharpe {s['Sharpe']:.2f} | CAGR {s['CAGR']:.1%} | DD {s['DD']:.1%} | trades {len(t3)} | WR {(t3.ret > 0).mean():.0%}\n     por año: {yearly(d3)}")
    out["R3 mechas consolidadas"] = d3
    print("\nCOMPLEMENTO DE LA CARTERA P (1/3 carry, 1/3 S1, 1/3 tendencia)")
    for k, r in out.items():
        complement(k, r, P)
    pd.DataFrame(out).to_csv(ROOT / "docs/l17_piezas_diarias.csv")
