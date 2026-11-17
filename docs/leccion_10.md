# Lección 10 — Scalping de verdad: cuatro hipótesis en 1 y 5 minutos con ejecución conservadora

## 0. Qué se prueba y cómo
La Lección 1 descartó el scalping por costes sin probar reglas concretas. Aquí se prueban cuatro hipótesis clásicas,
con **entrada limit (maker)** donde tiene sentido y un simulador de ejecución en velas de 1 minuto.

**Modelo de ejecución (conservador):**
- Una orden limit solo se da por ejecutada si el precio la **atraviesa** (compra en L: mínimo de 1m ≤ L × (1 − 0,01 %)).
  Tocar el nivel no basta: equivale a suponer que somos los últimos de la cola.
- El objetivo (limit) se ejecuta igual: el máximo debe atravesarlo. El stop salta al tocarlo y sale a mercado.
- En la vela de ejecución puede saltar el stop, pero no el objetivo. Si una vela toca stop y objetivo, cuenta el stop.
- Costes: maker 0,02 %; taker 0,05 % + slippage 0,03 %. Salida por tiempo: taker.

**Datos:** velas de 1m de futuros, 2024-01 → 2026-10.
**Desarrollo:** BTC, ETH, SOL, BNB, XRP, DOGE. **Examen (una vez):** ADA, AVAX, LINK, LTC, BCH, DOT.

## 1. Hipótesis pre-registradas (señal en velas de 5m, ejecución en 1m, largos y cortos simétricos)

**C1 — Reversión al VWAP.** Causa: los excesos intradía respecto al precio medio ponderado por volumen los corrigen los
creadores de mercado. VWAP anclado a las 00:00 UTC. desv = cierre − VWAP; σ = desviación típica de desv en las 288 velas previas.
Señal (desde las 02:00 UTC): desv < −2,5σ y |desv| ≥ 0,4 % del precio → limit de compra en el cierre, válida 10 min.
Objetivo: el VWAP del momento de la señal. Stop: a la misma distancia por debajo (RR ≈ 1). Máximo 60 min.

**C2 — Ruptura del rango de apertura de EE. UU.** Causa: la apertura de la bolsa de EE. UU. concentra flujo direccional.
Rango = máximo y mínimo de 13:30–14:00 UTC; solo si mide entre el 0,3 % y el 2 %. De 14:00 a 16:00: primer cierre de 1m fuera
del rango → entrada a mercado en la apertura siguiente. Stop: el lado opuesto del rango (1R). Objetivo: 1,5R. Salida a las 20:00 UTC.
Un trade por día y activo.

**C3 — Continuación tras desequilibrio de flujo.** Causa: una ráfaga de compras agresivas refleja información o un gran
operador que aún no ha terminado. Vela de 5m con ≥ 65 % del volumen comprador agresivo, volumen ≥ 3× la media de 288 velas y
cierre > apertura → limit de compra en el cierre, válida 10 min. Stop: 1,5 × ATR14(5m), mínimo 0,35 %. Objetivo: 1R. Máximo 60 min.

**C4 — Rebote tras barrido de liquidez.** Causa: el precio perfora un mínimo reciente para ejecutar stops y, si no hay vendedores
reales, vuelve. Vela de 5m cuyo mínimo perfora el mínimo de las 48 velas previas (4 h) y cierra por encima de él, con volumen
≥ 2× la media → limit de compra en el cierre, válida 10 min. Stop: mínimo de la vela − 0,1 × ATR (se exige R ≥ 0,3 %).
Objetivo: 1,5R. Máximo 120 min.

## 2. Criterios
**Criba (desarrollo):** esperanza neta > 0 con t ≥ 3, PF ≥ 1,2, positiva en las dos mitades del periodo
(2024-01 → 2025-05 y 2025-06 → 2026-10) y en al menos 4 de los 6 activos.
**Examen:** esperanza neta > 0 con t ≥ 3, PF ≥ 1,2 y Deflated Sharpe ≥ 0,90 (354 + 4 pruebas), con un 0,25 % de riesgo por trade.
Se informa siempre de: trades, tasa de ejecución de las órdenes limit, win rate, y resultado BRUTO (sin costes) para ver
cuánto se llevan las comisiones.
