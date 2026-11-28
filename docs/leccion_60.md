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

## 2. Resultados — `l60_busqueda.txt`, `l60_validacion.txt`
**Búsqueda (D en BTC y ETH: 98 operaciones, acierto 41 %, media +0,62R), resultado medio por tercil:**
| Variable | Bajo | Medio | Alto | ¿Ordenado? |
|---|---|---|---|---|
| Fuerza de la ruptura | +0,57R | +0,46R | +0,83R | No |
| Volatilidad | +1,35R | +0,17R | +0,33R | No |
| Funding 3 días | +0,36R | +0,77R | +0,74R | No |
| Extensión sobre la EMA50 | +1,15R | +0,47R | +0,24R | Sí |
| **Rentabilidad 30 días** | **+1,09R** | **+0,58R** | **+0,20R** | **Sí (mayor mejora)** |
| Volumen 24 h | +0,72R | +0,95R | +0,21R | No |
| BTC vs su EMA50 | +1,25R | +0,33R | +0,25R | Sí |

Filtro elegido: no comprar si la moneda ya subió más de un 17,9 % en los 30 días previos.

| Prueba | Sin filtro | Con filtro | ¿Cumple? |
|---|---|---|---|
| (1) Otras monedas del top 30, desarrollo | +0,215R (n 480) | +0,217R (n 237) | Sí (por poco) |
| (1) Otras monedas del top 30, examen | +0,107R (n 556) | +0,153R (n 284) | Sí |
| (2) D real, desarrollo | Sharpe 1,23 · caída 5,8 % | Sharpe **1,11** · caída 4,6 % | **No** |
| (2) D real, examen | Sharpe 0,64 · caída 12,6 % | Sharpe 0,68 · caída 12,0 % | Sí |

**No pasa:** empeora el Sharpe de D en 2020–23. D no cambia. Las tres variables ordenadas (extensión, rentabilidad de 30 días y
tendencia de BTC) apuntan a lo mismo: comprar una ruptura cuando la subida ya está muy extendida rinde menos, pero quitar esas
compras también quita algunas de las mejores tendencias.
