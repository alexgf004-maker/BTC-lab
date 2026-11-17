"""Investigación sistemática: IC por variable (paso A) y modelos con validación hacia delante (paso B)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

C_TURN = 0.0007


def _rank_rows(X: np.ndarray) -> np.ndarray:
    """Rangos por fila en [-0.5, 0.5], NaN se conserva."""
    R = np.full_like(X, np.nan, dtype=float)
    for i in range(X.shape[0]):
        m = np.isfinite(X[i])
        n = m.sum()
        if n >= 5:
            R[i, m] = (stats.rankdata(X[i, m]) - 1) / (n - 1) - 0.5
    return R


def ic_table(P: pd.DataFrame, feats: list[str], horizons: dict) -> pd.DataFrame:
    """IC de rangos por fecha (solo miembros), con fechas no solapadas para el estadístico t."""
    M = P[P.miembro]
    rows = []
    piv = {c: M[c].unstack("symbol") for c in feats + [f"fwd_{h}" for h in horizons]}
    times = piv[feats[0]].index
    half = times[len(times) // 2]
    for h, k in horizons.items():
        Y = _rank_rows(piv[f"fwd_{h}"].to_numpy())
        for c in feats:
            X = _rank_rows(piv[c].reindex(times).to_numpy())
            ok = np.isfinite(X) & np.isfinite(Y)
            n = ok.sum(1)
            Xc, Yc = np.where(ok, X, 0), np.where(ok, Y, 0)
            mx, my = Xc.sum(1) / np.maximum(n, 1), Yc.sum(1) / np.maximum(n, 1)
            Xd, Yd = np.where(ok, X - mx[:, None], 0), np.where(ok, Y - my[:, None], 0)
            den = np.sqrt((Xd ** 2).sum(1) * (Yd ** 2).sum(1))
            ic = np.where((n >= 10) & (den > 0), (Xd * Yd).sum(1) / np.where(den > 0, den, 1), np.nan)
            s = pd.Series(ic, index=times).iloc[::k].dropna()          # fechas no solapadas
            if len(s) < 50:
                continue
            t = s.mean() / s.std() * np.sqrt(len(s))
            rows.append({"variable": c, "horizonte": h, "IC": s.mean(), "t": t, "p": 2 * stats.norm.sf(abs(t)),
                         "IC_1a_mitad": s[s.index < half].mean(), "IC_2a_mitad": s[s.index >= half].mean(), "n": len(s)})
    T = pd.DataFrame(rows)
    if T.empty:
        return T
    # Benjamini-Hochberg al 5 %
    o = T.p.sort_values()
    thr = 0.05 * np.arange(1, len(o) + 1) / len(o)
    passed = o.values <= thr
    kmax = np.flatnonzero(passed).max() if passed.any() else -1
    T["significativa"] = False
    if kmax >= 0:
        T.loc[o.index[: kmax + 1], "significativa"] = True
    T["estable"] = np.sign(T.IC_1a_mitad) == np.sign(T.IC_2a_mitad)
    return T.sort_values("t", key=abs, ascending=False)


def cs_transform(M: pd.DataFrame, feats, target):
    """Variables y objetivo a rangos por fecha (neutral al mercado)."""
    g = M.groupby(level="time")
    X = g[feats].rank(pct=True) - 0.5
    y = g[target].rank(pct=True) - 0.5
    return X.fillna(0.0), y


def make_model(kind):
    if kind == "ridge":
        from sklearn.linear_model import Ridge
        return Ridge(alpha=10.0)
    import lightgbm as lgb
    return lgb.LGBMRegressor(n_estimators=300, max_depth=4, num_leaves=15, learning_rate=0.03, subsample=0.7,
                             subsample_freq=1, colsample_bytree=0.7, min_child_samples=200, verbose=-1, n_jobs=4, random_state=0)


def walk_forward(P, feats, horizon: str, k: int, kind: str, mode: str, first_year: int):
    """Devuelve la serie de rentabilidades por periodo (netas) fuera de muestra y la rotación media."""
    M = P[P.miembro].copy()
    tgt = f"fwd_{horizon}"
    if mode == "neutral":
        X, y = cs_transform(M, feats, tgt)
    else:
        X = M[feats].replace([np.inf, -np.inf], np.nan)
        y = (M[tgt] / (M["vol_30d"] * np.sqrt(k))).clip(-5, 5)
    times = M.index.get_level_values("time")
    out, turns = [], []
    w_prev, prev_cols = None, None
    for Y in range(first_year, 2027):
        t0 = pd.Timestamp(f"{Y}-01-01", tz="UTC"); t1 = pd.Timestamp(f"{Y + 1}-01-01", tz="UTC")
        tr = (times < t0 - pd.Timedelta(hours=4 * k)) & y.notna().to_numpy()
        te = (times >= t0) & (times < t1)
        if tr.sum() < 5000 or te.sum() == 0:
            continue
        Xtr, Xte = X[tr], X[te]
        if mode != "neutral":
            lo, hi = Xtr.quantile(0.01), Xtr.quantile(0.99)
            mu, sd = Xtr.clip(lo, hi, axis=1).mean(), Xtr.clip(lo, hi, axis=1).std().replace(0, 1)
            Xtr = ((Xtr.clip(lo, hi, axis=1) - mu) / sd).fillna(0.0)
            Xte = ((Xte.clip(lo, hi, axis=1) - mu) / sd).fillna(0.0)
        model = make_model(kind).fit(Xtr, y[tr])
        pred = pd.Series(model.predict(Xte), index=Xte.index)
        if mode != "neutral":
            ptr = model.predict(Xtr)
            q_lo, q_hi = np.quantile(ptr, 1 / 3), np.quantile(ptr, 2 / 3)
        PR = pred.unstack("symbol")
        cols = PR.columns
        TG = M.loc[te, tgt].unstack("symbol").reindex(index=PR.index, columns=cols).to_numpy()
        FF = M.loc[te, f"ffund_{horizon}"].unstack("symbol").reindex(index=PR.index, columns=cols).fillna(0).to_numpy()
        VO = M.loc[te, "vol_30d"].unstack("symbol").reindex(index=PR.index, columns=cols).to_numpy()
        PRn = PR.to_numpy()
        for i in range(0, len(PR), k):
            ok = np.isfinite(PRn[i]) & np.isfinite(TG[i])
            if ok.sum() < 10:
                continue
            w = np.zeros(len(cols))
            if mode == "neutral":
                idx = np.flatnonzero(ok); order = idx[np.argsort(PRn[i, idx], kind="stable")]
                n = max(2, len(idx) // 5)
                w[order[-n:]] = 0.5 / n; w[order[:n]] = -0.5 / n
            else:
                iv = np.where(ok & (VO[i] > 0), 1 / VO[i], 0.0)
                sgn = np.where(PRn[i] > q_hi, 1.0, np.where(PRn[i] < q_lo, -1.0, 0.0))
                w = np.where(ok, sgn, 0.0) * iv / max(iv.sum(), 1e-12)
            if w_prev is None or len(w_prev) != len(w) or prev_cols is not cols:
                wp = np.zeros(len(cols)) if w_prev is None else pd.Series(w_prev, index=prev_cols).reindex(cols, fill_value=0).to_numpy()
            else:
                wp = w_prev
            turn = np.abs(w - wp).sum()
            tg = np.where(np.isfinite(TG[i]), TG[i], 0.0)
            gross = float((w * tg).sum())
            out.append((PR.index[i], gross - float((w * FF[i]).sum()) - turn * C_TURN, gross)); turns.append(turn)
            w_prev, prev_cols = w, cols
    res = pd.DataFrame(out, columns=["time", "net", "gross"]).set_index("time")
    return res, float(np.mean(turns)) if turns else np.nan


def perf(res: pd.DataFrame, k: int) -> dict:
    ppy = 365 * 6 / k
    r = res["net"]
    eq = (1 + r).cumprod()
    yr = r.groupby(r.index.year).sum()
    return {"sharpe": r.mean() / r.std() * np.sqrt(ppy), "sharpe_bruto": res["gross"].mean() / res["gross"].std() * np.sqrt(ppy),
            "CAGR": eq.iloc[-1] ** (ppy / len(r)) - 1, "maxDD": (1 - eq / eq.cummax()).max(),
            "años_pos": float((yr > 0).mean()), "por_año": yr.round(3).to_dict(), "n": len(r),
            "WR": float((r > 0).mean()), "PF": float(r[r > 0].sum() / -r[r <= 0].sum())}
