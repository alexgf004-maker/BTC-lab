# Lección 7 — Cartera combinada: carry (núcleo) + tendencia en BTC y ETH

## 0. Naturaleza de esta lección
Ya no quedan datos históricos sin ver: aquí **no se descubre ventaja nueva**, se decide **cómo repartir capital y riesgo**
entre dos piezas ya validadas. La validación final será hacia delante (testnet y real pequeño).

## 1. Pre-registro
**Bloque A — Carry de funding** (Lección 6, sin cambios de señal), universo point-in-time top 20 de los 89 activos:
- Cambio solo de riesgo: pata corta a **2x** (spot 2/3 y margen 1/3 de cada hueco; nocional = 2/3 del hueco).
  Liquidación simulada si el máximo intravela supera el +45 % desde la referencia; reequilibrio al +20 %.
- **4 huecos del 20 %** = hasta el 80 % del capital.

**Bloque B — Tendencia en BTC y ETH** (reglas de la Lección 3: ruptura de 20 días en 4h, chandelier m = 5, filtro EMA50 diaria):
- El 20 % del capital queda reservado como margen de futuros.
- Riesgo por trade (sobre el capital TOTAL) ∈ {0,5 %; 1 %; 2 %}.

**Combinación:** capital único; los resultados de cada bloque se suman cada día (pesos 80/20, reequilibrio mensual).
**Regla de elección (fijada ahora):** la configuración de **mayor CAGR con DD máximo histórico ≤ 20 %**.
Se informa también de cada bloque por separado y de su correlación.
