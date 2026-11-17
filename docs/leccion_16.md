# Lección 16 — Examen de "pescar las mechas sin stop" y cartera combinada

## 1. Pre-registro (antes de ver resultados)

**Examen de W3 (mechas sin stop) en las 482 criptos nuevas** (nunca usadas por esta familia).
Reglas idénticas a la Lección 14: compra limit a 5σ bajo el cierre de la hora anterior; objetivo a media vuelta; sin stop; salida a las 24 h.
Riesgo nominal 0,25 % por trade, máximo 10 posiciones, universo point-in-time top 30 (como S1).
Aprobación: Sharpe ≥ 1,0, PF ≥ 1,3 y Deflated Sharpe ≥ 0,90 con 393 pruebas.

**Cartera combinada** (todas las piezas ya conocidas: es construcción, no descubrimiento).
Bloques, cada uno simulado sobre su propio capital, 2020-03 → 2026-10:
- A. Carry de funding spot-perpetuo en Binance (versión de umbral bajo de la Lección 8; 4 huecos; corto a 2x), monedas con spot.
- B. S1 corto de altcoins débiles frente a BTC, sobre las ~700 criptos (218 antiguas + 482 nuevas), top 30 point-in-time, 1 % de riesgo.
- C. W3 mechas sin stop, mismas ~700 criptos, top 30, 0,25 % de riesgo — **solo si aprueba el examen**.
- D. Tendencia en BTC y ETH (Lección 3), 5 % de riesgo sobre el bloque.
Pesos: **igual contribución al riesgo** (inversos a la volatilidad diaria de cada bloque en los 365 días previos; los primeros 365 días,
pesos iguales), reequilibrio mensual. Comparación: pesos iguales.
Se informa de: correlaciones, Sharpe, CAGR, caída máxima, peor mes y rentabilidad por año. Después se escala la cartera a un objetivo
de caída máxima histórica del 20 % (apalancamiento único para toda la cartera).

## 2. Examen de W3 (mechas sin stop) en 482 criptos nuevas — `l16_salida_examen_W3.txt`
| Sharpe | CAGR | DD máx. | Trades | Win rate | PF | E por trade | Peor trade | Deflated Sharpe |
|---|---|---|---|---|---|---|---|---|
| 1,13 | 11,5 % | 11,4 % | 3000 | 77 % | 1,28 | +0,091R | −23,8R | 0,58 → **NO aprobada** |

En las criptos nuevas la ventaja por trade se reduce a la mitad (+0,09R frente a +0,19–0,22R) y aparece una cola mucho peor (−23,8R):
en monedas nuevas, una caída del 5σ puede ser el inicio de un colapso, no una mecha. **W3 queda fuera de la cartera.**

## 3. Cartera combinada (2020-03 → 2026-10) — `l16_salida_cartera.txt`
**Bloques sobre su propio capital**
| Bloque | Sharpe | CAGR | DD máx. | Peor mes | Meses + |
|---|---|---|---|---|---|
| A carry (211 monedas con spot, 76 episodios) | 4,69 | 15,9 % | 2,4 % | −1,8 % | 45 % |
| B S1 corto alt/BTC (700 criptos, 2091 trades) | 1,13 | 44,8 % | 33,8 % | −16,5 % | 51 % |
| D tendencia BTC/ETH (120 trades) | 1,06 | 33,9 % | 33,9 % | −12,9 % | 33 % |

Correlaciones mensuales: A–B −0,21; A–D +0,06; B–D −0,04. **Prácticamente independientes.**

| Año | A carry | B S1 | D tendencia | **Cartera 1/3 cada uno** |
|---|---|---|---|---|
| 2020 | +16,5 % | +113,6 % | +116,7 % | **+84,6 %** |
| 2021 | +98,4 % | −18,4 % | +42,8 % | **+36,3 %** |
| 2022 | +0,2 % | +160,1 % | −16,5 % | **+33,2 %** |
| 2023 | +5,0 % | +40,0 % | +85,7 % | **+50,1 %** |
| 2024 | +12,4 % | +96,6 % | +29,4 % | **+51,0 %** |
| 2025 | −1,8 % | +30,4 % | +24,5 % | **+18,7 %** |
| 2026 (a oct.) | 0,0 % | −27,3 % | −9,2 % | **−12,0 %** |

**Cartera con pesos iguales: Sharpe 1,79, CAGR 36,4 %, caída máxima 15,8 %, peor mes −5,8 %, 64 % de meses positivos.**
Ningún año negativo hasta 2026: cada año perdedor de un bloque lo compensó otro (2021: S1; 2022: tendencia; 2025: carry).

**La regla de pesos pre-registrada (igual contribución al riesgo) es engañosa:** el carry está parado la mayor parte del tiempo, su
volatilidad parece mínima y recibe el 90–97 % del capital. Resultado aparente: Sharpe 2,14 y, escalada al 20 % de caída, CAGR 59 %;
pero eso supone apalancar 2,5x un bloque que en 2025–26 no hace nada. **Se descarta; la referencia es la cartera de pesos iguales.**

## 4. Advertencia principal: la peor caída es AHORA
La caída máxima de la cartera (−15,8 %) va de 2025-08-13 a 2026-08-13, y a 31-oct-2026 sigue un 14,6 % bajo el máximo.
En 2026 fallan las tres piezas a la vez: el funding está bajo (carry parado), las altcoins débiles rebotan frente a BTC (S1 −27 %)
y no hay tendencias sostenidas en BTC/ETH (−9 %). Nueve de los últimos doce meses son negativos.
Empezar a operar ahora es empezar en el régimen más desfavorable de los siete años: puede ser el momento previo a la recuperación
(como en otras caídas) o el inicio de un cambio de régimen. Los datos no permiten distinguirlo.

## 5. Conclusiones
1. Cartera final de referencia: **1/3 carry, 1/3 S1, 1/3 tendencia BTC/ETH**, sin apalancamiento adicional (o como máximo 1,25x,
   que en la historia lleva la caída al ~20 %).
2. W3 no supera el examen: el "pescar mechas" funciona en monedas consolidadas, no en nuevas; queda como candidata solo para las 218 antiguas.
3. La diversificación funciona: tres ventajas pequeñas e independientes dan un resultado mucho mejor que cualquiera de ellas.
