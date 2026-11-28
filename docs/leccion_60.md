# Lección 60 — ¿Qué tienen en común las operaciones perdedoras del bloque D?

Mismo método que las L57–L59, aplicado al bloque D (tendencia en BTC y ETH: ruptura del máximo de 20 días con tendencia diaria
alcista; piramidación; filtro de euforia).

## 1. Pre-registro (subido antes de calcular)
**Búsqueda** en las operaciones de D en BTC y ETH (2020-03 → 2026-10). **Validación** con la misma regla en las demás monedas del top
30 de cada mes (D nunca las opera), que no se miran hasta elegir el filtro. D opera poco (≈ 100 operaciones), así que la
validación pesa más.

Variables candidatas (al cierre de la vela de 4 h de la ruptura):
1. Fuerza de la ruptura: (cierre − máximo previo de 120 velas) / ATR.
2. Volatilidad: ATR(14) de 4 h / precio.
3. Funding medio de 3 días (por debajo del corte de euforia).
4. Extensión de la tendencia: cierre diario frente a su EMA50.
5. Rentabilidad de los 30 días previos.
6. Volumen de las últimas 24 h frente a la media de 20 días.
7. Tendencia de BTC frente a su EMA50 diaria (para BTC coincide con la 4).

Procedimiento: terciles; resultado medio por operación (R del riesgo total de 5 %); **como mucho un filtro** (quitar un tercil
extremo de una variable con patrón ordenado), el de mayor mejora.
**Criterio:** (1) en la validación, con el corte fijo, mejora el resultado medio en desarrollo (2020-03 → 2023-06) **y** examen
(2023-07 → 2026-10); y (2) en D real (BTC + ETH), Sharpe mayor en los dos periodos y caída máxima no mayor (criterio de la L43).
