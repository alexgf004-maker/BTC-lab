# Lección 56 — ¿Le falta un take profit al bloque B?

Observación del usuario siguiendo el bot: las operaciones de B (corto altcoin / largo BTC) suelen ir ganando bastante y nunca
cierran: el stop dinámico (5 ATR) devuelve parte de la ganancia. Propuesta: añadir un take profit.

## 1. Pre-registro (subido antes de calcular)
Simulador del bloque B de la L44 (velas de 4 h del par altcoin/BTC, riesgo 1 %, máximo 10 posiciones, top 30, costes y funding).
R = distancia inicial al stop (5 ATR). "Ganancia latente máxima" = la mejor ganancia que llegó a tener la operación.

**Diagnóstico (descriptivo):** distribución de la ganancia latente máxima y del resultado final; cuántas operaciones llegan a
+1R, +2R y +3R y cuántas de esas terminan en pérdida; qué parte del beneficio total aportan las operaciones de más de +5R.

**Variantes:**
- **T1:** take profit en +1R.
- **T2:** take profit en +2R.
- **T3:** take profit en +3R.
- **T4:** cierra la mitad en +2R; la otra mitad sigue con el stop dinámico.
- **T5:** sin take profit, pero tras llegar a +2R el stop dinámico se aprieta de 5 a 2,5 ATR ("asegurar ganancia").

Criterio (el de la L44): Sharpe mayor que B actual en las dos mitades (2020-03 → 2022-12 y 2023-01 → 2026-10) y caída máxima no
mayor. Pruebas nuevas: 5.
