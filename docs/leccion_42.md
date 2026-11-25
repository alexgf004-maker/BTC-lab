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

## 2. Resultados — `l42_salida.txt`
**H1 — Motor A en altcoins: RECHAZADO.** Desarrollo −0,00R (t −1,6, n 2 036); examen +0,18R de media pero t −1,2 (n 1 707), con solo un
17–19 % de aciertos: la media la sostienen unas pocas subidas enormes y el día típico pierde. En altcoins, una subida brusca con pico de
actividad suele ser un "pump" que se deshace. **El bloque G se queda en BTC, ETH y SOL**, donde sí funciona (examen +0,73R, n 199).
**H2 — Espejo bajista: RECHAZADO.** En BTC/ETH/SOL +0,03R / +0,15R con t ≈ 0; en altcoins, negativo en desarrollo. Las caídas bruscas con
pánico no continúan de forma fiable (coherente con la Lección 8: tras las cascadas de liquidación hay rebotes).
**H3 — Filtro anticapitulación para B: RECHAZADO.** 2020–2022: Sharpe 1,56 → 1,60 y caída 30 % → 26 %; 2023–2026: Sharpe 0,82 → 0,78 y caída
34 % → 38 %. Mejora una mitad y empeora la otra: no es una mejora estable. B se mantiene sin filtro.
