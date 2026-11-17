"""Diario de decisiones y ejecuciones (CSV, una línea por evento)."""
import csv
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ["ts", "modo", "bloque", "evento", "symbol", "lado", "cantidad", "precio", "detalle"]


class Journal:
    def __init__(self, path, mode):
        self.path, self.mode = Path(path), mode
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                csv.writer(f).writerow(FIELDS)

    def log(self, sleeve, event, symbol="", side="", qty="", price="", detail="", ts=None):
        ts = ts or datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow([ts, self.mode, sleeve, event, symbol, side, qty, price, detail])
