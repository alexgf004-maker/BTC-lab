# Lección 36 — Mercados de predicción (Polymarket): ¿están bien calibrados los precios?

## 0. Por qué
En un mercado de predicción, un contrato paga 1 $ si ocurre el suceso y 0 si no; su precio es la probabilidad que asigna el mercado.
En las apuestas deportivas y en las carreras de caballos está documentado desde hace 70 años el **sesgo favorito–improbable**: los
resultados improbables se pagan demasiado caros (a la gente le gusta la "lotería") y los favoritos, demasiado baratos (Griffith 1949;
Thaler y Ziemba 1988; Snowberg y Wolfers 2010). Si Polymarket lo tiene, comprar favoritos daría una ventaja sistemática.
Es un mercado joven, con mucho público minorista y sin creadores de mercado dominantes: el tipo de mercado donde hemos encontrado ventajas.

## 1. Pre-registro (antes de descargar precios)
**Mercados:** todos los mercados binarios (Sí/No) de Polymarket ya resueltos con resultado claro (1/0), con volumen ≥ 100 000 $ y una
duración ≥ 8 días. Precio: historial del token "Sí" en la CLOB pública (velas de 1 h).
**Momento de medida:** T = cierre del mercado. Precio a T−7 días (principal), T−1 día y T−30 días (secundarios).
"Favorito" = el lado con precio q = max(p, 1−p).
**P0 — Calibración (medición):** por tramos de q, porcentaje de favoritos que ganan frente a q (con error estándar).
**P1 — Comprar el favorito a T−7 días** si q está entre 0,80 y 0,97. Coste: precio de compra = q + 1 céntimo (diferencial).
Resultado por operación = (1 − precio)/precio si gana, −1 si pierde; mismo importe en cada mercado.
**P2 — Comprar casi seguros a T−1 día** (q entre 0,95 y 0,995; coste + 0,5 céntimos): rendimiento por esperar la resolución.
**Periodos:** desarrollo = mercados cerrados antes del 2025-01-01; **examen = cerrados desde el 2025-01-01 hasta hoy** (una vez).
**Criterio (P1 y P2 por separado):** resultado medio neto > 0 con t ≥ 3 (agrupando por semana de cierre) en el examen y positivo en el
desarrollo. Se informa la rentabilidad por día de capital inmovilizado, la peor racha y el resultado por categoría si existe.
**Limitaciones:** el historial de la CLOB da precios de referencia, no el libro completo; el diferencial real puede ser mayor en mercados
pequeños (por eso el filtro de volumen). Polymarket puede no estar disponible en todos los países: hay que comprobarlo antes de operar.
Pruebas nuevas: 2.

## 2. Resultados — `l36_salida.txt` (26 012 mercados: 1 862 de desarrollo, 24 150 de examen)
**P1 — Comprar el favorito a T−7 días: RECHAZADA.** Gana el 87,5 %, pero pierde un −3,9 % por operación en el examen (t −6,4) y
un −4,5 % en el desarrollo.
**P2 — Comprar casi seguros a T−1 día: RECHAZADA.** Gana el 98 %, pero el 2 % que falla se lo come todo (−0,7 % por operación en el examen).

**Calibración a T−7 días (examen):** los favoritos ganan MENOS de lo que dice su precio en todos los tramos de 0,5 a 0,95
(de −1,8 a −4,9 puntos; z de −3 a −6). Es **lo contrario del sesgo favorito–improbable clásico**: en Polymarket 2025–2026,
los improbables están baratos y los favoritos, caros.
Desglose (favoritos entre 0,60 y 0,95):
| | n | Precio | Gana | Diferencia |
|---|---|---|---|---|
| El favorito es "Sí" | 2 248 | 74,5 % | 76,7 % | +2,3 pts |
| **El favorito es "No"** | 7 820 | 79,6 % | 74,6 % | **−5,0 pts (z −11)** |
| Volumen 100 k–300 k / 300 k–1 M / > 1 M | | | | −3,3 / −2,4 / −5,3 pts |
Por trimestre: entre −0,9 y −5,3 puntos en los 8 trimestres. **El patrón es "el Sí está barato"**: en las preguntas del tipo
"¿pasará X antes de tal fecha?", el mercado infravalora que ocurra.

**Advertencia importante — posible sesgo de selección:** el filtro de volumen (≥ 100 000 $) usa el volumen FINAL del mercado. Los
mercados donde ocurre lo inesperado atraen más operaciones al final, así que pasan el filtro más a menudo. Eso por sí solo puede crear
un "Sí barato" aparente. Con los datos públicos no se puede saber el volumen que había 7 días antes, así que **el hallazgo no se puede
validar con historia.**

## 3. Conclusiones
1. Ninguna de las estrategias pre-registradas funciona: comprar favoritos o casi seguros pierde dinero, aunque acierte el 87–98 %.
2. Aparece una anomalía interesante y persistente (el "Sí" infravalorado 4–5 puntos), pero podría ser un artefacto del filtro de volumen.
3. **Pista para seguimiento en tiempo real (sin sesgo posible):** elegir cada semana los mercados con volumen ≥ 100 000 $ YA acumulado
   y comprar "Sí" cuando cueste entre 0,05 y 0,40 a 7 días del cierre; anotar sin dinero real durante 3–6 meses.
4. Antes de operar en Polymarket hay que comprobar que está permitido desde tu país.
