# Lección 28 — Carry entre familias de perpetuos de Binance (USDT, USDC y COIN-M)

## 0. Idea propia
Binance tiene **tres perpetuos distintos sobre la misma moneda**: el de margen USDT (el principal), el de margen USDC y el inverso
(COIN-M, margen en la propia moneda). Son libros de órdenes separados, con participantes distintos, y **cada uno tiene su propio funding**.
Si el funding de uno es sistemáticamente más alto que el del otro, se puede estar **corto en el caro y largo en el barato**: posición
neutral al precio, las dos patas en futuros (sin préstamo de margen ni spot, a diferencia de los bloques A y E), que cobra la diferencia.
Mecanismo esperado: el perpetuo USDT concentra la especulación minorista apalancada (paga más funding en euforia); el USDC y el COIN-M
tienen más creadores de mercado y coberturas institucionales.

## 1. Pre-registro (antes de calcular ningún diferencial)
**Datos:** funding y velas 1h de data.binance.vision. 40 perpetuos USDC (desde 2024-01) y 49 COIN-M (desde 2022-07), cada uno con su par USDT.
**Diferencial:** s = media de 3 días del funding por 8 h del perpetuo USDT − la del otro (suma de pagos de las últimas 72 h / 9, para
igualar intervalos de 1, 4 u 8 h). Se evalúa a las 00, 08 y 16 UTC.
**Regla (igual que el bloque A, sin optimizar):** si |s| > 0,015 % → corto en el de funding alto y largo en el de funding bajo, mismo
nocional N en USD. Salida si |s| < 0,005 %.
**Resultado por posición:** funding cobrado − pagado (pagos reales, con su hora) + variación del diferencial de precio entre los dos
perpetuos (cierres horarios), − costes: 0,07 % por pata y por lado (taker 0,05 % + deslizamiento 0,02 %) → 0,28 % de N por ciclo completo.
**Cartera:** hasta 5 posiciones simultáneas, 20 % del capital por posición (N = 20 % del capital, apalancamiento bruto 2x en futuros).
Prioridad por |s| mayor. Rentabilidad sobre el capital total; liquidez sin remunerar.
**X1:** USDT frente a USDC. Desarrollo 2024-01 → 2025-03; **examen 2025-04 → 2026-10.**
**X2:** USDT frente a COIN-M. Desarrollo 2022-07 → 2024-06; **examen 2024-07 → 2026-10.** Simplificación declarada: el resultado se
calcula en USD sin modelar la convexidad del contrato inverso ni el colateral en moneda (en real, habría que cubrir ese colateral).
**Criterio (en cada X por separado):** en el examen, rentabilidad neta > 0 con t ≥ 3 (rentabilidades diarias de la cartera) y Sharpe ≥ 1,5;
y positiva en desarrollo. Se informa qué parte viene del funding y qué parte del diferencial de precio, y la rentabilidad sin costes.
Pruebas nuevas: 2.

## 2. Resultados — `l28_salida.txt`
| | Neto anual | t | Sharpe | Funding cobrado | Diferencial de precio | Costes | Entradas |
|---|---|---|---|---|---|---|---|
| X1 USDT/USDC desarrollo | −2,9 % | −4,3 | −3,8 | +3,6 %/año | −0,1 % | 6,4 % | 145 |
| **X1 USDT/USDC examen** | **−1,3 %** | −1,7 | −1,3 | +6,1 %/año | +1,0 % | 8,4 % | 239 |
| X2 USDT/COIN-M desarrollo | −5,0 % | 0,1 | 0,1 | +10,8 %/año | −2,6 % | 13,2 % | 415 |
| **X2 USDT/COIN-M examen** | **−5,2 %** | −0,1 | −0,0 | +14,4 %/año | −10,3 % | 9,2 % | 365 |

**Las dos se rechazan.**
- **El mecanismo era el contrario al esperado:** el funding del perpetuo USDT es en general MÁS BAJO que el del USDC y el COIN-M
  (mediana −1,1 a −2,5 % anual; solo el 11–29 % de los pares al revés). Hay más creadores de mercado y arbitrajistas en el USDT, y su prima
  está más ajustada; los libros pequeños (USDC, COIN-M) son los que se desvían.
- **El diferencial existe pero es pequeño y cambia de signo a menudo:** la regla lo cobra (+6 % a +14 % anual en bruto), pero entra y
  sale demasiadas veces y los costes de cuatro órdenes por ciclo se lo comen.
- **COIN-M:** los perpetuos inversos poco líquidos tienen precios que se separan del USDT durante días (−10 % anual por el diferencial de
  precio en el examen y caídas del 34–59 %): el "neutral al mercado" no lo es tanto cuando una pata es poco líquida.
- Confirma una regla general de toda la investigación: **las primas entre mercados de Binance que se pueden cubrir al instante son
  demasiado pequeñas para costes de taker.** Solo sobreviven las primas que pagan por un riesgo o una restricción (carry spot-perpetuo,
  carry inverso con préstamo).
