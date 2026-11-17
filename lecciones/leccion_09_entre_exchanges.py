"""Lección 9: carry Binance ↔ Hyperliquid y examen de nuevos listados. Reglas: docs/leccion_09.md

  python lecciones/leccion_09_entre_exchanges.py h10      # examen confirmatorio (una vez)
  python lecciones/leccion_09_entre_exchanges.py criba
  python lecciones/leccion_09_entre_exchanges.py examen   # una vez, solo lo que pase la criba
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "lecciones"))
from sclab import carry, data, hyperliquid as hl, lab, universe  # noqa: E402

DIV = json.load(open(ROOT / "docs/l09_division_hl.json"))
T0 = pd.Timestamp("2023-06-01", tz="UTC")
SUB = {"2023-06→2024": ("2023-06-01", "2025-01-01"), "2025→2026-10": ("2025-01-01", "2026-11-01")}


def fase_h10():
    cand = [s for l in open(ROOT / "data/universo_examen2.txt") if not l.startswith("#") for s in l.split()]
    fresh = [s for s in cand if list((ROOT / "data/raw").glob(f"{s}-1h-*.zip"))]
    P = lab.panel(fresh)
    d, tr = lab.h10(P, data.load("BTCUSDT", "1h")["close"], data.load_funding("BTCUSDT"))
    r = tr.ret
    t = r.mean() / r.std() * np.sqrt(len(r))
    pf = r[r > 0].sum() / -r[r <= 0].sum()
    print(f"H10 examen: n {len(r)} | WR {(r > 0).mean():.0%} | media {r.mean():+.1%} | mediana {r.median():+.1%} | t {t:.2f} | PF {pf:.2f} | "
          f"stops {int(tr.stopped.sum())} | peor {r.min():.0%}")
    print("por año:", tr.groupby(tr.entry.dt.year).ret.agg(["count", "mean", lambda x: (x > 0).mean()]).round(2).values.tolist(),
          sorted(tr.entry.dt.year.unique()))
    m = lab.metrics(d[d.index >= tr.entry.min().floor("1D")])
    print(f"cartera (5 % por trade): Sharpe {m['sharpe']:.2f} | CAGR {m['CAGR']:.1%} | DD {m['maxDD']:.1%}")
    conc = pd.concat([pd.Series(1, tr.entry), pd.Series(-1, tr.exit)]).sort_index().cumsum().max()
    print("posiciones simultáneas máx.:", conc)
    print("VEREDICTO:", "APROBADA" if len(r) >= 50 and t >= 3 and pf >= 1.3 else "NO aprobada")
    tr.to_csv(ROOT / "docs/l09_h10_trades.csv", index=False)


if __name__ == "__main__":
    fase = sys.argv[1]
    if fase == "h10":
        fase_h10()


def run_x(part: str):
    """Ejecuta X1 y X2 en una mitad ('desarrollo' o 'examen'). Devuelve {nombre: (curva diaria, episodios, ocupación)}."""
    coins = [c for c in DIV[part] if (hl.DIR / f"{c}-funding.parquet").exists()]
    mp = DIV["mapa"]
    syms = [mp[c] for c in DIV[part]]
    members = universe.monthly_members(universe.daily_volume(syms), 10)
    from leccion_06_universo import spot_close
    one_h = pd.Timedelta("1h")
    hl_px, hl_hi, hl_lo, hl_f, b_perp, b_spot, f_diff = {}, {}, {}, {}, {}, {}, {}
    for c in coins:
        s = mp[c]
        k = hl.candles_8h(c)
        hl_px[s], hl_hi[s], hl_lo[s] = k["close"], k["high"], k["low"]
        hl_f[s] = hl.funding(c)
        bp = data.load(s, "1h")["close"]; bp.index = bp.index + one_h
        b_perp[s] = bp
        sp = spot_close(s)
        if sp is not None:
            sp.index = sp.index + one_h
            b_spot[s] = sp
        f_diff[s] = pd.concat([hl_f[s], -data.load_funding(s)]).sort_index()
    Hg, Lg = pd.DataFrame(hl_hi), pd.DataFrame(hl_lo)
    out = {}
    cv, ep = carry.simulate(hl_px, b_spot, hl_f, members, enter=0.00015, exit_=0.00005, max_pos=4, slot=0.25,
                            notional_frac=2 / 3, liq_move=0.45, start="2023-06-01", Hgrid=Hg,
                            leg_cost=0.0010 + 0.00045 + 2 * 0.0002, rebal_cost=2 * (0.00045 + 0.0002))
    out["X1 spot Binance + corto HL"] = (cv, ep)
    cv, ep = carry.simulate(hl_px, b_perp, f_diff, members, enter=0.00015, exit_=0.00005, max_pos=4, slot=0.25,
                            notional_frac=1.0, liq_move=0.45, start="2023-06-01", Hgrid=Hg, Lgrid=Lg,
                            leg_cost=0.0005 + 0.00045 + 2 * 0.0002, rebal_cost=2 * (0.0005 + 0.00045 + 2 * 0.0002))
    out["X2 perp Binance + corto HL"] = (cv, ep)
    return out, len(coins)


def summarize(name, cv, ep):
    eq = cv.equity.resample("1D").last()
    d = eq.pct_change().dropna()
    res = {"sharpe": d.mean() / d.std() * np.sqrt(365) if d.std() > 0 else np.nan,
           "CAGR": (eq.iloc[-1] / eq.iloc[0]) ** (365.25 / (eq.index[-1] - eq.index[0]).days) - 1,
           "maxDD": (1 - eq / eq.cummax()).max(), "n": len(ep), "WR": (ep.pnl > 0).mean() if len(ep) else np.nan,
           "PF": ep.pnl[ep.pnl > 0].sum() / -ep.pnl[ep.pnl <= 0].sum() if len(ep) and (ep.pnl <= 0).any() else np.nan,
           "liq": int(ep.liq.sum()) if len(ep) else 0}
    sub = {}
    for h, (a, b) in SUB.items():
        e = eq[(eq.index >= a) & (eq.index < b)]
        sub[h] = e.iloc[-1] / e.iloc[0] - 1
        res[f"ocup {h}"] = cv.n_pos[(cv.index >= a) & (cv.index < b)].mean() / 4
    print(f"{name:<28} Sharpe {res['sharpe']:5.2f} | CAGR {res['CAGR']:6.1%} | DD {res['maxDD']:5.1%} | episodios {res['n']:3d} | "
          f"WR {res['WR']:4.0%} | PF {res['PF']:6.2f} | liquidaciones {res['liq']}")
    for h in SUB:
        print(f"    {h}: rentabilidad {sub[h]:+6.1%} | ocupación {res[f'ocup {h}']:4.0%}")
    return res, sub, d


if __name__ == "__main__" and sys.argv[1] in ("criba", "examen"):
    fase = sys.argv[1]
    PASS = ROOT / "docs/l09_pasan_criba.json"
    part = "desarrollo" if fase == "criba" else "examen"
    out, n = run_x(part)
    print(f"{fase.upper()} — {part}: {n} monedas con datos de HL, top 10 point-in-time, 2023-06 → 2026-10\n")
    ok = []
    for name, (cv, ep) in out.items():
        if fase == "examen" and name not in json.load(open(PASS)):
            continue
        res, sub, d = summarize(name, cv, ep)
        if fase == "criba":
            if res["sharpe"] >= 1.7 and res["PF"] >= 1.3 and all(v > 0 for v in sub.values()):
                ok.append(name)
        else:
            from sclab.stats_tests import deflated_sharpe
            ds = deflated_sharpe(d.to_numpy(), 354, 0.000328)
            good = res["sharpe"] >= 1.0 and res["PF"] >= 1.3 and ds["DSR"] >= 0.90
            print(f"    Deflated Sharpe {ds['DSR']:.3f} -> {'APROBADA' if good else 'NO aprobada'}")
        ep.to_csv(ROOT / f"docs/l09_{fase}_{name[:2]}_episodios.csv", index=False)
    if fase == "criba":
        print("\nPasan la criba:", ok)
        json.dump(ok, open(PASS, "w"), indent=1, ensure_ascii=False)
