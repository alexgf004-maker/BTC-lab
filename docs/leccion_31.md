# Lección 31 — ¿Mejora la cartera con lo aprendido?

## 1. Pre-registro (antes de calcular)
**Base:** la cartera actual (A carry, E carry inverso, B corto alt/BTC, D tendencia; 1/4 cada uno, reequilibrio mensual), con las series
diarias de la Lección 17. **Aproximación declarada para A:** como la serie diaria del carry ejecutable (3 huecos con reserva) no se guardó,
se usa la serie de A escalada para que su rentabilidad media sea la ejecutable (+3,6 % anual en lugar de +15,9 %): conserva el momento y
las correlaciones, no el nivel exacto de cada día.
**Mitades:** 2020-03 → 2022-12 y 2023-01 → 2026-10.

**I1 — Bloque de "hold inteligente"** (H3 de la Lección 27: BTC spot con filtro de 200 días y exposición limitada por volatilidad).
Carteras: (a) base; (b) base + H3 con 1/5 cada uno; (c) H3 en lugar de D. Se informa la correlación de H3 con D.
**Criterio:** Sharpe mayor y caída máxima no mayor que la base, en las dos mitades.

**I2 — Filtro de temporada de altcoins para B.** Índice de temporada = fracción de las 30 criptos más líquidas (point-in-time, sin BTC)
cuya rentabilidad de 90 días supera a la de BTC (definición habitual del "altseason index"), con datos hasta el día anterior.
Si el índice > 0,75, B no abre posiciones nuevas (las abiertas siguen con su stop).
**Criterio:** Sharpe de B mayor en las dos mitades **y** caída de B no mayor. Pruebas nuevas: 2.
