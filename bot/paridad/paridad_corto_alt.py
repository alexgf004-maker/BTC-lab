import sys, json, time, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,'.')
import pandas as pd
from bot.replay import run_replay
from bot.strategies.weak_alts import WeakAlts
from sclab import lab15, universe
start, end = sys.argv[1], sys.argv[2]
OLD = json.load(open("docs/l11_universo.json"))["todos"]
syms = ["BTCUSDT"] + sorted(OLD)[::9]                       # muestra de ~25 monedas
mem = universe.monthly_members(universe.daily_volume(syms), 30)
def uni(now): return mem.get(pd.Timestamp(now.year, now.month, 1, tz="UTC"), set())
class W(WeakAlts):
    def __init__(self, cfg, state, broker, market, journal): super().__init__(cfg, state, broker, market, journal, uni)
t0 = time.time()
st, s = run_replay(W, {"capital": 1.0}, start, end, step="1h")
bot = pd.DataFrame(st.d["sleeves"]["B_corto_alt_btc"].get("trades", []))
print(f"bot: {len(bot)} operaciones cerradas ({len(st.d['sleeves']['B_corto_alt_btc']['positions'])} abiertas) en {time.time()-t0:.0f}s, {len(syms)} monedas")
d, tk, _ = lab15.s1_relative_weakness(syms, K=30)
tk["entry_time"] = pd.to_datetime(tk.entry_time, utc=True); tk["exit_time"] = pd.to_datetime(tk.exit_time, utc=True)
ref = tk[(tk.entry_time >= pd.Timestamp(start, tz="UTC")) & (tk.exit_time <= pd.Timestamp(end, tz="UTC"))]
bot["entry_time"] = pd.to_datetime(bot.entry_time, utc=True); bot["exit_time"] = pd.to_datetime(bot.exit_time, utc=True)
M = ref.merge(bot, on=["symbol", "entry_time"], how="outer", suffixes=("_ref", "_bot"), indicator=True)
both = M[M._merge == "both"]
print(f"backtest: {len(ref)} | coinciden: {len(both)} | solo backtest: {(M._merge=='left_only').sum()} | solo bot: {(M._merge=='right_only').sum()}")
print(f"misma salida: {(both.exit_time_ref == both.exit_time_bot).mean():.1%} | R igual: {((both.R_ref - both.R_bot).abs()/both.R_ref < 1e-6).mean():.1%}")
bad = M[(M._merge != "both") | (M.exit_time_ref != M.exit_time_bot)]
if len(bad): print(bad[["symbol","entry_time","exit_time_ref","exit_time_bot","_merge"]].head(12).to_string(index=False))
ex = M[M._merge == "right_only"]
for r in ex.itertuples():
    t = r.entry_time; inpos = ref[(ref.entry_time <= t) & (ref.exit_time > t)]
    print(f"  extra del bot {r.symbol} {t}: posiciones abiertas en el backtest en ese momento = {len(inpos)}; ¿el backtest tenía ese símbolo abierto? {r.symbol in set(inpos.symbol)}")
