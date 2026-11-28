# Lección 57 — ¿Qué tienen en común las operaciones perdedoras del bloque J?

Pregunta del usuario: J acierta el ~70 % pero pierde ~18 % cuando falla frente a ~7,5 % que gana cuando acierta. ¿Hay algo, al
entrar, que avise de que una operación será perdedora?

## 1. Pre-registro (subido antes de calcular)
Operaciones: regla J actual (stop 2 ATR). **Búsqueda solo en el top 30** (6.455 operaciones, L54). **Validación en los puestos
31–100** (13.657 operaciones, L55), que no se miran hasta haber elegido el filtro.

Variables candidatas (medidas al cierre del día de la ruptura, sin mirar al futuro):
1. Tamaño de la ruptura: distancia del cierre al nivel, en % (p. ej. BTW cerró un 18 % por encima de 1,00 $).
2. Tamaño de la ruptura en ATR.
3. Volatilidad: ATR(14) diario / precio.
4. Volumen del día de la ruptura frente a la media de 20 días.
5. Tendencia: cierre frente a la media de 50 días, en la dirección de la ruptura.
6. Rentabilidad de los 30 días previos, en la dirección de la ruptura.
7. Mercado: rentabilidad de BTC en 7 días, en la dirección de la ruptura.
8. Antigüedad de la moneda (días desde su primer dato).
9. Funding medio de 3 días, en la dirección de la ruptura (largos pagando → ruptura alcista "cargada").
10. Dirección de la ruptura (alcista → corto; bajista → largo).

Procedimiento: en el top 30, terciles de cada variable; para cada una, acierto, pérdida media y resultado medio por tercil. Se elige
**como mucho un filtro** (quitar un tercil extremo de una sola variable), el de mayor mejora del resultado medio en el top 30,
siempre que el patrón sea monótono (los tres terciles en orden).
**Criterio de validación** (puestos 31–100): el filtro mejora el resultado medio de J en desarrollo (2020–2022) **y** examen
(2023 → 2026-10), y deja J con media positiva en los dos. Si no, no se aplica.

## 2. Resultados — `l57_busqueda.txt`, `l57_validacion.txt`
**Búsqueda (top 30, 6.455 operaciones), resultado medio por tercil:**
| Variable | Bajo | Medio | Alto | ¿Ordenado? |
|---|---|---|---|---|
| Tamaño de la ruptura (%) | −0,35 % | −0,06 % | +0,93 % | Sí |
| Tamaño de la ruptura (ATR) | −0,20 % | +0,44 % | +0,28 % | No |
| **Volatilidad (ATR/precio)** | **−0,48 %** | **−0,30 %** | **+1,29 %** | **Sí (mayor mejora)** |
| Volumen del día de ruptura | +0,06 % | +0,48 % | −0,02 % | No |
| Tendencia (vs media 50 d) | +0,60 % | +0,05 % | −0,13 % | Sí |
| Rentabilidad 30 días | +0,93 % | −0,11 % | −0,30 % | Sí |
| BTC 7 días | −0,11 % | 0,00 % | +0,63 % | Sí |
| Antigüedad de la moneda | −0,14 % | +0,35 % | +0,31 % | No |
| Funding 3 días | +0,09 % | +0,72 % | −0,26 % | No |
| Dirección (bajista / alcista) | +0,47 % | — | −0,13 % | — |

Filtro elegido según la regla: **no operar las monedas tranquilas** (tercil bajo de volatilidad; corte en el top 30: ATR diario
≤ 7,53 % del precio). En las monedas tranquilas la ruptura del redondo suele ser real; en las volátiles suele ser ruido.

**Validación en los puestos 31–100 (13.657 operaciones no miradas):**
| | Desarrollo | Examen |
|---|---|---|
| J sin filtro | −0,067 % (n 4847) | −0,041 % (n 8810) |
| J con filtro (corte del propio grupo, 8,15 %) | +0,168 % (n 3773) | +0,338 % (n 5331) |
| **J con filtro fijo (7,53 %, el del top 30)** | **+0,006 %** (n 4046) | **+0,247 %** (n 5974) |

**Pasa el criterio** (mejora en los dos periodos y queda positivo en ambos), pero justo: con el corte fijo, el desarrollo queda en
≈ 0 y la significación total es baja (t +0,43). El filtro mejora J de forma consistente en datos nuevos; J sigue siendo una
estrategia marginal. **Activado en el bot** (`vol_min: 0.0753`): J no abre si el ATR(14) diario es ≤ 7,53 % del precio.

Hallazgo contraintuitivo: las pérdidas más grandes están en las monedas volátiles (−26 % de media cuando falla), pero esas son
también las que más aciertan y más ganan; las que destruyen valor son las tranquilas, donde la ruptura del redondo suele ser de verdad.
