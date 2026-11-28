# Lección 58 — ¿Qué tienen en común las operaciones perdedoras del bloque B?

Mismo método que la L57 (bloque J), aplicado al bloque B de la cartera (corto altcoin / largo BTC, con el stop que se aprieta tras
+2R de la L56).

## 1. Pre-registro (subido antes de calcular)
**Búsqueda** en las operaciones de B en el top 30 (su universo real). **Validación** en las mismas señales en los puestos 31–100
(costes +0,03 % por lado), que no se miran hasta elegir el filtro.

Variables candidatas (al cierre de la vela de señal, sin mirar al futuro; "a favor" = en la dirección del corto):
1. Profundidad de la ruptura: cuánto cerró el ratio por debajo del mínimo de 120 velas, en ATR.
2. Volatilidad de la altcoin: ATR(14) diario / precio en dólares.
3. Funding medio de 3 días de la altcoin (negativo = cortos amontonados).
4. Caída previa del ratio en 30 días.
5. Distancia del ratio a su media de 50 días (diaria).
6. BTC en 7 días.
7. Volumen de la altcoin el día de la señal / media de 20 días.
8. Antigüedad de la moneda.

Procedimiento: terciles en el top 30; resultado medio por operación (en R) de cada tercil; se elige **como mucho un filtro** (quitar
un tercil extremo de una variable con patrón ordenado), el de mayor mejora.
**Criterio:** (1) en los puestos 31–100, con el corte fijo del top 30, el filtro mejora el resultado medio en desarrollo (2020–2022)
**y** examen (2023 → 2026-10); y (2) en la cartera B real (top 30, riesgo 1 %, máximo 10), Sharpe mayor en las dos mitades y caída
máxima no mayor (criterio de la L44). Si no cumple las dos, B no cambia.
