# Lección 26 — Soportes y resistencias: ¿reacciona el precio en los niveles?

## 0. Por qué y cómo
Es la idea más básica del análisis técnico y no se había probado de frente. Referencia: Osler (2000, 2003, Reserva Federal de Nueva York):
en divisas, las órdenes de recogida de beneficios se acumulan EN los números redondos (→ rebotes) y los stops justo DETRÁS (→ aceleración al cruzar).
**Método:** cada nivel real se compara con un **nivel placebo** (el mismo nivel desplazado al azar entre 0,5 y 2 ATR, hacia arriba o abajo,
con semilla fija). Si el precio reacciona igual en el placebo, el nivel no tiene nada de especial.

## 1. Pre-registro
**Familias de niveles** (velas de 1h; un nivel solo existe desde que es conocido, sin mirar al futuro):
1. Máximos y mínimos de giro horarios: extremo de las 24 velas a cada lado (se conoce 24 h después); activo durante 30 días.
2. Máximos y mínimos de giro diarios: extremo de 5 días a cada lado; activo 60 días.
3. Máximo y mínimo del día anterior (UTC).
4. Máximo y mínimo de la semana anterior.
5. Números redondos, escalón fino: múltiplos de 10^(⌊log10 precio⌋ − 1) (BTC: 1000; una moneda de 2,37: 0,1).
6. Números redondos, escalón grueso: 5 veces el anterior (BTC: 5000; moneda de 2,37: 0,5).

**Evento de toque:** la vela alcanza el nivel viniendo del lado correcto (soporte: cierre anterior por encima; resistencia: por debajo).
Cada nivel cuenta solo en su primer toque. Distancia de medida d = 2 × ATR(14) horario en el momento del toque.
**Medidas:**
- *Rebote:* desde el nivel, ¿el precio se aleja +d (en el sentido del rebote) antes de cruzar −d? Bajo azar, ≈ 50 %.
- *Continuación tras ruptura:* tras el primer cierre al otro lado del nivel, ¿avanza +d más antes de volver −d?
Se compara real frente a placebo (diferencia y prueba de proporciones).
**Operación (solo para las familias cuyo rebote real supere al placebo):** orden limit en el nivel, stop a −d, objetivo +d (RR 1:1);
comisión maker 0,02 % en la entrada y el objetivo, y taker + deslizamiento en el stop.
**Datos:** desarrollo = 218 monedas antiguas (top 20 point-in-time), 2020-03 → 2026-10; examen = 482 nuevas (top 30). Una vez.
**Criterio:** diferencia real − placebo > 0 con z ≥ 3 en desarrollo y z ≥ 3 en examen; para operar, además, esperanza neta > 0 con t ≥ 3 en el examen.

## 2. Resultados de desarrollo (140 monedas que estuvieron en el top 20) — `l26_salida_desarrollo.txt`
| Familia | Toques reales | Rebote real | Rebote placebo | Diferencia (z por moneda-mes) |
|---|---|---|---|---|
| Giros de 1 h | 27 200 | 42,7 % | 46,9 % | **−4,2 % (−11,2)** |
| Día anterior | 43 386 | 47,9 % | 50,0 % | −2,2 % (−7,1) |
| Semana anterior | 6 078 | 41,7 % | 44,4 % | −3,1 % (−4,0) |
| Giros diarios | 4 087 | 39,6 % | 42,6 % | −2,9 % (−2,8) |
| Redondos finos / gruesos | 82 442 / 16 301 | 48,5 % / 47,5 % | 49,5 % / 49,8 % | −1,3 % (−5,0) / −1,6 % (−2,3) |
La continuación tras cruzar un nivel es igual que en los placebos (diferencias de −0,6 % a +1,1 %, no significativas).

**Hallazgo: los soportes y resistencias reales se ROMPEN más que los niveles placebo** (lo contrario del análisis técnico clásico).
Coherente con la segunda parte del mecanismo de Osler: los stops (y en cripto, las liquidaciones) se acumulan detrás de los niveles visibles,
y el precio los atraviesa para ejecutarlos. La hipótesis pre-registrada (rebote mayor que el placebo) queda **rechazada** en todas las familias.

## 3. Hipótesis NUEVA (registrada después de ver el desarrollo): operar la ruptura en el primer toque
Al tocar un nivel por primera vez: entrada en el sentido de la RUPTURA (vender en un soporte, comprar en una resistencia) a mercado en el
nivel (taker + deslizamiento 0,07 %); objetivo a d = 2 ATR más allá (limit, maker 0,02 %); stop a d en contra (taker 0,07 %). Vela de toque:
si alcanza el stop, cuenta como pérdida aunque también alcance el objetivo (conservador). Máximo 168 h.
Se compara con la misma operación en los niveles placebo. **Solo en el EXAMEN (482 criptos nuevas), una vez.**
Criterio: esperanza neta > 0 con t ≥ 3 agrupando por día **y** mayor que en los placebos.
Familias: giros de 1 h, día anterior, semana anterior (las de mayor diferencia). Se excluyen niveles ≤ 0 y eventos con d > 20 % del nivel.
