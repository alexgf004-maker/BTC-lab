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
