"""Lección 29 — R1: rebote en números redondos finos solo en días tranquilos (eventos de la Lección 26)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from sclab import data  # noqa: E402


def calm_flags(E):
    out = []
    for sym, g in E.groupby("symbol"):
        c = data.load(sym, "1h")["close"]
        r = np.log(c).diff()
        v24 = r.rolling(24).std()
        med = v24.rolling(24 * 30, min_periods=24 * 20).median()
        calm = (v24 < med).shift(1)                       # solo información anterior a la vela del toque
        out.append(pd.Series(calm.reindex(g.t).to_numpy(), index=g.index))
    return pd.concat(out).reindex(E.index)


def run(fase):
    E = pd.read_parquet(ROOT / f"data/cache/l26_{fase}.parquet")
    E["t"] = pd.to_datetime(E.t, utc=True)
    E = E[(E.familia == "redondo_fino") & E.r.notna()].copy()
    if "clase" in E:
        E = E[E.clase != "acciones"] if "acciones" in set(E.clase) else E
    E["calm"] = calm_flags(E).astype("boolean")
    E["day"] = E.t.dt.floor("1D")
    print(f"\n=== {fase.upper()} ({E.symbol.nunique()} monedas)")
    for tipo in ("real", "placebo"):
        g = E[E.tipo == tipo]
        for label, sel in (("todos los toques", g), ("días tranquilos", g[g.calm == True]),
                           ("tranquilos + primer toque del día", g[g.calm == True].sort_values("t").groupby(["symbol", "day"]).head(1))):
            r = sel.r
            d = sel.groupby("day").r.mean()
            print(f"{tipo:8s} {label:34s} n {len(r):6d} | E {r.mean():+.3f}R (t op. {r.mean() / r.std() * np.sqrt(len(r)):+.1f}) | "
                  f"acierto {100 * (r > 0).mean():.1f} % | por día E {d.mean():+.3f} t {d.mean() / d.std() * np.sqrt(len(d)):+.1f} ({len(d)} días)")


if __name__ == "__main__":
    for f in ("desarrollo", "examen"):
        run(f)
