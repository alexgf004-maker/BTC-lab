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

## 2. Resultados (2020-03 → 2026-10) — `l07_salida.txt`

**Bloques por separado**
| Bloque | Sharpe | CAGR | DD máx. | Win rate | PF | Notas |
|---|---|---|---|---|---|---|
| A carry (2x, 4 huecos) | 4,77 | 12,6 % | 1,0 % | 79 % | 318 | 53 episodios; **1 liquidación** (frente a 29 a 3x); invertido el 28 % del tiempo |
| B tendencia BTC/ETH | 1,05 | 33 % (del bloque) | 33,9 % (del bloque) | 41 % | 2,26 | 120 trades |

**Correlación mensual entre bloques: 0,07** → se diversifican casi por completo.

**Cartera combinada (80 % carry / 20 % tendencia)**
| Riesgo por trade de tendencia (sobre el total) | Sharpe | CAGR | DD máx. | Peor mes | Meses positivos |
|---|---|---|---|---|---|
| 0,5 % | 3,20 | 14,3 % | 4,0 % | −1,0 % | 52 % |
| 1,0 % | 2,33 | 18,4 % | 7,8 % | −2,0 % | 53 % |
| **2,0 %** | **1,79** | **26,0 %** | **14,9 %** | **−3,8 %** | 43 % |

Rentabilidad anual con el 2 %: 2020 +58 %, 2021 +74 %, 2022 −7 %, 2023 +37 %, 2024 +24 %, 2025 +11 %, 2026 −3 % (hasta octubre).

## 3. Decisión (regla pre-registrada: mayor CAGR con DD ≤ 20 %)
**Riesgo de tendencia del 2 % por trade sobre el capital total**, 80 % del capital para el carry.

Advertencias:
- **El carry no ha abierto ninguna posición en 2025-26**: el funding no ha superado el umbral. La cartera depende de que
  vuelvan las fases de euforia; mientras tanto, el carry es capital parado (no se ha modelado ningún rendimiento por él).
- Con el 2 %, el bloque de tendencia llega a ~6x de nocional sobre su 20 % de margen (≈1,2x del capital total). En Binance:
  margen cruzado en la cartera de futuros y apalancamiento máximo 10x; la distancia a la liquidación (~15 %) es mayor que la del stop (3-6 %).
- Resultados dentro de muestra: **no hay examen nuevo posible**. La prueba es la ejecución hacia delante.
