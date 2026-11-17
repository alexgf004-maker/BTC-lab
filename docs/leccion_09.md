# Lección 9 — Carry entre exchanges (Binance ↔ Hyperliquid) y examen de los nuevos listados

## 0. Motivo
El carry de funding es la única ventaja confirmada (tres veces), pero en Binance el funding está bajo desde 2025 y el capital
queda parado. En Hyperliquid (HL) el funding se paga cada hora y su nivel puede ser distinto.
Datos: API pública de HL (funding horario desde 2023-05-12; velas de 8h). Bybit bloquea esta región y OKX solo publica ~3 meses: descartados.

## 1. Pre-registro (antes de descargar los datos de HL)

**Universo:** monedas con perpetuo en HL y en Binance (de nuestros 218 símbolos). **División aleatoria por moneda (semilla 2027)**
en desarrollo y examen. En cada mitad, universo point-in-time: las 10 más líquidas por volumen de Binance de los 30 días previos.
**Periodo:** 2023-06 → 2026-10. Submitades: 2023-06 → 2024-12 y 2025-01 → 2026-10 (el periodo problemático).

**X1 — Spot en Binance + corto en el perpetuo de HL.** Reglas idénticas al carry validado (umbral bajo, H2): entra si el funding de HL
medio de 3 días > 0,015 % por 8h, sale si < 0,005 %; 4 huecos del 25 %; corto a 2x (nocional = 2/3 del hueco);
liquidación simulada si el máximo supera +45 %; reequilibrio al +20 %.
Costes por entrada o salida: spot Binance 0,10 % + HL taker 0,045 % + 0,02 % de slippage por pata.

**X2 — Largo en el perpetuo de Binance + corto en el de HL (diferencial de funding).** Entra si (funding HL − funding Binance) medio de
3 días > 0,015 % por 8h, sale si < 0,005 %. 4 huecos del 25 %, las dos patas a 2x (nocional = hueco completo).
Liquidación simulada si el precio se mueve ±45 % desde la referencia; reequilibrio al ±20 %.
Costes: Binance taker 0,05 % + HL taker 0,045 % + 0,02 % de slippage por pata.

**Criba (desarrollo):** Sharpe ≥ 1,7 (t ≈ 3 en 3,4 años), rentabilidad > 0 en las DOS submitades y PF ≥ 1,3.
**Examen (una vez):** Sharpe ≥ 1,0, PF ≥ 1,3 y Deflated Sharpe ≥ 0,90 con 351 + 2 + 1 pruebas.
Se informa de la ocupación y de la rentabilidad de 2025-26, que es lo que se quiere arreglar.
Riesgos no modelados que se anotan: riesgo de contraparte de HL (exchange descentralizado, capital en USDC en Arbitrum),
transferencias entre exchanges para reequilibrar márgenes y liquidez real en HL de las monedas pequeñas.

**H10 — Corto en nuevos listados cubierto con BTC: examen confirmatorio único.**
Falló la criba de la Lección 8 por tamaño de muestra (36 trades, t = 1,8). Se examina UNA vez, con las mismas reglas, en los 129
símbolos nuevos (que esta hipótesis no ha tocado). Aprobación a nivel de trade: n ≥ 50, media > 0 con **t ≥ 3**, PF ≥ 1,3.

## 2. H10 — Examen confirmatorio en 129 símbolos nuevos (una vez) — `l09_salida_h10.txt`

| n | Win rate | Media | Mediana | t | PF | Stops (−100 %) | Peor |
|---|---|---|---|---|---|---|---|
| 127 | **72 %** | +9,9 % | +25,0 % | **2,13** | 1,56 | 30 | −110 % |

Por año de listado (trades, media): 2020: 12, +35 % · 2021: 30, +15 % · 2022: 13, +20 % · 2023: 35, +4 % · 2024: 35, −1 % · 2025: 2.
Cartera con el 5 % por trade: Sharpe 0,85, CAGR 9,8 %, DD 28,8 %, hasta 15 posiciones a la vez.

**Veredicto: NO aprobada** (t = 2,13 < 3). El efecto existe (los listados nuevos caen frente a BTC en el 72 % de los casos),
pero uno de cada cuatro trades acaba en stop con pérdida total, y **la ventaja ha desaparecido en 2023-24**.
Otro ejemplo de win rate alto con cola de pérdidas grande.
