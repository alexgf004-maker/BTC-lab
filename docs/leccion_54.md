# Lección 54 — El stop del bloque J (ruptura falsa de redondos)

Observación del usuario siguiendo BTW y ZEC: la regla acierta, pero el stop "en el siguiente número redondo" queda demasiado
cerca en unas operaciones (BTW: 0,4 % de la entrada) y muy lejos en otras (NEAR: 15 %). Su distancia depende de dónde caiga el
precio respecto a la escala de redondos, no del movimiento normal de la moneda.

**Advertencia (se declara):** la regla de J ya salió de una observación posterior de la L46. Comparar stops sobre los mismos datos
es exploratorio. Por eso: variantes fijadas aquí antes de calcular, criterio estricto, y la validación real sigue siendo el
seguimiento hacia adelante.

## 1. Pre-registro (subido antes de calcular)
Regla de J (igual que en el bot): top 30, cierre diario al otro lado de un redondo defendido 3 días → entrada en contra de la ruptura
a la apertura del día siguiente; ganancia cuando un cierre diario vuelve al otro lado del nivel; máximo 20 días. Costes 0,07 % por
lado + funding. Stop revisado dentro del día (como una orden stop). Desarrollo 2020–2022; examen 2023 → 2026-10.

Variantes de stop:
- **S0 (actual):** siguiente número redondo.
- **S1:** 2 × ATR(14) diario desde la entrada.
- **S2:** 3 × ATR(14) diario desde la entrada.
- **S3:** extremo del día de la ruptura + 1 × ATR (por encima del máximo de ese día en los cortos, por debajo del mínimo en los largos).
- **S4:** sin stop (solo la salida diaria y los 20 días).

Criterio para cambiar el stop de J: una variante con media neta por operación mayor que S0 en desarrollo **y** examen, y peor
operación no más de 2 veces peor que la de S0. Si varias cumplen, la de mayor media en el examen. Si ninguna cumple, J se queda igual.

## 2. Resultados — `l54_salida.txt`
| Stop | Desarrollo: media / acierto | Examen: media / acierto | Peor operación | Distancia mediana del stop (p10–p90) |
|---|---|---|---|---|
| S0 siguiente redondo (actual) | +0,06 % / 50 % | −0,05 % / 51 % | −51 % | 7,1 % (2,1–24,2 %) |
| **S1 2 ATR** | **+0,19 % / 71 %** | **+0,16 % / 71 %** | −99 % | 18,5 % (10,1–34,9 %) |
| S2 3 ATR | −0,01 % / 75 % | +0,21 % / 76 % | −126 % | 27,6 % |
| S3 extremo de la ruptura + 1 ATR | +0,48 % / 64 % | +0,01 % / 63 % | −303 % | 11,7 % |
| S4 sin stop | −0,35 % / 78 % | +0,13 % / 78 % | −466 % | — |

Las peores operaciones son reales, no errores de datos: el colapso de LUNA (2022) y lanzamientos muy volátiles (LAB, RIVER, SIREN en
2026) con movimientos diarios del 50–90 %.

**Decisión según el criterio:** solo **S1 (2 ATR)** mejora en los dos periodos (+0,19 % y +0,16 % frente a +0,06 % y −0,05 %) con
una peor operación dentro del límite (−99 % frente al tope de −103 %). **J pasa a usar stop de 2 ATR** en las operaciones nuevas.

**Lo que no cambia:** ninguna variante hace que J sea claramente rentable (t entre −0,4 y +1,3). El usuario tenía razón en que el
stop del redondo era arbitrario y demasiado justo a menudo (en el 10 % de los casos, a menos del 2,1 %); con 2 ATR se acierta el 71 %
de las veces, pero las pérdidas, cuando llegan, son mayores. J sigue en seguimiento.
