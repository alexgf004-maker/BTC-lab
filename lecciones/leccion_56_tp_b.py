"""Lección 56 — Take profit en el bloque B (docs/leccion_56.md)."""
import json
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
from leccion_22_validacion import st  # noqa: E402
from leccion_44_bloque_b import BAR, COST, frame  # noqa: E402

VB = {"B actual": {}, "T1 take profit +1R": {"tp": 1}, "T2 take profit +2R": {"tp": 2}, "T3 take profit +3R": {"tp": 3},
      "T4 mitad en +2R, resto con stop dinámico": {"half": 2}, "T5 stop a 2,5 ATR tras +2R": {"tight": 2}}


def trades(df, fund, tp=None, half=None, tight=None, m=5.0):
    o, h, l, c, a = (df[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    t, tns = df.index, df.index.as_unit("ns").asi8
    f_t = fund.index.as_unit("ns").asi8; f_cum = np.concatenate([[0.0], np.cumsum(fund.to_numpy())])
    n, rows, d = len(df), [], -1
    for i in np.flatnonzero(df["sig"].to_numpy()):
        if i + 1 >= n or not (a[i] > 0):
            continue
        j = i + 1; entry = o[j]; R = m * a[i]; stop = entry + R; ext = entry
        legs, part_done, mult = [], False, m
        exit_px, k = None, j
        for k in range(j, n):
            if k > j and o[k] >= stop:
                exit_px = o[k]; break
            if h[k] >= stop:
                exit_px = stop; break
            if tp is not None and l[k] <= entry - tp * R:                 # objetivo (corto en el par: gana si baja)
                exit_px = min(o[k], entry - tp * R) if k > j else entry - tp * R; break
            if half is not None and not part_done and l[k] <= entry - half * R:
                legs.append((min(o[k], entry - half * R) if k > j else entry - half * R, 0.5, k)); part_done = True
            ext = min(ext, l[k])
            if tight is not None and entry - ext >= tight * R:
                mult = 2.5
            stop = min(stop, ext + mult * a[k])
        if exit_px is None:
            exit_px, k = c[n - 1], n - 1
        legs.append((exit_px, 1.0 - sum(w for _, w, _ in legs), k))
        fa_ = np.searchsorted(f_t, tns[j], side="right")
        r = 0.0
        for px, w, kk in legs:
            fb_ = np.searchsorted(f_t, tns[kk] + BAR.value, side="right")
            fsum = f_cum[fb_] - f_cum[fa_]
            r += w * (d * (px - entry) - (entry + px) * COST - d * fsum * entry) / R
        mfe = (entry - ext) / R
        rows.append((t[j], t[k] + BAR, d, entry, R, r, mfe))
    return pd.DataFrame(rows, columns=["entry_time", "exit_time", "side", "entry", "R", "r_net", "mfe"])


def job(args):
    sym, months = args
    btc = data.load("BTCUSDT", "1h")["close"]; f_btc = lab15._funding("BTCUSDT")
    fr = frame(sym, btc, f_btc)
    if fr is None:
        return sym, None, {}
    df, fund = fr
    out = {}
    for name, kw in VB.items():
        T = trades(df, fund, **kw)
        if len(T):
            T = T[universe.is_member(months, sym, pd.DatetimeIndex(T.entry_time))]
            T["symbol"] = sym
        out[name] = T
    return sym, df["close"], out


if __name__ == "__main__":
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    syms = sorted(set(OLD + NEW))
    vol = pd.read_parquet(ROOT / "data" / "vol_diario.parquet")
    mem = universe.monthly_members(vol[[s for s in syms if s in vol]], 30)
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, [(s, mem) for s in syms if s != "BTCUSDT"]))
    closes = {s: c for s, c, _ in res if c is not None}
    fmt = lambda d: f"Sharpe {d['Sharpe']:.2f} | anual {100 * d['CAGR']:+6.1f} % | caída {100 * d['DD']:5.1f} %"
    print("=== Diagnóstico de B actual (todas las operaciones candidatas)")
    A = pd.concat([o["B actual"] for _, c, o in res if c is not None and len(o.get("B actual", []))], ignore_index=True)
    print(f"  operaciones {len(A)} | acierto {100 * (A.r_net > 0).mean():.0f} % | media {A.r_net.mean():+.3f}R")
    for x in (1, 2, 3, 5):
        reach = A[A.mfe >= x]
        print(f"  llegaron a +{x}R en algún momento: {100 * len(reach) / len(A):4.1f} % | de ellas terminaron en pérdida: "
              f"{100 * (reach.r_net < 0).mean():4.1f} % | resultado final medio de esas: {reach.r_net.mean():+.2f}R")
    big = A[A.r_net >= 5]
    print(f"  operaciones que terminaron en ≥ +5R: {100 * len(big) / len(A):.1f} % del total, y aportan "
          f"{100 * big.r_net.sum() / A.r_net.sum():.0f} % del beneficio neto total")
    print(f"  devolución media: las que llegaron a +2R cerraron, de media, en {A[A.mfe >= 2].r_net.mean():+.2f}R "
          f"con una ganancia latente máxima media de {A[A.mfe >= 2].mfe.mean():+.2f}R")
    print("\n=== Cartera B (riesgo 1 %, máximo 10 posiciones)")
    for name in VB:
        cands = pd.concat([o[name] for _, c, o in res if c is not None and name in o and len(o[name])], ignore_index=True)
        daily, tk, _ = lab15._run_portfolio(cands.drop(columns=["mfe"]), closes, 0.01, 10)
        line = f"  {name:42s}"
        for lab, a_, b_ in (("2020–22", "2020-03-01", "2022-12-31"), ("2023–26", "2023-01-01", "2026-10-31")):
            line += f" | {lab}: {fmt(st(daily.loc[a_:b_]))}"
        print(line + f" | operaciones {len(tk)} | E {tk.ret.mean():+.3f}R | acierto {100 * (tk.ret > 0).mean():.0f} %", flush=True)
