# Lección 13 — Tres líneas con mecanismos y datos nuevos

## 1. Pre-registro (antes de calcular ningún resultado)

**W1 — Pescar las mechas (dar liquidez a vendedores forzados).**
*Origen:* comprar DESPUÉS de una cascada se quedó cerca (H3a Sharpe 0,95; N4 WR 66 %, PF 2,26) pero entra tarde y a mercado.
Aquí la orden ya está en el libro y quien vende en la mecha es el liquidado.
*Reglas (velas de 1h, universo point-in-time top 20):* al empezar cada hora, para cada moneda sin posición, compra limit en
`L = cierre anterior × (1 − 5σ)`, con σ = desviación típica de las rentabilidades horarias de los 30 días previos.
Se ejecuta si el mínimo de la hora atraviesa L (maker 0,02 %). D = cierre anterior − L.
Objetivo: limit en L + 0,5·D (media vuelta), desde la hora siguiente, válido 24 h (maker). Stop: L − D (taker 0,05 % + 0,02 %);
si en la misma vela de entrada el mínimo toca el stop, se da por perdido. Si en 24 h no pasa nada, salida a mercado.
Riesgo: 0,5 % del capital por trade (pérdida en el stop), máximo 10 posiciones. Solo largos.
*Datos:* desarrollo = 57 monedas; examen = las otras 161.
*Criba:* Sharpe ≥ 1,2, positivo en las dos mitades y PF ≥ 1,3. *Examen:* Sharpe ≥ 1,0, PF ≥ 1,3, Deflated Sharpe ≥ 0,90 (384 pruebas).

**B1 — Carry con futuros trimestrales (rendimiento fijado al entrar).**
*Origen:* el carry es la única ventaja aprobada; con perpetuos depende de que el funding siga alto. Con un futuro con vencimiento,
la diferencia de precio con el spot (la base) se cobra íntegra al vencer.
*Reglas:* BTC y ETH, 50 % del capital cada uno. Cada día a las 00:00 UTC, si no hay posición: entre los trimestrales USDT con
≥ 20 días hasta el vencimiento, el de mayor base anualizada; si es ≥ 8 %, comprar spot y vender el futuro por el mismo importe
(spot 2/3 del hueco, margen 1/3 → corto a 2x). Mantener hasta el vencimiento.
Costes: spot 0,12 % al entrar y al salir, futuro 0,07 % al entrar y 0,02 % al vencer; 0,10 % del nocional cada vez que el precio sube
un 20 % (reponer margen); penalización del 1,5 % si sube un 45 % en un día sin reponer.
*Evaluación:* no es una apuesta estadística sino un arbitraje con convergencia garantizada: se informa del rendimiento realizado por año,
del tiempo invertido y de la caída máxima a mercado. Informativo también con umbrales del 5 % y del 12 %.

**C1 — Valoración en cadena + tendencia para BTC (swing largo / posición).**
*Datos nuevos:* ratio MVRV (valor de mercado / valor realizado = precio medio al que se movió cada moneda por última vez), diario desde 2011.
*Reglas (umbrales publicados y de uso común, no ajustados):* invertido al 100 % en BTC si (precio > media de 200 días **y** MVRV < 3,5)
o si MVRV < 1,0 (valor profundo, aunque la tendencia sea bajista); en otro caso, fuera. Decisión con datos del día anterior; 0,10 % por cambio.
*Comparación:* comprar y mantener, y solo tendencia (precio > media de 200 días).
*Periodos:* 2011–2019 (referencia) y **2020–2026 (prueba)**. Se aprueba como filtro si en 2020–2026 mejora a la vez el Sharpe y la caída
máxima frente a solo tendencia. *Aviso:* hay muy pocos ciclos (3–4): la evidencia estadística es débil por construcción.
