# Lección 42 — Ampliar y reforzar lo que funciona (motor A, su espejo bajista y un filtro para B)

## 1. Pre-registro (antes de calcular resultados)
Datos: velas de 1 h de los perpetuos de Binance (incluyen el número de operaciones). Universo de altcoins: las 20 más líquidas de cada
mes (point-in-time, con deslistadas), excluidos BTC, ETH y SOL (ya usados en la Lección 40).
**Desarrollo 2020-03 → 2023-06; examen 2023-07 → 2026-10.**

**H1 — Motor A (bloque G) en altcoins:** reglas idénticas (subida de 3 h > 1,5 %, z-score de operaciones > 3,936 frente a 168 h,
cierre > EMA200, vela alcista; stop 1,5 ATR; control a 6 h; máximo 60 h; coste 0,24 % por operación como en el monitor).
Criterio: E[R] > 0 con t ≥ 3 en el examen (operaciones agrupadas por día) y positiva en desarrollo.
**H2 — Espejo bajista del motor A:** caída de 3 h > 1,5 %, z-score > 3,936, cierre < EMA200, vela bajista → corto a la apertura siguiente;
stop 1,5 ATR por encima; control a 6 h (si va en contra, fuera); máximo 60 h. En BTC, ETH, SOL y las altcoins de H1. Mismo criterio.
**H3 — Filtro anticapitulación para el bloque B:** no abrir cortos nuevos si BTC ha caído más de un 10 % en las 72 h previas.
Criterio: Sharpe de B mayor en las dos mitades y caída máxima de B no mayor.
Pruebas nuevas: 3.
