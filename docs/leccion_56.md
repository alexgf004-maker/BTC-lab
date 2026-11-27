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
