"""Ejecuta el bot hora a hora sobre datos históricos (sin mirar al futuro) para comprobar que decide igual que el backtest."""
from __future__ import annotations

import logging
import tempfile

import pandas as pd

from .broker import PaperBroker
from .journal import Journal
from .market import ReplayMarket
from .state import State


def run_replay(strategy_cls, cfg, start, end, step="4h", slip=0.0):
    tmp = tempfile.mkdtemp()
    st = State(f"{tmp}/state.json")
    mk = ReplayMarket(pd.Timestamp(start, tz="UTC"))
    br = PaperBroker(mk, slip=slip)
    jr = Journal(f"{tmp}/diario.csv", "replay")
    s = strategy_cls(cfg, st, br, mk, jr)
    for now in pd.date_range(pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"), freq=step):
        mk.now = now
        if s.due(now):
            s.run(now)
    return st, s
