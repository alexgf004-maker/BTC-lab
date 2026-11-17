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

## 2. Resultados — `l27_salida.txt`, `l27_salida_corregida.txt`
**Error de diseño declarado:** la media de 200 días necesita 200 días de historia y los datos spot de Binance empiezan el 17-ago-2017.
En el desarrollo pre-registrado (desde 2017-09) las reglas con filtro estuvieron fuera a la fuerza durante la subida de finales de 2017.
Se informa del resultado pre-registrado **y** del corregido (desde el 6-mar-2018, cuando existen todas las señales), y se añade como
comprobación la historia larga de BTC (Coin Metrics, desde 2013). No se cambia ninguna regla.

**BTC (P≤0 = probabilidad por remuestreo de que la mejora de Sharpe sea nula o negativa)**
| Periodo | Hold: Sharpe / caída | H1 volatilidad | H2 media 200 | H3 ambas |
|---|---|---|---|---|
| Desarrollo pre-registrado 2017-09→2021 | 1,06 / 83 % | 1,10 / 59 % | 0,62 / 64 % | 0,79 / 45 % |
| Desarrollo corregido 2018-03→2021 | 0,89 / 70 % | 0,87 / 53 % | 0,69 / 64 % | 0,85 / 45 % |
| Historia larga 2013→2017-08 | 1,85 / 85 % | 1,98 / 64 % | 1,97 / 71 % | **2,28 / 49 %** |
| Historia larga 2013→2021 | 1,49 / 85 % | 1,56 / 64 % | 1,51 / 71 % | **1,74 / 49 %** |
| **Examen 2022→2026-10** | 0,45 / 67 % | 0,51 / 55 % | 0,89 / 32 % | **0,92 / 25 %** (P≤0 0,10) |
ETH y la cesta 50/50 (examen): H3 mejora el Sharpe en +0,41 y +0,51 y baja la caída de 74 % a 30 % y de 68 % a 22 %.

**H5 índice top-10:** peor que BTC en los dos periodos (Sharpe 0,27 frente a 0,48; 0,81 frente a 0,93) y con más caída → **rechazado**.
Diversificar en altcoins no compensa: las que entran en el top 10 suelen hacerlo tras subir y luego se desinflan.
**H6 DCA:** invertir todo de golpe gana en el 64 % de los inicios (a 12 y a 24 meses), porque BTC sube más de lo que baja.
El DCA solo sirve para reducir el peor caso a 12 meses (x0,45 frente a x0,28): es una herramienta psicológica, no de rentabilidad.

## 3. Veredicto
- **Por el criterio estricto, H1–H3 NO se aprueban:** en el desarrollo con datos de Binance (2018–2021) ninguna mejora el Sharpe.
- **Lo que sí es robusto en TODOS los periodos (7 de 7, BTC y ETH):** la caída máxima baja muchísimo. Con H3, la caída de BTC pasa de
  67–85 % a 25–49 %, y el peor mes de −37 % a −16/−24 %, con un Sharpe igual o algo mejor (mejor en 4 de 5 ventanas de BTC).
  El precio es una rentabilidad menor en las grandes subidas.
- **Conclusión práctica:** si alguien quiere "tener BTC a largo plazo", la forma racional es **H3 (filtro de 200 días + exposición
  limitada por volatilidad)**: misma rentabilidad ajustada a riesgo con la mitad de la caída. No es una ventaja nueva sobre el mercado;
  es una mejor forma de soportarlo. Su Sharpe (≈ 0,9 en el examen) es parecido al del bloque D; en la Lección 31 se mide si aporta
  algo a la cartera o si es redundante con D.
