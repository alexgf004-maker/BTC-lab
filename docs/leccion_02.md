# Lección 2 — Hipótesis A: retroceso dentro de la tendencia (swing 4h)

## 1. Pre-registro (escrito y commiteado ANTES de ver ningún resultado)

**Por qué podría funcionar:** en cripto, la tendencia diaria persiste (momentum), y los excesos
de corto plazo dentro de ella tienden a revertir (los vendedores de pánico entregan
liquidez a los compradores). Comprar caídas fuertes de 4h **solo** cuando el diario es alcista.

**Universo:** perpetuos USDⓈ-M de BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, LINK y LTC.
**Datos:** velas de 1h → agregadas a 4h y 1d.
**División:** EN MUESTRA 2020-01 → 2023-12 (diseño). FUERA DE MUESTRA 2024-01 → 2026-10
(se mira **una sola vez**, al final, con los parámetros ya congelados).

**Reglas (largos; los cortos son el espejo y se evalúan por separado):**
1. Filtro de tendencia: último cierre diario COMPLETO > EMA50 diaria.
2. Señal: al cierre de una vela 4h, RSI(3) < `umbral`.
3. Entrada: orden limit en `cierre − 0,25·ATR14(4h)`, válida solo la vela siguiente
   (si no se llena, se cancela). Comisión maker.
4. Stop: `entrada − m·ATR`. Objetivo: `entrada + rr·m·ATR` (limit, maker).
5. Salida por tiempo: 12 velas (48 h) a mercado.
6. Una posición por activo a la vez.

**Simulación conservadora:** en la vela de llenado puede saltar el stop pero NO el objetivo;
si una vela toca ambos, cuenta el stop; los gaps se cobran a la apertura.
Stop y salida por tiempo: taker 0,05 % + slippage 0,02 %. Funding real histórico cobrado/abonado.

**Rejilla de diseño (solo en muestra):** umbral ∈ {10,15,20,25,30}, m ∈ {1,5; 2; 2,5; 3},
rr ∈ {0,5; 0,75; 1; 1,5; 2} → 100 combinaciones.

**Regla de elección:** entre combinaciones con ≥ 300 trades en muestra, la que maximice la
**media de E neta de ella y sus vecinas** en la rejilla (premiamos zonas estables, no picos).

**Control:** entradas aleatorias con el MISMO filtro de tendencia y las mismas salidas.
Si la señal RSI no supera a este control, la "ventaja" sería solo el filtro de tendencia
(o el mercado alcista), no el retroceso.

**Aprobación fuera de muestra:** PF neto ≥ 1,3, ≥ 300 trades, E neta > control y positiva
en la mayoría de activos y años.
