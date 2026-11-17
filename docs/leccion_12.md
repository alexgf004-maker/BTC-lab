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

## 3. Criba (desarrollo) — `l12_salida_criba.txt`

| | Sharpe | CAGR | DD máx. | n | Win rate | PF | Mitades | Veredicto |
|---|---|---|---|---|---|---|---|---|
| **N1 tendencia relativa alt/BTC** | 1,35 | 59,7 % | 40,1 % | 2590 | 40 % | 1,40 | +1743 % / +33 % | ✅ pasa |
| N2 cesta contra la volatilidad | 1,12 | 27,1 % | 32,3 % | 76 meses | 62 % | 2,65 | +236 % / +36 % | ❌ (Sharpe < 1,2) |
| N3 captura del pago de funding | −2,69 | −28,9 % | 90,1 % | 6429 | 41 % | 0,73 | −69 % / −68 % | ❌ |
| N4 rebote tras purga | 0,74 | 9,7 % | 15,8 % | 301 | 66 % | 2,26 | +23 % / +43 % | ❌ (Sharpe < 1,2) |

- **N1** se degrada con el tiempo: 2020–22 > +150 % anual; 2023 +42 %; 2024 +20 %; 2025 +2 %; 2026 −21 %. Apalancamiento nocional de hasta 6x.
- **N2:** 62 % de meses positivos, pero rotación mensual del 81 % (más de lo previsto) y dos años negativos (2023 y 2026).
- **N4:** +2,07 % por trade (mediana +1,60 %), pero las señales llegan en racimos (hasta 19 a la vez): agrupando por día, t = 2,28
  sobre 101 días. No es tan sólido como parece trade a trade.

### N3 en detalle: el mercado descuenta el funding como un dividendo
Tasa media cobrada +0,24 %; movimiento del precio en contra −0,28 %; bruto −0,04 %; neto −0,24 % (t = −14,6).
Perfil minuto a minuto (10 926 eventos): el precio cae ~0,24 % durante la hora previa y salta +0,32 % en el primer minuto tras T.

### N3b (exploración derivada, solo desarrollo): ¿se puede capturar el salto entrando justo después de T?
Con las operaciones individuales de los primeros 90 s tras las liquidaciones de las 00:00 (2937 eventos, peores precios, comisiones 0,10 %):

| Entrada | \|f\| ≥ 0,10 % | \|f\| ≥ 0,25 % | \|f\| ≥ 0,50 % |
|---|---|---|---|
| a 0,5 s | +0,14 % (t +12,8) | +0,28 % | +0,43 % |
| a 2 s | +0,10 % | +0,21 % | +0,33 % |
| a 5 s | +0,01 % | −0,07 % | −0,36 % |
| a 15 s | −0,10 % | −0,16 % | −0,31 % |

El salto ocurre de golpe entre los 2 y los 5 segundos. Binance documenta que el cobro real del funding puede desviarse hasta
15 segundos de la hora oficial: lo más probable es que las entradas anteriores a ~3 s sigan dentro del cobro y PAGUEN el funding
(0,24–0,97 %), más que la ganancia aparente. **No se considera ventaja.** Solo una prueba real con importe mínimo (¿se cobra funding
a una posición abierta a T+1 s?) lo resolvería; la probabilidad de que sea real se estima baja.

## 4. Examen de N1 (161 monedas restantes, una vez) — `l12_salida_examen.txt`

| | Sharpe | CAGR | DD máx. | n | Win rate | PF | Deflated Sharpe |
|---|---|---|---|---|---|---|---|
| N1 tendencia relativa | 0,89 | 30,7 % | 42,6 % | 2502 | 39 % | 1,26 | 0,35 → **NO aprobada** |

Por lado (informativo, división posterior):
| | Desarrollo | Examen |
|---|---|---|
| Ratio al alza (largo alt / corto BTC) | E +0,169R, PF 1,42 | E +0,017R, PF 1,04 |
| **Ratio a la baja (corto alt / largo BTC)** | **E +0,134R, PF 1,39, WR 43 %** | **E +0,138R, PF 1,43, WR 44 %** |

## 5. Conclusiones
1. **Ninguna de las cuatro queda aprobada** (382 pruebas acumuladas).
2. **Hilo común — la misma ventaja vista desde cuatro ángulos:** las altcoins débiles y volátiles pierden frente a BTC.
   Aparece en la Lección 11 (volatilidad, t −12,7), en H10 (los nuevos listados caen el 72 % de las veces), en N2 (62 % de meses
   positivos, PF 2,65) y en el lado corto de N1 (casi idéntico en dos conjuntos independientes de monedas: PF 1,39 y 1,43).
   Ninguna implementación supera por sí sola el filtro de pruebas múltiples, y todas sufren en 2026 (N1 −21 %/−37 %, N2 −5 %):
   es una prima estructural con riesgo de régimen (una "temporada de altcoins" la invierte), no un cajero automático.
3. El funding se descuenta en el precio con precisión de segundos: confirma que en plazos cortos el mercado es eficiente para un minorista.
4. Candidatos para seguimiento en papel (no aprobados): corto de altcoins débiles frente a BTC con confirmación de tendencia;
   cesta contra la volatilidad; rebote tras purga; modelo direccional de la Lección 11.
