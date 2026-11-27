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

## 2. Resultados — `l56_salida.txt`
**Diagnóstico (17.182 operaciones candidatas de B, 2020–2026):** acierto 42 %, media +0,117R.
| La operación llegó a… | % de operaciones | De ellas, terminaron en pérdida | Resultado final medio |
|---|---|---|---|
| +1R | 39,6 % | 7,8 % | +1,13R |
| +2R | 17,3 % | 0,3 % | +2,06R |
| +3R | 8,6 % | 0,0 % | +2,84R |
| +5R | 1,9 % | 0,0 % | +4,62R |
Las que llegan a +2R tienen una ganancia latente máxima media de +3,37R y cierran en +2,06R: **devuelven ~1,3R**. La observación
del usuario es correcta. Pero el 0,6 % de operaciones que acaban en ≥ +5R aporta **un tercio de todo el beneficio**: un take profit
fijo las corta.

| Variante | 2020–22: Sharpe / caída | 2023–26: Sharpe / caída | E por operación |
|---|---|---|---|
| B actual | 1,56 / 30,4 % | 0,82 / 33,8 % | +0,147R |
| T1 take profit +1R | 1,19 / 32,9 % | 0,36 / 46,2 % | +0,053R |
| T2 take profit +2R | 1,35 / 31,3 % | 0,68 / 38,8 % | +0,099R |
| T3 take profit +3R | 1,52 / 30,0 % | 0,92 / 33,3 % | +0,140R |
| T4 mitad en +2R | 1,36 / 30,8 % | 0,83 / 33,4 % | +0,133R |
| **T5 stop a 2,5 ATR tras +2R** | **1,68 / 29,2 %** | **0,97 / 32,7 %** | **+0,152R** |

**T5 aprobada:** mejor Sharpe en las dos mitades y menor caída. Los take profits fijos (T1–T4) empeoran B: cuanto más cerca el
objetivo, peor. La solución a "devuelve ganancias" no es cerrar en un precio fijo, sino **apretar el stop cuando la operación ya va
+2R**: se protege más ganancia sin cortar las operaciones enormes.

**Robustez año por año** (cartera B completa, rentabilidad anual):
| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| B actual | +113,6 % | −18,4 % | +160,1 % | +40,0 % | +96,6 % | +30,4 % | −27,3 % |
| T5 | +116,2 % | −12,2 % | +168,1 % | +48,9 % | +123,7 % | +36,0 % | −27,3 % |
Mejor en 6 de 7 años (2026 igual).

**Doble comprobación con el código del bot** (repetición hora a hora de 2022, muestra de 25 monedas): las 157 operaciones (B actual)
y las 172 (T5) del bot coinciden con el simulador en la entrada y en la hora de salida al 100 %. En esa muestra pequeña T5 ganó menos
(+24 % frente a +32 %), pero en el universo completo de ese año ganó más (+168 % frente a +160 %): diferencia de muestra, no de
mecánica.

**Activado en el bot:** B aprieta su stop dinámico de 5 a 2,5 ATR cuando la operación llega a +2R (`asegurar_tras_R: 2.0`,
`m_asegurado: 2.5`; se puede apagar con `asegurar_tras_R: 0`). No se añade take profit fijo.
