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
