"""Estado persistente del bot (JSON con escritura atómica). Sobrevive a reinicios sin duplicar posiciones."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


class State:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.d = json.loads(self.path.read_text()) if self.path.exists() else {
            "sleeves": {}, "equity_peak": None, "halted": False, "last_run": {}, "version": 1}

    def sleeve(self, name, capital):
        s = self.d["sleeves"].setdefault(name, {"balance": capital, "positions": {}, "closed": 0, "pnl": 0.0})
        return s

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".state")
        with os.fdopen(fd, "w") as f:
            json.dump(self.d, f, indent=1, default=str)
        os.replace(tmp, self.path)
