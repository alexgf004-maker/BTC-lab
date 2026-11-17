# Lección 27 — HOLD: ¿se puede mejorar comprar y mantener?

## 0. Por qué
Hasta ahora todo lo estudiado era trading activo. Pero la referencia honesta para cualquier estrategia es **comprar BTC y no hacer nada**.
Esta lección estudia formas de "hold" que la literatura académica defiende, con el mismo rigor que el resto:
- **Gestión por volatilidad** (Moreira y Muir, 2017, *Journal of Finance*): reducir la exposición cuando la volatilidad reciente es alta
  mejora el Sharpe en acciones, divisas y bonos, porque la volatilidad es predecible y la rentabilidad no sube con ella.
- **Filtro de tendencia lento** (media de 200 días; Faber, 2007): salir a liquidez en las tendencias bajistas largas.
- **Índice diversificado** de criptos frente a solo BTC.
- **Compras periódicas (DCA)** frente a invertir todo de golpe.

## 1. Pre-registro (antes de calcular ningún resultado)
**Datos:** velas diarias **spot** de Binance (BTCUSDT y ETHUSDT desde 2017-08). Sin funding (spot). Liquidez en USDT al 0 % (conservador).
**Costes:** 0,12 % por unidad de nocional negociado (comisión spot 0,10 % + deslizamiento 0,02 %).
**Periodos:** desarrollo 2017-09-01 → 2021-12-31; **examen 2022-01-01 → 2026-10-31** (una vez).
**Señales:** calculadas con el cierre del día t y aplicadas al cierre del día t (operación al cierre, rentabilidad desde t+1). Sin apalancamiento (peso ≤ 1).

Referencias (no son pruebas): **H0** comprar y mantener BTC; ETH; 50/50 BTC-ETH con reequilibrio mensual.

**H1 — BTC gestionado por volatilidad.** σ̂ = desviación típica de las 30 últimas rentabilidades diarias, anualizada (√365).
Peso w = min(1, 0,40 / σ̂). Se reequilibra solo si |w − w_actual| > 0,10.
**H2 — BTC con filtro de 200 días.** w = 1 si cierre > media simple de 200 días; si no, 0.
**H3 — H1 y H2 combinados:** w = H1 si cierre > media de 200 días; si no, 0.
**H4 — Las mismas tres reglas en ETH y en la cesta 50/50** (robustez; no se elige la mejor).
**H5 — Índice igual ponderado de las 10 criptos más líquidas** (universo point-in-time del mes anterior, con monedas deslistadas,
excluidas stablecoins, oro y acciones), reequilibrio mensual, precios de perpetuo con funding (2020-03 → 2026-10;
desarrollo hasta 2022-12, examen desde 2023-01) frente a BTC en el mismo periodo y con el mismo tratamiento.
**H6 — DCA frente a todo de golpe (informativo):** para cada mes de inicio, invertir 12 partes iguales mensuales frente a invertirlo todo
el primer día; se compara el valor a los 12 y a los 24 meses.

**Criterio de aprobación de H1–H3** (frente a comprar y mantener el mismo activo): Sharpe mayor **y** caída máxima menor,
**en desarrollo y en examen**, en BTC; y se informa si se repite en ETH y en la cesta (no se exige para no seleccionar).
Diferencia de Sharpe con intervalo por remuestreo en bloques de 3 meses (se informa la probabilidad de que la mejora sea ≤ 0).
**H5** se aprueba solo si supera a BTC en Sharpe en los dos periodos.
Pruebas nuevas para la corrección por suerte: 6.
