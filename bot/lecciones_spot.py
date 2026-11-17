"""Acceso al spot histórico para el modo de reproducción (reutiliza el cargador de la Lección 6)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lecciones"))
from leccion_06_universo import spot_close  # noqa: E402,F401
