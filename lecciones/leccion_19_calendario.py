"""Lección 19: barrido de calendario. Reglas: docs/leccion_19.md"""
import json, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data, universe

def basket(symbols, K=30):
    mem = universe.monthly_members(universe.daily_volume(symbols), K)
    R = pd.DataFrame({s: data.load(s, "1h")["close"].pct_change(fill_method=None) for s in symbols}).clip(-0.5, 0.5)
    months = pd.DatetimeIndex(R.index.tz_localize(None).to_period("M").to_timestamp()).tz_localize("UTC")
    M = pd.DataFrame([[s in mem.get(m, ()) for s in R.columns] for m in months], index=R.index, columns=R.columns)
    return R.where(M).mean(axis=1).dropna()

def effects(r):
    """r: rentabilidades horarias. Devuelve {efecto: serie de una observación por ocurrencia}."""
    out = {}
    lr = np.log1p(r)
    for h in range(24):
        x = lr[lr.index.hour == h]; out[f"hora {h:02d} UTC"] = x
    d = lr.resample("1D").sum(min_count=20).dropna()
    for k, nm in enumerate(["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]):
        out[nm] = d[d.index.dayofweek == k]
    tom = d.groupby(d.index.to_period("M")).apply(lambda x: x[x.index.day <= 3].mean() - x[x.index.day > 3].mean())
    out["3 primeros días del mes (diferencia diaria)"] = tom
    return out

def table(series, label):
    rows = []
    for name, r in series.items():
        for eff, x in effects(r).items():
            x = x.dropna()
            t = x.mean() / x.std() * np.sqrt(len(x))
            rows.append({"serie": name, "efecto": eff, "media": x.mean(), "t": t, "p": 2 * stats.norm.sf(abs(t)), "n": len(x)})
    T = pd.DataFrame(rows)
    o = T.p.sort_values(); thr = 0.05 * np.arange(1, len(o) + 1) / len(o); ok = o.values <= thr
    T["BH"] = False
    if ok.any(): T.loc[o.index[: np.flatnonzero(ok).max() + 1], "BH"] = True
    return T

if __name__ == "__main__":
    OLD = json.load(open(ROOT / "docs/l11_universo.json"))["todos"]
    NEW = json.load(open(ROOT / "docs/l15_filtro.json"))["cripto"]
    btc = data.load("BTCUSDT", "1h")["close"].pct_change().dropna()
    cut = pd.Timestamp("2023-07-01", tz="UTC")
    bo, bn = basket(OLD), basket(NEW)
    bt = btc.reindex(bo.index); btn = btc.reindex(bn.index)
    dev = table({"BTC": btc[btc.index < cut], "cesta": bo, "cesta − BTC": (bo - bt).dropna()}, "dev")
    exa = table({"BTC": btc[btc.index >= cut], "cesta": bn, "cesta − BTC": (bn - btn).dropna()}, "exam")
    M = dev.merge(exa, on=["serie", "efecto"], suffixes=("_dev", "_exam"))
    cost = M.serie.map({"BTC": 0.0009}).fillna(0.0014)
    M["operable"] = M.BH_dev & (np.sign(M.media_dev) == np.sign(M.media_exam)) & (M.p_exam < 0.05) & (M.media_exam.abs() > cost)
    M.to_csv(ROOT / "docs/l19_calendario.csv", index=False)
    print(f"96 pruebas | significativas en desarrollo (BH 5 %): {int(M.BH_dev.sum())} | además replicadas en examen (mismo signo, p<0,05): "
          f"{int((M.BH_dev & (np.sign(M.media_dev)==np.sign(M.media_exam)) & (M.p_exam<0.05)).sum())} | operables tras costes: {int(M.operable.sum())}\n")
    show = M[M.BH_dev | (M.p_exam < 0.01)].sort_values("t_dev", key=abs, ascending=False)
    fm = {c: "{:+.3%}".format for c in ["media_dev", "media_exam"]}
    fm.update({c: "{:+.1f}".format for c in ["t_dev", "t_exam"]})
    print(show[["serie", "efecto", "media_dev", "t_dev", "BH_dev", "media_exam", "t_exam", "operable"]].to_string(index=False, formatters=fm))
