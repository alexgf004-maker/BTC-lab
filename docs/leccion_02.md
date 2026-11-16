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

## 2. Resultados en muestra (2020-2023) — salida completa en `l02_salida_diseno.txt`

> Nota de proceso: la primera ejecución dio E = −6R y win rates de 0 %/100 % por activo.
> Era un **error del motor** (las fechas estaban en milisegundos y la duración de la vela en nanosegundos, así que el funding
> se cobraba de toda la historia). Se corrigió y se añadieron pruebas (`tests/test_swing.py`).
> Lección: **un resultado espectacular es un error hasta que se demuestre lo contrario.**

**Largos** (mejor zona robusta: umbral 20, m 3, rr 2):

| | Trades | Win rate | E neta | PF |
|---|---|---|---|---|
| Estrategia (RSI<20 en tendencia) | 1279 | 54 % | +0,03R | 1,12 |
| **Control: entradas al azar en tendencia** | 8319 | 51 % | **+0,05R** | **1,19** |

- Por año: 2020 −0,03R, 2021 +0,11R, 2022 −0,10R, 2023 +0,06R → solo gana en años alcistas.
- El 80 % de los trades sale **por tiempo**: el stop y el objetivo casi nunca se alcanzan en 48 h.
- Win rate alto (63 %) solo con rr 0,5, y ahí E ≈ 0.

**Cortos:** 98 de 100 combinaciones pierden; la mejor tiene E ≈ 0. Sin ventaja.

## 3. Veredicto: HIPÓTESIS A RECHAZADA (ya en muestra)

- PF 1,12 < 1,3 exigido.
- **Peor que el control aleatorio**: comprar el retroceso no añade nada; lo poco que
  gana viene del filtro de tendencia diaria (y del mercado alcista de 2021 y 2023).
- Por eso **NO se ejecuta la fase fuera de muestra**: 2024-2026 sigue virgen para la próxima hipótesis.

## 4. Lo que aprendemos para la Lección 3
1. Que el **control** (al azar pero a favor de la tendencia diaria) tenga PF 1,19 es la pista más
   valiosa: **la tendencia diaria sí contiene información**. La siguiente hipótesis debe explotarla
   directamente (seguimiento de tendencia / momentum), no comprar retrocesos.
2. En 4h el RSI(3) es ruido: la reversión de corto plazo no supera al azar en estas criptos.
3. Los cortos en cripto son mucho más difíciles: deriva alcista estructural.
4. Siempre hay que compararse contra un control aleatorio con el mismo filtro y las mismas salidas.
   Sin él habríamos celebrado un "PF 1,12, 54 % de aciertos, 76 de 100 combinaciones positivas".
