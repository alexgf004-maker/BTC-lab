"""Carry de funding neutral al mercado: largo en spot + corto en el perpetuo (reglas: docs/leccion_06.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .universe import is_member

SPOT_FEE, PERP_FEE, SLIP = 0.0010, 0.0005, 0.0002
LEG_COST = SPOT_FEE + PERP_FEE + 2 * SLIP          # entrar o salir (dos patas)
REBAL_COST = 2 * (PERP_FEE + SLIP)                  # cerrar y reabrir la pata del perpetuo


def simulate(perp: dict, spot: dict, funding: dict, members: dict, enter=0.0003, exit_=0.00005,
             max_pos=5, slot=0.20, notional_frac=0.75, rebal_move=0.20, highs: dict | None = None,
             liq_move=0.30, liq_penalty=0.015, leg_cost=LEG_COST, rebal_cost=REBAL_COST,
             start="2020-03-01", Hgrid: pd.DataFrame | None = None, Lgrid: pd.DataFrame | None = None,
             ffill_limit: int = 8):
    """Hgrid/Lgrid: máximos/mínimos ya alineados a la rejilla de 8h (si se dan, sustituyen a `highs`).
    Con Lgrid la posición tiene dos patas apalancadas: también se liquida/reequilibra en caídas."""
    """perp/spot: {sym: Serie de cierres 1h}; funding: {sym: Serie de pagos}. Paso de decisión: 8h."""
    grid = pd.date_range(pd.Timestamp(start, tz="UTC"), max(s.index[-1] for s in perp.values()), freq="8h")
    syms = [s for s in perp if s in spot and s in funding]
    P = pd.DataFrame({s: perp[s].reindex(grid, method="ffill", limit=ffill_limit) for s in syms})
    S = pd.DataFrame({s: spot[s].reindex(grid, method="ffill", limit=ffill_limit) for s in syms})
    # funding cobrado entre la decisión anterior y la actual; media de 3 días normalizada a 8h
    F = pd.DataFrame({s: funding[s].groupby((funding[s].index - pd.Timedelta("1min")).ceil("8h")).sum().reindex(grid).fillna(0) for s in syms})
    F3 = F.rolling(9, min_periods=9).sum() / 9
    # máximo intravela del perpetuo en cada tramo de 8h (para detectar liquidaciones de la pata corta)
    H = pd.DataFrame({s: (highs[s] if highs else perp[s]).groupby(highs[s].index.floor("8h") + pd.Timedelta("8h") if highs else perp[s].index.floor("8h") + pd.Timedelta("8h")).max().reindex(grid) for s in syms})
    if Hgrid is not None:
        H = Hgrid.reindex(index=grid, columns=syms)
    Hn = H.to_numpy()
    Ln = Lgrid.reindex(index=grid, columns=syms).to_numpy() if Lgrid is not None else None
    member = pd.DataFrame({s: is_member(members, s, grid) for s in syms}, index=grid)
    equity, cash_eq = 1.0, []
    pos, episodes = {}, []
    Pn, Sn, Fn, F3n, Mn = P.to_numpy(), S.to_numpy(), F.to_numpy(), F3.to_numpy(), member.to_numpy()
    col = {s: i for i, s in enumerate(syms)}
    for g in range(1, len(grid)):
        # 1) devengar PnL de las posiciones abiertas en el paso g-1 -> g
        for s, p in list(pos.items()):
            i = col[s]
            ps, pp = Sn[g, i], Pn[g, i]
            if not (np.isfinite(ps) and np.isfinite(pp)):          # deslistado: cerrar al último precio conocido
                ps, pp = p["last_s"], p["last_p"]
                force = True
            else:
                force = False
            pnl = p["notional"] * ((ps - p["last_s"]) / p["entry_s"] - (pp - p["last_p"]) / p["entry_p"]) + p["notional"] * Fn[g, i] * (pp / p["entry_p"])
            p["pnl"] += pnl; equity += pnl
            p["last_s"], p["last_p"] = ps, pp
            if np.isfinite(Hn[g, i]) and Hn[g, i] > p["ref"] * (1 + liq_move):
                # liquidación de la pata corta: penalización + reabrir la cobertura
                c = p["notional"] * (liq_penalty + rebal_cost); p["pnl"] -= c; equity -= c; p["ref"] = pp; p["liq"] += 1
            elif Ln is not None and np.isfinite(Ln[g, i]) and Ln[g, i] < p["ref"] * (1 - liq_move):
                c = p["notional"] * (liq_penalty + rebal_cost); p["pnl"] -= c; equity -= c; p["ref"] = pp; p["liq"] += 1
            elif pp > p["ref"] * (1 + rebal_move) or (Ln is not None and pp < p["ref"] * (1 - rebal_move)):
                c = p["notional"] * rebal_cost; p["pnl"] -= c; equity -= c; p["ref"] = pp; p["rebal"] += 1
            if force or not (F3n[g, i] > exit_):
                c = p["notional"] * leg_cost; p["pnl"] -= c; equity -= c
                episodes.append({"symbol": s, "entry": p["t0"], "exit": grid[g], "pnl": p["pnl"],
                                 "ret_on_notional": p["pnl"] / p["notional"], "rebal": p["rebal"], "liq": p["liq"]})
                del pos[s]
        # 2) entradas: los de mayor funding primero
        if len(pos) < max_pos:
            cand = [(F3n[g, col[s]], s) for s in syms if s not in pos and Mn[g, col[s]]
                    and F3n[g, col[s]] > enter and np.isfinite(Sn[g, col[s]]) and np.isfinite(Pn[g, col[s]])]
            for _, s in sorted(cand, reverse=True)[: max_pos - len(pos)]:
                i = col[s]
                notional = equity * slot * notional_frac
                c = notional * leg_cost; equity -= c
                pos[s] = {"t0": grid[g], "notional": notional, "pnl": -c, "entry_p": Pn[g, i], "entry_s": Sn[g, i], "ref": Pn[g, i],
                          "last_s": Sn[g, i], "last_p": Pn[g, i], "rebal": 0, "liq": 0}
        cash_eq.append((grid[g], equity, len(pos)))
    curve = pd.DataFrame(cash_eq, columns=["t", "equity", "n_pos"]).set_index("t")
    return curve, pd.DataFrame(episodes)
