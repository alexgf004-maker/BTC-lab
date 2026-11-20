# Lección 40 — ¿Complementa la suite del BTC-Strategy-Monitor a nuestra cartera?

## 0. Qué se prueba
La suite `BTCUSDT_Strategy_Suite_v1.0_FINAL` (repositorio BTC-Strategy-Monitor): cuatro motores diseñados y ajustados SOLO en BTC
(A ráfaga de momentum 1h, B recuperación en tendencia 4h, C momentum 15m, D corto por expansión 1h), congelados el 13-sep-2026.
Histórico declarado: 554 operaciones, 800 $ → ~3 100 $ (2020–ago 2026). Simulado en vivo (sep–nov 2026): 800 → 771 $.
Se usa **el código del propio monitor sin cambiar nada** (señales, salidas, costes del 0,24 % por operación y gestor de riesgo).

## 1. Pre-registro (antes de calcular resultados)
**C1 — ¿Ventaja real fuera de BTC?** Los cuatro motores, idénticos, sobre ETHUSDT y SOLUSDT (perpetuos de Binance, velas de 15 min
2020-01 → 2026-10), monedas no usadas en su diseño. Por motor: resultado medio por operación (en R) y t, agrupando ETH y SOL.
Criterio: E[R] > 0 con t ≥ 2 en el conjunto ETH+SOL y positivo en cada una de las dos. (Exploratorio: no es una pieza nueva, es un complemento.)
Se informa también BTC (dentro de muestra) para comprobar que se reproducen sus cifras.
**C2 — ¿Complementa la cartera?** Serie diaria de la suite en BTC con su propio gestor de riesgo (y la versión en BTC+ETH+SOL con un
tercio del capital por moneda). Correlación con la cartera actual (bloques de la Lección 31: A ejecutable, E, B, D; 1/4 cada uno).
Cartera con la suite como quinto bloque (1/5 cada uno) frente a la actual.
Criterio: Sharpe mayor y caída máxima no mayor en las dos mitades (2020-03 → 2022-12 y 2023-01 → 2026-10).
Pruebas nuevas: 2.
