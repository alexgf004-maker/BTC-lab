"""Lección 34 — Forex G10: carry, tendencia, valor y combinación (docs/leccion_34.md)."""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
FX = ROOT / "data/fx"
CCY = {  # serie FRED, ¿cotiza como USD por unidad?, códigos de tipos, código BIS, diferencial por lado
    "EUR": ("DEXUSEU", True, ["IR3TIB01EZM156N", "IRSTCI01EZM156N"], "RBXMBIS", 1e-4),
    "JPY": ("DEXJPUS", False, ["IR3TIB01JPM156N", "IRSTCI01JPM156N", "INTDSRJPM193N"], "RBJPBIS", 1e-4),
    "GBP": ("DEXUSUK", True, ["IR3TIB01GBM156N", "IRSTCI01GBM156N"], "RBGBBIS", 1e-4),
    "CHF": ("DEXSZUS", False, ["IR3TIB01CHM156N", "IRSTCI01CHM156N"], "RBCHBIS", 1e-4),
    "CAD": ("DEXCAUS", False, ["IR3TIB01CAM156N", "IRSTCI01CAM156N"], "RBCABIS", 1e-4),
    "AUD": ("DEXUSAL", True, ["IR3TIB01AUM156N", "IRSTCI01AUM156N"], "RBAUBIS", 1e-4),
    "NZD": ("DEXUSNZ", True, ["IR3TIB01NZM156N", "IRSTCI01NZM156N"], "RBNZBIS", 2e-4),
    "SEK": ("DEXSDUS", False, ["IR3TIB01SEM156N", "IRSTCI01SEM156N"], "RBSEBIS", 5e-4),
    "NOK": ("DEXNOUS", False, ["IR3TIB01NOM156N", "IRSTCI01NOM156N"], "RBNOBIS", 5e-4),
}
USD_RATE = ["IR3TIB01USM156N", "IRSTCI01USM156N"]


def fred(id_):
    d = pd.read_csv(FX / f"{id_}.csv")
    s = pd.to_numeric(d.iloc[:, 1], errors="coerce")
    s.index = pd.to_datetime(d.iloc[:, 0])
    return s.dropna()


def rate(ids):
    out = None
    for i in ids:
        s = fred(i).resample("ME").last()
        out = s if out is None else out.combine_first(s)
    return out


def load():
    spot, rates, reer, spread = {}, {}, {}, {}
    for c, (sid, usd_per, rids, bis, sp) in CCY.items():
        s = fred(sid).resample("ME").last()
        spot[c] = s if usd_per else 1 / s
        rates[c] = rate(rids)
        reer[c] = fred(bis).resample("ME").last()
        spread[c] = sp
    S, I, V = pd.DataFrame(spot), pd.DataFrame(rates), pd.DataFrame(reer)
    iu = rate(USD_RATE)
    idx = S.index[S.index >= "1980-01-31"]
    S, I, V, iu = S.reindex(idx), I.reindex(idx).ffill(limit=12), V.reindex(idx), iu.reindex(idx).ffill(limit=12)
    diff = I.sub(iu, axis=0) / 100
    R = (S.shift(-1) / S - 1) + diff / 12            # rentabilidad del mes siguiente de estar largo (con carry)
    return S, diff, V, R, pd.Series(spread)


def xs_weights(score, n=3):
    W = pd.DataFrame(0.0, index=score.index, columns=score.columns)
    for t, row in score.iterrows():
        r = row.dropna()
        if len(r) < 2 * n:
            continue
        W.loc[t, r.nlargest(n).index] = 1 / (2 * n)
        W.loc[t, r.nsmallest(n).index] = -1 / (2 * n)
    return W


def strategies(S, diff, V, R):
    carry = xs_weights(diff)
    past12 = (1 + R.shift(1)).rolling(12).apply(np.prod, raw=True) - 1          # 12 meses hasta el mes actual
    vol3 = R.shift(1).rolling(3, min_periods=3).std() * np.sqrt(12)
    dvol = (np.log(S).diff()).rolling(3).std() * np.sqrt(12)                     # vol. con el mes actual (datos diarios no; mensual)
    vol = vol3.fillna(dvol)
    n = R.notna().sum(axis=1).replace(0, np.nan)
    trend = (np.sign(past12) * (0.10 / vol)).div(n, axis=0).where(R.notna()).fillna(0)
    trend = trend.clip(-1, 1)
    dev = np.log(V.shift(1)) - np.log(V.shift(1)).rolling(60, min_periods=48).mean()
    value = xs_weights(-dev)
    return {"F1 carry": carry, "F2 tendencia": trend, "F3 valor": value}


def run(W, R, spread, markup):
    W = W.reindex(R.index).fillna(0)
    gross = (W * R.fillna(0)).sum(axis=1)
    turn = (W.diff().abs().fillna(W.abs()) * spread).sum(axis=1)
    fin = W.abs().sum(axis=1) * markup / 12
    return gross - turn - fin, W.abs().sum(axis=1)


def scaled(W, R, target=0.10, look=36):
    g = (W.reindex(R.index).fillna(0) * R.fillna(0)).sum(axis=1)
    vol = g.shift(1).rolling(look, min_periods=24).std() * np.sqrt(12)       # solo meses ya cerrados
    k = (target / vol).clip(upper=20)
    return W.mul(k, axis=0)


def stats(r, lev=None):
    r = r.dropna()
    eq = (1 + r).cumprod()
    out = dict(anual=eq.iloc[-1] ** (12 / len(r)) - 1, sharpe=r.mean() / r.std() * np.sqrt(12), dd=(1 - eq / eq.cummax()).max(),
               peor_mes=r.min(), meses=len(r))
    if lev is not None:
        out["apal_medio"], out["apal_max"] = lev.mean(), lev.max()
    return out


def fmt(d):
    s = f"anual {100 * d['anual']:+6.1f} % | Sharpe {d['sharpe']:5.2f} | caída {100 * d['dd']:5.1f} % | peor mes {100 * d['peor_mes']:+5.1f} %"
    if "apal_medio" in d:
        s += f" | apalancamiento medio {d['apal_medio']:.1f}x (máx {d['apal_max']:.1f}x)"
    return s


if __name__ == "__main__":
    S, diff, V, R, spread = load()
    raw = strategies(S, diff, V, R)
    sc = {k: scaled(w, R) for k, w in raw.items()}
    unit = {k: (w.reindex(R.index).fillna(0) * R.fillna(0)).sum(axis=1) for k, w in sc.items()}
    avail = pd.DataFrame({k: (sc[k].abs().sum(axis=1) > 0) for k in sc})
    comb = sum(sc[k].mul(avail[k], axis=0) for k in sc).div(avail.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    sc["F4 combinación"] = scaled(comb, R)
    periods = {"F1 carry": (("1985", "2005"), ("2006", "2026-10")), "F2 tendencia": (("1985", "2005"), ("2006", "2026-10")),
               "F3 valor": (("1999", "2010"), ("2011", "2026-10")), "F4 combinación": (("1985", "2005"), ("2006", "2026-10"))}
    res = {}
    for name, W in sc.items():
        for label, sp, mk in (("CFD minorista", spread, 0.01), ("Interactive Brokers", spread * 0 + 0.2e-4, 0.0025)):
            net, lev = run(W, R, sp, mk)
            res[(name, label)] = net
            (d0, d1), (e0, e1) = periods[name]
            print(f"{name:15s} {label:20s} DESARROLLO {d0}-{d1}: {fmt(stats(net.loc[d0:d1], lev.loc[d0:d1]))}")
            print(f"{'':15s} {'':20s} EXAMEN     {e0}-{e1}: {fmt(stats(net.loc[e0:e1], lev.loc[e0:e1]))}")
        g, _ = run(W, R, spread * 0, 0.0)
        print(f"{'':15s} sin costes, examen: Sharpe {stats(g.loc[periods[name][1][0]:periods[name][1][1]])['sharpe']:.2f}")
    f4 = res[("F4 combinación", "CFD minorista")]
    print("\nF4 por década (CFD):", {f"{y}s": f"{100 * ((1 + g).prod() ** (12 / len(g)) - 1):+.1f}%/año" for y, g in f4.loc["1985":].groupby((f4.loc['1985':].index.year // 10) * 10)})
    print("F4 últimos años (CFD):", {y: f"{100 * ((1 + g).prod() - 1):+.1f}%" for y, g in f4.loc["2018":].groupby(f4.loc['2018':].index.year)})
    # correlación con la cartera de cripto
    C = pd.read_csv(ROOT / "docs/l17_bloques_diarios.csv", index_col=0, parse_dates=True)
    a = C["A carry"]; C["A carry"] = a - a.mean() + (1.036 ** (1 / 365.25) - 1)
    cm = (1 + C.mean(axis=1)).resample("ME").prod() - 1
    cm.index = cm.index.tz_localize(None)
    j = pd.concat([cm, f4], axis=1, keys=["cripto", "forex"]).dropna().loc["2020-03":"2026-10"]
    print(f"\nCorrelación mensual cartera cripto vs F4 forex (2020-03 → 2026-10): {j.corr().iloc[0, 1]:+.2f}")
    print(f"Mismo periodo: cripto {fmt(stats(j.cripto))}")
    print(f"               forex  {fmt(stats(j.forex))}")
    mix = 0.75 * j.cripto + 0.25 * j.forex
    print(f"               75 % cripto + 25 % forex: {fmt(stats(mix))}")
    f4.to_csv(ROOT / "docs/l34_F4_mensual.csv")
