# Lección 12 — Cuatro estrategias diseñadas a partir de nuestros propios hallazgos

## 0. Cambio de enfoque
Hasta ahora se probaron ideas de manual. Aquí cada estrategia nace de una evidencia concreta de las lecciones anteriores
y busca ventajas que no dependan de predecir mejor que el mercado: tendencias en series neutrales, primas estructurales,
pagos mecánicos y ventas forzadas.

## 1. Pre-registro (commiteado antes de ver ningún resultado; solo se han contado los eventos de N3)

**N1 — Tendencia relativa altcoin/BTC (swing, neutral al mercado).**
*Evidencia de origen:* H6 (Lección 8): apostar por la reversión del ratio perdió con Sharpe −1,40 → los ratios tienen tendencia.
*Reglas:* serie = ratio altcoin/BTC en 4h (máximos y mínimos a partir de los cierres de 1h). Mismas reglas y parámetros que la
tendencia validada en la Lección 3, sin reajustar: filtro = ratio diario sobre (largos) o bajo (cortos) su EMA50; entrada en la
ruptura del máximo/mínimo de 120 velas; stop chandelier de 5 ATR. Ratio al alza → largo altcoin + corto BTC; a la baja → al revés.
Riesgo 1 % por trade, máximo 10 posiciones, universo point-in-time top 20. Costes: 0,28 % ida y vuelta (dos patas) + funding de ambas patas.
*Datos:* desarrollo = 57 monedas (las mismas en las que se vio H6); examen = las otras 161.

**N2 — Cesta contra la volatilidad (swing lento, neutral en beta).**
*Evidencia de origen:* Lección 11: volatilidad a 30d con IC −0,09 (t −12,7), estable en las dos mitades; la cartera neutral falló
por rotación, cortos caros y pesos iguales.
*Reglas:* el día 1 de cada mes, en el universo point-in-time top 25: largo en las 8 monedas de menor volatilidad de 30 días y
corto en las 8 de mayor. Pesos inversos a la volatilidad dentro de cada lado. Cada lado se escala por 1/beta (beta frente a BTC a 90 días)
para que la cartera sea neutral en beta; bruto total = 100 % del capital. Ningún corto supera el 5 % del capital.
Stop individual: un corto que sube un 50 % desde el rebalanceo se cierra hasta el mes siguiente. Sin rebalanceos intermedios.
Costes: 0,07 % por unidad rotada + funding real.
*Fuga declarada:* el signo de la señal se conoce de toda la muestra (y de la literatura: Frazzini y Pedersen, 2014).
Lo que se prueba es si la construcción la convierte en rentabilidad neta. Desarrollo = 57 monedas; examen = las otras 161.

**N3 — Captura del pago de funding (scalping de minutos, sin predicción).**
*Mecanismo:* quien tiene la posición en el instante de liquidación cobra o paga el funding. Con tasas extremas el pago es grande y conocido.
*Reglas:* eventos con |funding| ≥ 0,10 % en monedas con volumen medio ≥ 20 M$/día (30 días previos). Si la tasa es positiva, corto;
si es negativa, largo. Entrada a mercado al cierre del minuto T−2; salida a mercado al cierre del minuto T+15.
Resultado = |tasa| + movimiento del precio a favor − costes. Costes: taker 0,05 % + slippage 0,05 % por lado = **0,20 %** ida y vuelta.
Cartera: 20 % del capital por evento, máximo 5 a la vez. Se informa también con costes dobles (0,40 %).
*Datos:* velas de 1m alrededor de cada evento. División aleatoria por moneda (semilla 2028).

**N4 — Rebote tras purga de apalancamiento (swing de 24 h).**
*Evidencia de origen:* H3a (Lección 8) se quedó en Sharpe 0,95 sin distinguir cascadas reales; Lección 11: caída del interés abierto → mejor rentabilidad posterior.
*Reglas (velas de 1h, universo top 20):* en las últimas 4 horas, rentabilidad ≤ −3σ (σ de las rentabilidades de 4h de 30 días) **y**
caída del interés abierto ≥ 10 %. Compra al cierre; venta 24 h después. Una posición por moneda; 10 % del capital por trade.
Costes: 0,14 % + funding. Solo largos (los cortos tras subidas fallaron en H3b).
*Datos:* desarrollo = 57 monedas; examen = las otras 161 (con datos de interés abierto, sobre todo desde 2022).

## 2. Criterios
**Criba (desarrollo):** Sharpe neto ≥ 1,2, rentabilidad positiva en las dos mitades del periodo disponible y PF ≥ 1,3.
**Examen (una vez, solo lo que pase):** Sharpe ≥ 1,0, PF ≥ 1,3 y Deflated Sharpe ≥ 0,90 con 374 + 4 pruebas.
**Advertencia:** los 218 símbolos ya han pasado por análisis agregados (Lección 11). Para cada hipótesis el examen usa monedas
en las que ESA hipótesis no se ha mirado, pero la prueba definitiva de todo lo que pase es operar hacia delante.
