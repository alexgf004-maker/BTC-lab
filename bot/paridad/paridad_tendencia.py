import sys, time, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,'.'); sys.path.insert(0,'lecciones')
import pandas as pd
from bot.replay import run_replay
from bot.strategies.trend import Trend
from sclab import trend
from leccion_02_pullback import BAR, prepare
from leccion_03_tendencia import signals
start, end = sys.argv[1], sys.argv[2]
t0 = time.time()
st, s = run_replay(Trend, {"capital": 1.0, "symbols": ["BTCUSDT", "ETHUSDT"]}, start, end)
bot = pd.DataFrame(st.d["sleeves"]["D_tendencia"].get("trades", []))
print(f"bot: {len(bot)} operaciones en {time.time()-t0:.0f}s")
ref = []
for sym in ["BTCUSDT", "ETHUSDT"]:
    df, f = prepare(sym)
    t = trend.simulate(df, signals(df, 120, 1), 5.0, f, bar=BAR); t["symbol"] = sym; ref.append(t)
ref = pd.concat(ref)
ref = ref[(ref.entry_time >= pd.Timestamp(start, tz="UTC")) & (ref.exit_time <= pd.Timestamp(end, tz="UTC"))]
bot["entry_time"] = pd.to_datetime(bot.entry_time, utc=True); bot["exit_time"] = pd.to_datetime(bot.exit_time, utc=True)
k = ["symbol", "entry_time"]
M = ref.merge(bot, on=k, how="outer", suffixes=("_ref", "_bot"), indicator=True)
both = M[M._merge == "both"]
print(f"backtest: {len(ref)} | coinciden en entrada: {len(both)} | solo backtest: {(M._merge=='left_only').sum()} | solo bot: {(M._merge=='right_only').sum()}")
print(f"misma salida: {(both.exit_time_ref == both.exit_time_bot).mean():.1%} | precio de entrada igual: {((both.entry_ref - both.entry_bot).abs() < 1e-6).mean():.1%} | "
      f"precio de salida igual: {((both.exit_ref - both.exit_bot).abs() / both.exit_ref < 1e-9).mean():.1%} | R igual: {((both.R_ref - both.R_bot).abs()/both.R_ref < 1e-6).mean():.1%}")
bad = M[(M._merge != "both") | (M.exit_time_ref != M.exit_time_bot)]
if len(bad): print(bad[["symbol","entry_time","exit_time_ref","exit_time_bot","_merge"]].head(10).to_string(index=False))
