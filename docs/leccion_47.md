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
