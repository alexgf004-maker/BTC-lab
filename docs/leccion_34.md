# Lección 34 — Forex: carry, tendencia y valor en las divisas principales

## 0. Por qué estas tres
En divisas, la literatura académica documenta tres primas con décadas de datos y muchos países: **carry** (las divisas con tipos
altos rinden más de lo que su tipo de interés "debería" compensar; Lustig, Roussanov y Verdelhan, 2011), **tendencia** (momentum de serie
temporal; Moskowitz, Ooi y Pedersen, 2012) y **valor** (las divisas baratas en términos reales tienden a recuperarse; Asness, Moskowitz y
Pedersen, 2013). Son las que usan los fondos de divisas. Se prueban aquí con el mismo rigor que en cripto.

## 1. Datos (FRED, Reserva Federal de San Luis)
Tipos de cambio diarios frente al USD (H.10): EUR (desde 1999), JPY, GBP, CHF, CAD, AUD, NZD, SEK, NOK.
Tipos de interés a corto plazo de cada país (OCDE: interbancario a 3 meses; antes, tipo a un día; Japón antes de 1985, tipo de descuento).
Tipo de cambio efectivo real de cada divisa (BIS, mensual, desde 1994).
Rentabilidad de estar largo en una divisa frente al USD en un mes = variación del tipo de cambio + (tipo de la divisa − tipo del USD)/12
(lo que paga un contrato a plazo o el "swap" de un bróker, antes de su margen).

## 2. Pre-registro (antes de calcular ningún resultado)
Señales con datos hasta el último día hábil del mes; posiciones durante el mes siguiente.
**F1 — Carry:** largo en las 3 divisas con mayor diferencial de tipos frente al USD y corto en las 3 con menor (pesos iguales, neutral al dólar).
**F2 — Tendencia:** en cada divisa, signo de su rentabilidad de los 12 meses previos (tipo de cambio + carry); tamaño inverso a su
volatilidad de 3 meses (objetivo 10 % anual por divisa, dividido entre el número de divisas).
**F3 — Valor:** desviación del tipo de cambio real (BIS) respecto a su media de 5 años; largo en las 3 más baratas, corto en las 3 más caras
(desde 1999 por la historia de los datos).
**F4 — Combinación:** F1, F2 y F3 con el mismo riesgo (cada una escalada a 10 % de volatilidad anual con su volatilidad de los 36 meses previos),
y el conjunto escalado de nuevo a 10 % anual.
**Costes (bróker de CFD minorista, conservador):** diferencial por lado de 1 pb (EUR, JPY, GBP, CHF, CAD, AUD), 2 pb (NZD), 5 pb (SEK, NOK)
sobre lo negociado + **1 % anual sobre el nocional bruto** por el margen del bróker en los swaps. Se informa también con costes de
Interactive Brokers (0,2 pb + 0,25 % anual).
**Periodos:** desarrollo 1985–2005; **examen 2006 → 2026-10** (F3: desarrollo 1999–2010, examen 2011 → 2026-10). Una vez.
**Criterio:** Sharpe neto de F4 ≥ 0,5 en el examen y positivo en el desarrollo. Se informa cada pieza, el apalancamiento necesario
(máximo europeo para particulares: 30:1 en principales), la caída máxima y la correlación con la cartera de cripto (2020-03 → 2026-10).
Pruebas nuevas: 4.

## 3. Resultados — `l34_salida.txt` (escaladas a 10 % de volatilidad anual)
| Estrategia | Desarrollo: Sharpe / anual | **Examen (2006–2026): Sharpe / anual / caída** | Examen sin costes |
|---|---|---|---|
| F1 Carry | 0,40 / +3,8 % | **0,00 / −0,5 % / 42 %** (IB: 0,22) | 0,29 |
| F2 Tendencia | 0,73 / +7,3 % | **−0,19 / −2,5 % / 50 %** (IB: −0,07) | −0,04 |
| F3 Valor (1999–2010 / 2011–2026) | −0,38 / −4,8 % | **−0,29 / −3,2 % / 46 %** (IB: 0,00) | 0,10 |
| **F4 Combinación** | **0,77 / +8,1 %** | **−0,09 / −1,7 % / 47 %** (IB: +0,13) | 0,19 |
Por década (F4, costes de CFD): 1980s +3,5 %, 1990s +8,1 %, 2000s +5,9 %, **2010s +1,1 %, 2020s −5,0 % anual**.

**NO aprobada.** Las primas de divisas funcionaron hasta 2005 (Sharpe 0,77, como dice la literatura) y **desaparecieron después**:
el carry se hundió en 2008 y luego hubo una década de tipos casi iguales en todos los países (sin diferencial que cobrar); la tendencia
en divisas lleva 15 años sin funcionar. Es un resultado conocido: estas primas se publicaron, los fondos las explotaron y se comprimieron.

**Comparación con la cartera de cripto (2020-03 → 2026-10, mensual):**
| | Anual | Sharpe | Caída máx. |
|---|---|---|---|
| Cartera cripto del bot | +29,6 % | 1,81 | 6,2 % |
| Forex F4 | −3,3 % | −0,29 | 37,3 % |
| 75 % cripto + 25 % forex | +20,8 % | 1,65 | 5,9 % |
Correlación +0,16: diversificaría algo, pero restando rentabilidad. **No compensa.**

## 4. Conclusión
En las divisas principales, los mercados más eficientes y líquidos del mundo, las primas clásicas están agotadas desde hace 15 años
para un particular con costes de CFD. Las ventajas que hemos encontrado en cripto existen porque cripto es un mercado joven, segmentado
y con restricciones (funding, préstamos, emisión de tokens) que en forex no hay. **Forex no es mejor ni más rentable para nosotros.**
