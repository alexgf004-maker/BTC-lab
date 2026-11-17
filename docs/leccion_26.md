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
