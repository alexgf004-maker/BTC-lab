"""Lección 38 — Modelo ICT en el Nasdaq 100: tomas de liquidez + ventanas macro + IFVG (docs/leccion_38.md)."""
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
COST_PTS, MIN_RISK = 0.75, 5.0
WINDOWS = [((9, 50), (10, 10)), ((10, 50), (11, 10))]


def load():
    parts = []
    for f in sorted((ROOT / "data/histdata").glob("NSXUSD_*.zip")):
        with zipfile.ZipFile(f) as z:
            name = [n for n in z.namelist() if n.endswith(".csv")][0]
            parts.append(pd.read_csv(io.BytesIO(z.read(name)), sep=";", header=None, names=["t", "open", "high", "low", "close", "v"]))
    d = pd.concat(parts)
    t = (pd.to_datetime(d.t, format="%Y%m%d %H%M%S") + pd.Timedelta("5h")).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    df = d[["open", "high", "low", "close"]].set_index(pd.DatetimeIndex(t)).sort_index()
    return df[~df.index.duplicated()]


def minutes(ix):
    return ix.hour * 60 + ix.minute


def run(df, k_target):
    out = []
    days = pd.Series(df.index.normalize()).unique()
    m_all = minutes(df.index)
    by_day = {d: g for d, g in df.groupby(df.index.normalize())}
    for i in range(1, len(days)):
        D, prev = days[i], days[i - 1]
        if D.dayofweek >= 5 or D not in by_day:
            continue
        g = by_day[D]; gp = by_day.get(prev)
        mm = minutes(g.index)
        asia = gp[minutes(gp.index) >= 20 * 60] if gp is not None and (D - prev).days <= 3 else None
        lon = g[(mm >= 120) & (mm < 300)]
        pre = g[(mm >= 480) & (mm < 570)]
        sess = g[(mm >= 570) & (mm < 960)]
        if len(sess) < 300 or len(lon) < 60 or len(pre) < 45 or asia is None or len(asia) < 60:
            continue
        H = [asia.high.max(), lon.high.max(), pre.high.max()]
        L = [asia.low.min(), lon.low.min(), pre.low.min()]
        o, h, l, c = (sess[x].to_numpy() for x in ("open", "high", "low", "close"))
        sm = minutes(sess.index)
        swept_h, swept_l, last_side = set(), set(), 0
        hi_run, lo_run = -np.inf, np.inf
        bull, bear = [], []                                   # FVG activos: borde inferior (alcista) / superior (bajista)
        done_win = set()
        j = 0
        while j < len(sess):
            hi_run, lo_run = max(hi_run, h[j]), min(lo_run, l[j])
            for q, lv in enumerate(H):
                if q not in swept_h and h[j] > lv:
                    swept_h.add(q); last_side = -1
            for q, lv in enumerate(L):
                if q not in swept_l and l[j] < lv:
                    swept_l.add(q); last_side = 1
            if j >= 2:
                if l[j] > h[j - 2]:
                    bull.append(h[j - 2])
                if h[j] < l[j - 2]:
                    bear.append(l[j - 2])
            inv_bull = [b for b in bull if c[j] < b]
            inv_bear = [b for b in bear if c[j] > b]
            bull = [b for b in bull if c[j] >= b]
            bear = [b for b in bear if c[j] <= b]
            win = next((w for w, ((a1, a2), (b1, b2)) in enumerate(WINDOWS) if a1 * 60 + a2 <= sm[j] < b1 * 60 + b2), None)
            trade = None
            if win is not None and win not in done_win:
                if last_side == -1 and inv_bull:
                    trade = (-1, c[j], hi_run)
                elif last_side == 1 and inv_bear:
                    trade = (1, c[j], lo_run)
            if trade:
                side, entry, stop = trade
                risk = abs(entry - stop)
                if risk >= MIN_RISK and (stop - entry) * side < 0:
                    done_win.add(win)
                    target = entry + side * k_target * risk
                    res, kind = None, "tiempo"
                    for k in range(j + 1, len(sess)):
                        if (side == -1 and h[k] >= stop) or (side == 1 and l[k] <= stop):
                            res, kind = -risk, "stop"; break
                        if (side == -1 and l[k] <= target) or (side == 1 and h[k] >= target):
                            res, kind = k_target * risk, "objetivo"; break
                    if res is None:
                        res = side * (c[-1] - entry)
                    out.append((sess.index[j], side, (res - COST_PTS) / risk, kind, risk, (res - COST_PTS) / entry))
            j += 1
    return pd.DataFrame(out, columns=["t", "side", "R", "kind", "risk", "ret"])


def stats(T, label):
    if T.empty:
        print(f"{label}: sin operaciones"); return
    d = T.groupby(T.t.dt.date).R.mean()
    t = d.mean() / d.std() * np.sqrt(len(d))
    pf = T.R[T.R > 0].sum() / -T.R[T.R < 0].sum()
    print(f"{label:30s} n {len(T):5d} | E {T.R.mean():+.3f}R (t {t:+5.2f}) | acierto {100 * (T.R > 0).mean():4.1f} % | PF {pf:.2f} | "
          f"riesgo medio {T.risk.mean():.1f} pts | por operación {100 * T.ret.mean():+.3f} % del índice")


if __name__ == "__main__":
    df = load()
    print("datos:", df.index[0], "→", df.index[-1], len(df), "minutos")
    for name, k in (("Z1 ICT 1:1", 1.0), ("Z2 ICT 2:1", 2.0)):
        T = run(df, k)
        T.to_csv(ROOT / f"docs/l38_{name[:2]}.csv", index=False)
        print(f"\n=== {name}")
        y = T.t.dt.year
        stats(T[y <= 2019], "desarrollo 2012–2019")
        stats(T[y >= 2020], "EXAMEN 2020–2026")
        stats(T[(y >= 2021) & (y <= 2025)], "  periodo de la publicación 2021–2025")
        print("  por año:", {int(a): f"{g.R.mean():+.2f}R/{100 * (g.R > 0).mean():.0f}%" for a, g in T.groupby(y)})
