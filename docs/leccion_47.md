# Lección 47 — Indicadores de flujo de dinero: prima de Coinbase, prima kimchi y emisión de stablecoins

Los tres son indicadores que siguen los profesionales (CryptoQuant, Glassnode) como pistas de "quién está comprando".

## 1. Pre-registro (escrito y subido antes de descargar los datos)
**Datos:** Coinbase BTC-USD (1 h), Upbit KRW-BTC (1 d), spot Binance BTCUSDT (1 h), dólar/won de la Reserva Federal (FRED
DEXKOUS, se usa el del día hábil **anterior**), oferta total de stablecoins (DefiLlama, diaria, se usa la del día anterior).
Operación sobre el perpetuo BTCUSDT de Binance, con funding real y 0,07 % por lado en cada cambio de posición.
Desarrollo 2020–2022, examen 2023 → 2026-10.

**Indicadores** (convertidos en z-score frente a su propia historia de los 90 días anteriores, sin mirar al futuro):
- **CP — prima de Coinbase:** Coinbase / Binance spot − 1, media de las últimas 24 h. Signo esperado: **+** (los compradores de
  EE. UU. van por delante).
- **KP — prima kimchi:** Upbit en wones / (Binance × dólar/won) − 1, diaria. Signo esperado: **−** (la euforia minorista coreana
  marca techos).
- **SC — emisión de stablecoins:** cambio de 7 días de la oferta total. Signo esperado: **+** (dinero nuevo que entra).
- **CP4 — prima de Coinbase a 4 h:** la misma prima, media de 4 h, z frente a los 30 días anteriores, revisada cada 4 h.

**Regla:** al cierre de cada día UTC (cada 4 h en CP4): largo en BTC si signo × z > +1, corto si signo × z < −1, fuera si no.
Se mantiene hasta la siguiente revisión.

**Medidas:** Sharpe neto de la estrategia; correlación de rangos (IC) entre el indicador y la rentabilidad siguiente, con t de
errores robustos (Newey-West).

**Criterio de aprobación** (4 pruebas): Sharpe neto ≥ 0,8 en desarrollo **y** en examen, e IC con el signo esperado y t ≥ 2,5
en todo el periodo. Si pasa: doble comprobación y, si se confirma, bloque en seguimiento en el bot.

## 2. Resultados — `l47_salida.txt`
Un error del descargador (fechas y precios de Binance spot desalineados, todo NaN) se corrigió antes de leer resultados.
Comprobación: la prima de Coinbase media es +0,011 %, con el 90 % de las horas entre −0,13 % y +0,15 %. Es razonable.

| Indicador | IC (signo esperado), t | Desarrollo: Sharpe | Examen: Sharpe | ¿Pasa? |
|---|---|---|---|---|
| CP prima de Coinbase (diaria) | +0,017, t +0,88 | −0,40 | +1,13 | No |
| KP prima kimchi (diaria) | −0,029, t −1,46 (signo contrario) | +0,38 | −0,03 | No |
| SC emisión de stablecoins | +0,011, t +0,56 | −0,05 | +0,43 | No |
| CP4 prima de Coinbase (4 h) | +0,016, t +2,13 | +0,52 | +0,82 | No (le falta en desarrollo y en t) |

BTC comprado siempre: Sharpe +0,76 y +1,10 en los mismos periodos.

**Rechazados los cuatro.** La prima de Coinbase en 4 horas es lo más cercano: gana en los dos periodos y apunta en la dirección
esperada, pero no llega al listón (t 2,13 < 2,5; Sharpe 0,52 < 0,8 en desarrollo) y por sí sola no mejora a comprar y mantener.
No se ajusta nada después de ver esto. La prima kimchi y la emisión de stablecoins no predicen nada a 1 día: son buenos
termómetros del ánimo del mercado, pero no dan ventaja para operar.
