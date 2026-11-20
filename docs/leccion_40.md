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

## 1b. Comprobación añadida tras ver C1 (informativa, no aprobatoria)
En BTC los cuatro motores son resultados dentro de muestra. Solo A funciona fuera de BTC. Se mide la cartera con **solo el motor A**
(BTC+ETH+SOL, un tercio del capital por moneda, con el gestor de riesgo del monitor) como quinto bloque.

## 2. Resultados — `l40_salida.txt`, `l40_salida_motorA.txt`
Reproducción: en BTC el código da 569 operaciones (554 hasta ago-2026 + las posteriores) y 800 $ → 3 098 $, igual que su auditoría causal (3 103 $).

**C1 — Fuera de BTC (ETH y SOL, monedas no usadas para diseñarla):**
| Motor | BTC (dentro de muestra) | **ETH + SOL (fuera)** | ETH / SOL |
|---|---|---|---|
| **A · ráfaga de momentum (1 h)** | +0,81R (t 2,3) | **+0,67R (t 3,2, n 289)** ✅ | +0,86R / +0,50R |
| B · recuperación en tendencia (4 h) | +0,18R (t 2,5) | −0,04R (t −0,8) ❌ | −0,02R / −0,06R |
| C · momentum 15 min | +0,45R (t 3,9) | +0,08R (t 1,1) ❌ | +0,24R / −0,10R |
| D · corto por expansión (1 h) | +0,39R (t 2,6) | −0,01R (t −0,1) ❌ | +0,03R / −0,08R |
**Solo el motor A tiene ventaja fuera de BTC.** B, C y D funcionan únicamente en la moneda en la que se ajustaron: sobreajuste.
Con su gestor de riesgo: BTC 800 → 3 098 $; ETH 800 → 1 791 $; SOL 800 → 1 132 $.

**C2 — Como complemento (quinto bloque, 1/5):**
| | 2020-03→2022 | 2023→2026-10 |
|---|---|---|
| Cartera actual | Sharpe 2,36 / caída 7,5 % | Sharpe 1,78 / caída 8,2 % |
| + suite completa en BTC | 2,61 / 6,4 % | 2,01 / 6,9 % |
| **+ solo el motor A en BTC+ETH+SOL** | **2,52 / 5,9 %** | **1,93 / 6,7 %** |
La suite completa "pasa" C2, pero en BTC sus resultados son dentro de muestra (B, C y D no funcionan fuera), así que esa mejora está inflada.
**El motor A solo, en tres monedas, mejora el Sharpe y reduce la caída en las dos mitades** (correlación mensual con D 0,63, con la cartera 0,49).
A cambio, baja un poco la rentabilidad anual (27 % frente a 31 %), porque arriesga poco por operación (0,75 %).

## 3. Veredicto
- **Motor A: candidato serio a sexto bloque.** Es el primer hallazgo de fuera que supera nuestro filtro: funciona en monedas no vistas
  y mejora la cartera. Cautela: en el simulado en vivo (sep–nov 2026) sus 5 operaciones en BTC fueron casi todas stops; la muestra es mínima.
- **Motores B, C y D: rechazados** (sobreajustados a BTC).
- Siguiente paso recomendado: añadir el motor A al bot **en simulado** (BTC, ETH y SOL) y seguirlo unos meses antes de usarlo en real.
