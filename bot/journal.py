"""Diario de decisiones y ejecuciones (CSV, una línea por evento)."""
import csv
from datetime import datetime, timezone
from pathlib import Path

from .mensajes import formatear

FIELDS = ["ts", "modo", "bloque", "evento", "symbol", "lado", "cantidad", "precio", "detalle"]


class Journal:
    def __init__(self, path, mode, notifier=None):
        self.path, self.mode, self.notifier = Path(path), mode, notifier
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                csv.writer(f).writerow(FIELDS)

    def log(self, sleeve, event, symbol="", side="", qty="", price="", detail="", ts=None):
        ts = ts or datetime.now(timezone.utc).isoformat(timespec="seconds")
        with open(self.path, "a", newline="") as f:
            csv.writer(f).writerow([ts, self.mode, sleeve, event, symbol, side, qty, price, detail])
        if self.notifier is not None and event in getattr(self.notifier, "important", ()):
            try:
                text = formatear(self.mode, sleeve, event, symbol, side, qty, price, detail, ts)
            except Exception:                                   # un fallo al redactar nunca impide avisar
                text = f"{self.mode} · {sleeve} · {event} {symbol} {side} {qty} @ {price} {detail}".strip()
            self.notifier.send(text, raw=True)
