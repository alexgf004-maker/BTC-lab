# Lección 59 — ¿Qué tienen en común las operaciones perdedoras del bloque G?

Mismo método que las L57 (J) y L58 (B), aplicado al bloque G (ráfaga de momentum en BTC, ETH y SOL, con los filtros de euforia y
de figuras bajistas).

## 1. Pre-registro (subido antes de calcular)
**Búsqueda** en las operaciones de G en BTC, ETH y SOL (2020 → 2026-10). **Validación** con la misma regla en las demás monedas del
top 30 de cada mes (G nunca las opera), que no se miran hasta elegir el filtro.

Variables candidatas (al cierre de la vela de señal):
1. Tamaño de la subida de 3 h.
2. Intensidad del pico de operaciones (z-score).
3. Distancia sobre la EMA200 (horaria).
4. Volatilidad: ATR(14) horario / precio.
5. Funding medio de 3 días (por debajo del corte de euforia).
6. Tendencia de BTC: BTC frente a su media de 50 días.
7. Rentabilidad de las 24 h previas a la subida.
8. Volumen de las últimas 24 h frente a la media de 7 días.

Procedimiento: terciles en la búsqueda; resultado medio en R por tercil; se elige **como mucho un filtro** (quitar un tercil extremo
de una variable con patrón ordenado), el de mayor mejora.
**Criterio:** (1) en la validación (otras monedas del top 30), con el corte fijo de la búsqueda, el filtro mejora el resultado medio
en desarrollo (2020–2022) **y** examen (2023 → 2026-10); y (2) en G real, resultado medio mayor en los dos periodos conservando al
menos el 80 % de las operaciones (criterio de la L45). Si no, G no cambia.

## 2. Resultados — `l59_busqueda.txt`, `l59_validacion.txt`
**Búsqueda (G en BTC, ETH y SOL: 371 operaciones, acierto 28 %, media +0,83R), resultado medio por tercil:**
| Variable | Bajo | Medio | Alto | ¿Ordenado? |
|---|---|---|---|---|
| Subida de 3 h | +1,77R | +0,16R | +0,56R | No |
| Pico de operaciones (z) | +0,59R | +0,45R | +1,44R | No |
| Distancia sobre la EMA200 | +1,16R | +0,94R | +0,39R | Sí |
| **Volatilidad (ATR horario)** | **+1,61R** | **+0,59R** | **+0,28R** | **Sí (mayor mejora)** |
| Funding 3 días | +0,75R | +0,97R | +0,77R | No |
| BTC frente a su media de 50 días | +0,50R | +0,99R | +1,00R | Sí |
| Rentabilidad 24 h previas | +0,57R | +1,64R | +0,29R | No |
| Volumen 24 h / 7 días | +0,90R | +0,53R | +1,05R | No |

Filtro elegido: no comprar si el ATR horario es > 1,38 % del precio.

| Prueba | Sin filtro | Con filtro | ¿Cumple? |
|---|---|---|---|
| (1) Otras monedas del top 30, desarrollo | −0,057R (n 1567) | +0,028R (n 375) | Sí |
| (1) Otras monedas del top 30, examen | +0,126R (n 2425) | +0,474R (n 724) | Sí |
| (2) G real, desarrollo | +0,739R (n 142) | +1,300R (n 73, **51 %**) | No (< 80 %) |
| (2) G real, examen | +0,885R (n 229) | +1,020R (n 174, **76 %**) | No (< 80 %) |

**No pasa:** mejora el resultado por operación (también en monedas nuevas), pero quita demasiadas operaciones y el beneficio total
de G baja (105R → 95R en desarrollo; 203R → 178R en examen). G no cambia.

## 3. Conclusión de las lecciones 57–59 (rasgos de las pérdidas)
- **J:** no operar monedas tranquilas → aprobado y activado.
- **B:** no abrir cortos con funding bajo → mejora casi todo, pero sube la caída de 2020–22; se mide en paralelo como bloque M.
- **G:** no comprar con volatilidad alta → mejor por operación, pero menos beneficio total; rechazado.
Patrón común: **la volatilidad** separa operaciones buenas y malas en las tres estrategias (en J conviene alta; en B y G, baja).
