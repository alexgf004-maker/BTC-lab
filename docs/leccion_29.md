# Lección 29 — Scalping de verdad: creador de mercado y números redondos en días tranquilos

## 0. Por qué
En la Lección 10, el scalping que **toma** liquidez (órdenes a mercado) no tenía ni ventaja bruta: los costes de taker (0,07 % por lado)
son mayores que cualquier patrón de minutos. Pero los que viven del scalping de verdad hacen lo contrario: **dan** liquidez
(creadores de mercado). Cobran el diferencial entre compra y venta y pagan comisión de maker (0,02 % en VIP0, 0 % o negativa en niveles VIP).
Su enemigo es la **selección adversa**: te ejecutan justo cuando el precio va a moverse en tu contra. Esta lección lo mide de frente con
datos tick a tick (mejor precio de compra y venta con su cantidad, y cada operación) y una cola conservadora.
Además se comprueba la pista abierta de la Lección 26 (rebotes en números redondos los días tranquilos).

## 1. Pre-registro (antes de descargar ni calcular)
**Datos:** `bookTicker` (mejor compra/venta y cantidades, cada cambio) y `aggTrades` (cada operación con su lado agresor) de futuros USDT,
data.binance.vision (el bookTicker de futuros se publica hasta 2024-03-30).
**Monedas (regla fija):** las de puesto 5, 25 y 75 por volumen de los 30 días previos al 1-dic-2023 (excluidas stablecoins).
**Días (semilla 0):** desarrollo = 6 días al azar de 2023-07 → 2023-12; **examen = 6 días al azar de 2024-01-01 → 2024-03-29.**

**M1 — Creador de mercado simple.** Siempre una orden de compra en el mejor precio de compra y una de venta en el mejor de venta,
de 200 $ cada una. Si el mejor precio cambia, se cancela y se vuelve a poner **al final de la cola** del nuevo precio.
**Latencia 200 ms** (VPS en Europa → Binance). **Cola conservadora:** al entrar, delante de nosotros está toda la cantidad mostrada;
la cola solo avanza con operaciones a nuestro precio (las cancelaciones de otros no nos adelantan); una operación a un precio peor
que el nuestro nos ejecuta entera. **Inventario máximo:** 3 órdenes (600 $) por lado; al llegar al límite, solo se cotiza el lado que lo reduce.
Al final del día se cierra a mercado (taker 0,05 % + medio diferencial). Comisión maker **0,02 %** (VIP0); se informa también con 0 %.
**M2 — Selección adversa (medición independiente de la política):** para cada ejecución pasiva de M1, "markout" = (precio medio a +1 s,
+10 s y +60 s − precio de ejecución) × lado. Diferencial realizado = medio diferencial − selección adversa.
**Criterio M1:** resultado neto diario > 0 con t ≥ 3 en los días del examen, en las tres monedas por separado (comisión 0,02 %).

**R1 — Rebote en números redondos finos, solo en días tranquilos (pista de la Lección 26).** Mismos eventos y operación que la Lección 26
(orden limit en el nivel, stop a −2 ATR, objetivo +2 ATR, comisiones incluidas), con dos condiciones ex ante:
(a) volatilidad de las últimas 24 h (desviación típica de las rentabilidades de 1 h) por debajo de su mediana de los 30 días previos;
(b) solo el primer toque de cada moneda en cada día UTC. Mismo filtro para los niveles placebo.
**Criterio R1:** esperanza neta > 0 con t ≥ 3 agrupando por día en el examen (482 monedas nuevas) y positiva en desarrollo, y mayor que en placebo.
Pruebas nuevas: 2 (M1, R1); M2 es medición.

## 1b. Pre-registro adicional (escrito tras ver M1 y M2, antes de calcular M3)
M1 pierde antes de comisiones incluso con 1 ms de latencia (medición informativa): cotizar siempre al final de la cola del mejor precio
significa que te ejecutan cuando la cola se agota, que es justo cuando el precio va a atravesarte.
**M3 — Creador de mercado que se retira del lado peligroso** usando el hallazgo de la Lección 20 (el desequilibrio del libro predice el
siguiente movimiento): desequilibrio I = cantidad en la mejor compra / (cantidad en la mejor compra + cantidad en la mejor venta).
No se cotiza la compra si I < 0,30 (presión vendedora) ni la venta si I > 0,70. Todo lo demás como M1 (200 ms de latencia).
Mismos días y monedas. Criterio igual que M1 (neto diario > 0 con t ≥ 3 en el examen, en las tres monedas, maker 0,02 %).
