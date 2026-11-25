# Lección 48 — Ideas de Gemini (primera tanda)

El usuario pidió ideas a Gemini con un prompt que listaba lo ya probado (`docs/l48_gemini_ideas.md`, 10 hipótesis). Filtro:

| # | Idea | Decisión |
|---|---|---|
| 1 | Curva de volatilidad implícita de Deribit invertida → corto | Segunda tanda (datos de Deribit pesados) |
| 2 | Funding menos letras del Tesoro → corto en altcoins | **Descartada:** el mecanismo no se sostiene; deshacer un carry es vender spot **y recomprar el perpetuo**, neutro para el precio |
| 3 | Pérdida de paridad de stablecoins → largo BTC / corto altcoins | **Descartada:** 2–4 episodios en 6 años; imposible de validar |
| 4 | Agotamiento de bombas coreanas (dominancia de volumen en Upbit) → corto | **Esta tanda (U)** |
| 5 | Liberación de gamma tras el vencimiento mensual de Deribit | **Descartada:** no existe historia pública del interés abierto por strike |
| 6 | Lambda de Kyle asimétrica con aggTrades | Segunda tanda (procesamiento pesado; la lección 20 vio efectos minúsculos en microestructura) |
| 7 | Grandes contra pequeños en aggTrades | Segunda tanda (ídem) |
| 8 | Estrés de crédito y tipos reales (FRED) → corto altcoins | **Esta tanda (M)** |
| 9 | Monedas moribundas fuera del top 50 → corto | **Esta tanda (C)** |
| 10 | Prima de lotería (efecto MAX) largo-corto | **Esta tanda (X)**, con fuga declarada: la lección 11 ya vio el signo (IC −0,072) y la lección 15 (S5, corto contra BTC) falló |

Las cifras de "movimiento esperado" que da Gemini no tienen fuente y no se usan.

## 1. Pre-registro (subido antes de calcular ningún resultado)
Comunes: perpetuos USDT de Binance con funding real; desarrollo 2020–2022, examen 2023 → 2026-10; t con errores agrupados por
semana. Costes 0,07 % por lado (0,15 % en C, monedas poco líquidas).

**U — Agotamiento de bombas coreanas.** Universo: top 30 point-in-time con mercado KRW actual en Upbit (los deslistados de Upbit no
tienen datos: se declara). Velas de 4 h. Volumen de Upbit en dólares con el tipo implícito KRW-BTC(Upbit) / BTCUSDT(Binance).
`U` = volumen Upbit 24 h / (volumen Upbit 24 h + volumen del perpetuo de Binance 24 h).
Fase 1: `U` ≥ 3 × su mediana de los 90 días anteriores **y** subida de 24 h del perpetuo > +15 %.
Fase 2 (entrada, en las 24 h siguientes): primer cierre de 4 h en que el volumen de 4 h de Upbit sea ≤ 60 % de su máximo desde la
fase 1 **y** el cierre esté por debajo del VWAP de 8 h del perpetuo → **corto** a ese cierre.
Salida: +10 % (stop), −15 % (objetivo), o 72 h. Una operación por moneda a la vez.
Placebo: la misma regla con subidas de +15 % en las que `U` ≤ su mediana (sin dominancia coreana).

**M — Estrés de crédito y tipos reales.** FRED: BAA10Y (diferencial de crédito Baa; **sustituye** al high-yield que propone Gemini,
porque FRED solo publica el high-yield desde 2023-11) y DFII10 (tipo real a 10 años), con 2 días de retraso para no mirar al futuro.
`M` = z₂₅₂(cambio 5 días de BAA10Y) + z₂₅₂(cambio 5 días de DFII10).
Entrada a las 00:00 UTC si `M` ≥ 2: **corto** en cesta de las 15 altcoins de mayor beta frente a BTC (30 días) del top 30,
ponderada por inversa de volatilidad. Salida: `M` ≤ 0,5, 14 días naturales, o cesta +6 % (stop).
Placebo: la misma serie `M` desplazada ±15 días.

**C — Monedas moribundas.** Cada lunes 00:00 UTC, perpetuos fuera del top 50 por volumen de 30 días con volumen medio de 7 días
> 3 M$. Condiciones: volumen medio de 90 días ≤ 30 % del máximo de la media móvil de 30 días del último año; precio ≤ 40 % del
máximo de 365 días y bajo la media de 50 días; funding medio de 7 días > −0,01 % por 8 h. **Corto** equiponderado en hasta 15 (las
de mayor caída de volumen); rebalanceo semanal; stop individual +25 %.
Placebo: corto equiponderado en todas las monedas elegibles fuera del top 50 (sin las condiciones de deterioro).

**X — Prima de lotería largo-corto.** Cada 3 días a las 00:00 UTC, top 30. `L` = media de las 3 mayores subidas horarias de 14 días /
desviación horaria de 14 días, residualizada transversalmente frente a la rentabilidad y la volatilidad de 14 días.
**Corto** en las 6 de mayor residuo y **largo** en las 6 de menor, neutral en dólares, ponderado por inversa de volatilidad de 30
días; se excluyen de los cortos las monedas con funding de 24 h < −0,05 % por 8 h.

**Criterio de aprobación** (4 pruebas):
- U, M y C (eventos): media neta por operación (o por semana en C) > 0 en desarrollo **y** examen, t ≥ 2,5 en todo el periodo, y
  mejor que su placebo en los dos periodos.
- X (cartera continua): Sharpe neto ≥ 0,8 en desarrollo y en examen, y t ≥ 2,5 en todo el periodo.
Lo que pase va a doble comprobación y, si se confirma, a seguimiento en el bot.
