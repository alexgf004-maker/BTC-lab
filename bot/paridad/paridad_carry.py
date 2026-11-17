import sys, json, time, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0,'.'); sys.path.insert(0,'lecciones')
import pandas as pd
from bot.replay import run_replay
from bot.strategies.carry import Carry
from sclab import carry, data, universe
from leccion_06_universo import spot_close
start, end = sys.argv[1], sys.argv[2]
OLD = json.load(open("docs/l11_universo.json"))["todos"]
syms = [s for s in sorted(OLD) if spot_close(s) is not None][::4]
mem = universe.monthly_members(universe.daily_volume(syms), 20)
def uni(now): return sorted(mem.get(pd.Timestamp(now.year, now.month, 1, tz="UTC"), set()))
class A(Carry):
    def __init__(self, cfg, state, broker, market, journal): super().__init__(cfg, state, broker, market, journal, uni, direction=1)
t0 = time.time()
st, s = run_replay(A, {"capital": 1.0}, start, end, step="8h")
bot = pd.DataFrame(st.d["sleeves"]["A_carry"].get("trades", []))
print(f"bot: {len(bot)} episodios en {time.time()-t0:.0f}s ({len(syms)} monedas)")
perp = {s_: data.load(s_, "1h")["close"] for s_ in syms}; spot = {s_: spot_close(s_) for s_ in syms}; fund = {s_: data.load_funding(s_) for s_ in syms}
cv, ep = carry.simulate(perp, spot, fund, mem, enter=0.00015, exit_=0.00005, max_pos=4, slot=0.25, notional_frac=2/3)
ep = ep[(ep.entry >= pd.Timestamp(start, tz="UTC")) & (ep.exit <= pd.Timestamp(end, tz="UTC"))].rename(columns={"entry": "entry_time", "exit": "exit_time"})
bot["entry_time"] = pd.to_datetime(bot.entry_time, utc=True); bot["exit_time"] = pd.to_datetime(bot.exit_time, utc=True)
M = ep.merge(bot, on=["symbol", "entry_time"], how="outer", suffixes=("_ref", "_bot"), indicator=True)
both = M[M._merge == "both"]
print(f"backtest: {len(ep)} | coinciden: {len(both)} | solo backtest: {(M._merge=='left_only').sum()} | solo bot: {(M._merge=='right_only').sum()} | misma salida: {(both.exit_time_ref == both.exit_time_bot).mean():.1%}")
print(f"rendimiento sobre el nocional (media): backtest {both.ret_on_notional.mean():+.3%} | bot {(both.pnl_bot / (0.25*2/3)).mean():+.3%} (aprox.)")
bad = M[(M._merge != "both") | (M.exit_time_ref != M.exit_time_bot)]
print("episodios del backtest abiertos al empezar:", len(cv[cv.index == pd.Timestamp(start, tz='UTC')]), "| n_pos al empezar:", int(cv.n_pos.asof(pd.Timestamp(start, tz='UTC'))))
if len(bad): print(bad[["symbol","entry_time","exit_time_ref","exit_time_bot","_merge"]].head(10).to_string(index=False))
