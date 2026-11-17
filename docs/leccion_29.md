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

## 2. Resultados
### R1 — Números redondos en días tranquilos — `l29_salida_R1.txt`: RECHAZADA
| | Real: E por operación | Real: por día (t) | Placebo: E por operación | Placebo: por día (t) |
|---|---|---|---|---|
| Desarrollo, todos los toques | −0,051R | +0,073 (+8,7) | −0,032R | +0,089 (+10,7) |
| Desarrollo, tranquilos + primer toque | −0,048R | +0,034 (+2,8) | −0,020R | +0,050 (+4,2) |
| Examen, todos los toques | −0,063R | +0,066 (+7,7) | −0,054R | +0,077 (+9,1) |
| Examen, tranquilos + primer toque | −0,013R | +0,035 (+2,9) | **+0,008R** | +0,058 (+4,9) |
**La pista de la Lección 26 era un artefacto estadístico:** los niveles al azar dan el mismo "positivo por día" (incluso mayor).
Al promediar por día, los días tranquilos (pocos toques, que suelen salir bien) pesan tanto como los volátiles (muchos toques, que salen mal).
Pero "tranquilo" solo se sabe al final del día: con un filtro de volatilidad conocido de antemano, la operación sigue perdiendo, y los
números redondos no son mejores que niveles al azar.

### M1/M2 — Creador de mercado — `l29_salida_mm.txt`, `l29_mm_dias.csv`: RECHAZADO
| Fase / moneda | Diferencial mediano | Selección adversa a 60 s | Bruto (sin comisión) | **Neto (maker 0,02 %)** | t (días) |
|---|---|---|---|---|---|
| Desarrollo XRP / LTC / STX | 1,9 / 1,5 / 1,8 pb | −0,7 / −0,9 / −1,5 pb | −0,7 / −0,9 / −1,4 pb | −2,7 / −2,9 / −3,4 pb | −2,6 / −3,5 / −2,1 |
| **Examen XRP / LTC / STX** | 1,7 / 1,3 / 0,7 pb | −0,7 / −1,2 / −1,4 pb | −0,8 / −1,2 / −1,4 pb | **−2,8 / −3,2 / −3,4 pb** | −1,7 / −1,7 / −5,0 |
(pb = puntos básicos = 0,01 % del nocional negociado). El simulador ejecuta el 0,5 % del volumen de XRP y el 6 % del de STX.

**Sensibilidad a la latencia (informativa, XRP y STX, un día):** pérdida bruta de −0,85/−1,63 pb con 200 ms, −0,56/−1,23 pb con 10 ms y
−0,50/−1,10 pb con 1 ms. **Ni con la velocidad de un profesional gana** una cotización que se pone al final de la cola.

### M3 — Creador de mercado con señal de desequilibrio — `l29_salida_m3.txt`: RECHAZADO
Cotiza menos (la mitad de volumen), pero pierde lo mismo por unidad negociada: bruto −1,1 / −1,2 / −1,3 pb en el examen; neto −3,1 a −3,3 pb.

## 3. Por qué el scalping no es viable para nosotros (la aritmética)
1. **El diferencial de los perpetuos líquidos es de 1 tick ≈ 1–2 pb.** La comisión de maker VIP0 es 2 pb **por lado**: una vuelta completa
   cuesta 4 pb, el doble de todo el diferencial que se puede cobrar.
2. **Aunque la comisión fuera 0, se pierde antes de comisiones:** la selección adversa (0,7–1,5 pb) es mayor que el medio diferencial
   (0,5–1 pb). Quien está al final de la cola solo se ejecuta cuando la cola se agota, y eso pasa justo antes de que el precio la atraviese.
3. **Los profesionales que viven de esto** tienen tres cosas que un particular no puede conseguir: prioridad en la cola (llegan los primeros
   a cada nuevo precio, en microsegundos), comisiones negativas (les pagan por dar liquidez) y modelos de predicción de muy corto plazo
   con datos de todo el libro. Sin las tres, la ventaja es negativa.
4. Con esta lección, el scalping queda probado por los dos lados: **tomando liquidez** (Lección 10: los costes de taker superan cualquier
   patrón) y **dando liquidez** (Lección 29: la selección adversa supera el diferencial). Para nuestro nivel de comisiones y latencia,
   **el scalping no es viable**. Lo razonable son horizontes de horas a semanas, donde la ventaja por operación (0,5–5 %) supera de largo los costes.
