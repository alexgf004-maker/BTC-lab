# Lección 51 — "El oro se opera con liquidez": barridos de liquidez en XAUUSD

Pregunta del usuario: muchos traders dicen que el oro se mueve "buscando liquidez" (los stops acumulados sobre máximos y bajo
mínimos obvios: el rango de Asia, el de Londres, el máximo y mínimo del día anterior). La idea: el precio barre ese nivel, salta los
stops y regresa; se opera en contra del barrido. Ya se probó en cripto (L33, CRT), forex (L35) y Nasdaq (L38, ICT), siempre sin
ventaja, pero **nunca en oro**, que es donde más se usa.

## 1. Pre-registro (subido antes de descargar los datos)
**Datos:** XAUUSD en velas de 1 minuto de HistData (hora EST fija = UTC−5 → se pasa a UTC), agregadas a 5 minutos, 2012 → 2026-10.
Horarios en UTC fijos (sin ajustar el horario de verano; se declara).

**O1 — Barrido del rango de Asia en la apertura de Londres.** Rango de Asia = máximo y mínimo de 00:00–06:00 UTC. Entre 07:00 y
10:00, la primera vela de 5 min que supera el máximo de Asia y **cierra por debajo** → corto al cierre; stop en el máximo alcanzado
desde las 07:00; objetivo el mínimo de Asia; si no se alcanza nada, salida a las 16:00. Espejo con el mínimo de Asia. Una operación
por día (la primera que aparezca).

**O2 — Barrido del rango de Londres en la apertura de Nueva York.** Rango = 07:00–12:00 UTC; ventana 13:00–16:00; objetivo el extremo
opuesto del rango; salida a las 20:00. Mismas reglas que O1.

**O3 — Barrido del máximo o mínimo del día anterior.** Velas de 1 h. Cuando una vela supera el máximo del día anterior (UTC) y cierra
por debajo → corto al cierre; stop en el máximo de esa vela; objetivo 2R; salida a las 21:00 UTC si no se alcanza nada. Espejo con
el mínimo. Una operación por día.

**Costes:** 0,02 % por lado (horquilla + comisión típicas del oro en una cuenta ECN); también se informa con 0,05 % por lado.
Resultado en R (riesgo = distancia al stop) y en %. Stop conservador: si en la misma vela se tocan stop y objetivo, cuenta el stop.

**Placebo** (para saber si la sesión importa): las mismas reglas con las ventanas desplazadas 3 horas (O1: rango 03:00–09:00, barrido
10:00–13:00, salida 19:00; O2: rango 10:00–15:00, barrido 16:00–19:00, salida 23:00; O3: "día" de 12:00 a 12:00 UTC).

**Criterio de aprobación** (3 pruebas): media neta por operación (con 0,02 % por lado) > 0 en desarrollo (2012–2018) **y** examen
(2019 → 2026-10), t ≥ 2,5 (agrupado por semana) en todo el periodo, y mejor que su placebo en los dos periodos.
