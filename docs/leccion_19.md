# Lección 19 — Barrido sistemático de patrones de calendario

## 1. Pre-registro
**Series:** (a) BTC; (b) cesta a partes iguales del universo point-in-time top 30 (absoluta); (c) la misma cesta menos BTC (relativa).
**Desarrollo:** las 218 monedas antiguas (y BTC 2020-01 → 2023-06). **Examen:** las 482 criptos nuevas (y BTC 2023-07 → 2026-10).
**Efectos:** rentabilidad de cada hora del día (24), de cada día de la semana (7) y de los 3 primeros días del mes frente al resto (1)
→ 32 efectos × 3 series = **96 pruebas**. Estadístico: media de la rentabilidad del efecto en cada ocurrencia y t (las ocurrencias son
independientes: un valor por día o por semana). **Benjamini-Hochberg al 5 %** sobre las 96.
**Para ser operable:** significativo en desarrollo, mismo signo y significativo (p < 0,05) en el examen, y media mayor que el coste de
entrar y salir (BTC: 0,09 % con entrada limit; cesta: 0,14 %).
