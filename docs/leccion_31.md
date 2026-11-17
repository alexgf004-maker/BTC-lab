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

## 2. Resultados — `l31_salida.txt`
**I1 — Hold inteligente en la cartera: NO mejora.** Correlación de H3 con D: 0,45 diaria y 0,57 mensual (los dos van largos en BTC con tendencia).
| | 2020-03→2022: Sharpe / caída | 2023→2026-10: Sharpe / caída | Todo: anual / caída |
|---|---|---|---|
| (a) base 1/4 | **2,36 / 7,5 %** | 1,78 / **8,2 %** | +31,2 % / **8,2 %** |
| (b) base + H3, 1/5 | 2,18 / 10,6 % | 1,88 / 9,2 % | +31,7 % / 10,6 % |
| (c) H3 en lugar de D | 2,27 / 10,8 % | 1,84 / 9,8 % | +29,0 % / 10,8 % |
Añade caída sin mejorar el Sharpe en la primera mitad: es redundante con D y más expuesto a BTC. **Se mantiene la cartera actual.**

**I2 — Filtro de temporada de altcoins para B: NO mejora.** El índice supera 0,75 el 12 % de los días (25 % en 2021).
| | 2020-03→2022: Sharpe / caída | 2023→2026-10: Sharpe / caída |
|---|---|---|
| B sin filtro | **1,56 / 30,4 %** | 0,82 / 33,8 % |
| B con filtro | 1,43 / 34,8 % | 0,87 / 33,6 % |
En 2021, el año malo de B, el filtro lo empeora (−18 % → −29 %): el índice detecta la temporada de altcoins cuando ya ha subido mucho,
y los cortos que se evitan entonces son justo los que funcionan cuando la temporada se gira. Medir la temporada por rentabilidad pasada
llega tarde. **Se mantiene B sin filtro.**
