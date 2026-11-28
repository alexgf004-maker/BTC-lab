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

## 2. Resultados — `l58_busqueda.txt`, `l58_validacion.txt`
**Búsqueda (top 30, 17.182 operaciones candidatas), resultado medio por tercil (R):**
| Variable | Bajo | Medio | Alto | ¿Ordenado? |
|---|---|---|---|---|
| Profundidad de la ruptura | +0,172 | +0,166 | +0,052 | Sí |
| Volatilidad de la altcoin | +0,235 | +0,175 | −0,020 | Sí |
| **Funding 3 días de la altcoin** | **−0,022** | **+0,165** | **+0,261** | **Sí (mayor mejora)** |
| Caída del ratio en 30 días | +0,179 | +0,138 | +0,073 | Sí |
| Distancia bajo la media 50 | +0,148 | +0,146 | +0,096 | Sí |
| BTC 7 días | −0,071 | +0,243 | +0,222 | No |
| Volumen del día | +0,159 | +0,160 | +0,071 | No |
| Antigüedad de la moneda | +0,264 | +0,082 | +0,044 | Sí |

Filtro elegido: no abrir el corto si el funding medio de 3 días de la altcoin es ≤ 0,0024 % por 8 h (cortos ya amontonados).

| Prueba | Sin filtro | Con filtro | ¿Cumple? |
|---|---|---|---|
| (1) Puestos 31–100, desarrollo | +0,056R (n 10.938) | +0,081R (n 7.564) | Sí |
| (1) Puestos 31–100, examen | +0,124R (n 27.164) | +0,177R (n 18.686) | Sí |
| (2) Cartera top 30, 2020–22 | Sharpe 1,68 · caída 29,2 % | Sharpe 1,72 · caída **32,7 %** | **No (caída mayor)** |
| (2) Cartera top 30, 2023–26 | Sharpe 0,97 · caída 32,7 % | Sharpe 1,38 · caída 20,0 % | Sí |

**No pasa el criterio** por la caída máxima de 2020–22 (+3,5 puntos), aunque mejora todo lo demás, incluida la validación en
monedas nuevas. B no cambia. Es el mejor candidato encontrado para B hasta ahora; se puede medir en paralelo como variante en
seguimiento. Observaciones secundarias: la volatilidad de la altcoin y BTC a la baja en 7 días también señalan cortos peores.
