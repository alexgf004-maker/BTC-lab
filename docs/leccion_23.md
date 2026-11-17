# Lección 23 — Precios que se forman mal por diseño (ideas propias, no de manual)

## 0. Principio
Un precio es eficiente cuando quien lo forma tiene información y puede cubrirse. Se buscan situaciones de Binance donde falta una de las dos.

## 1. Pre-registro (antes de calcular ningún resultado)

**T1 — Mercados que duermen: el fin de semana de los perpetuos de acciones, ETFs y materias primas.**
De viernes a lunes el precio lo fijan traders de cripto sin la información de la bolsa y los creadores de mercado no pueden cubrirse.
*Hipótesis:* el movimiento del fin de semana (W) contiene exageración que revierte cuando abre el mercado real.
*Ventanas (UTC):* EE. UU.: W = viernes 21:00 → lunes 13:00; reacción R = lunes 13:00 → 16:00. Asia (Hong Kong, Corea): W = viernes 09:00 →
lunes 00:00; R = lunes 00:00 → 03:00. Materias primas (oro, plata, petróleo, gas, cobre, platino, paladio): W = viernes 21:00 → domingo 21:00;
R = domingo 21:00 → lunes 01:00.
*Regla:* si |W| ≥ 1 %, posición −signo(W) al inicio de R, cierre al final de R. Costes 0,14 % ida y vuelta.
*Datos:* 110 activos (excluidos índices sintéticos, stablecoins y los mal clasificados), división aleatoria por activo (semilla 2030).
*Estadístico:* resultado medio por fin de semana (promediando los activos de ese fin de semana) → t sobre fines de semana. Correlación W–R.
*Criterio:* desarrollo y examen con resultado neto > 0 y t ≥ 2 cada uno. **Aviso: muestra corta (20–45 fines de semana): evidencia exploratoria.**

**T2 — Acciones que son BTC disfrazado (MSTR, COIN, MARA, HOOD, IREN, HUT, BMNR, CRCL, MSTU, BITO).**
El fin de semana BTC se mueve y la acción debería moverse según su beta. *Desviación:* G = W − β·W_BTC (β de los 60 días hábiles previos).
*Hipótesis bilateral:* la reacción relativa R − β·R_BTC el lunes está relacionada con G (reversión si la relación es negativa).
*Regla:* posición = −signo(G) si |G| ≥ 1 % (o +signo si en desarrollo la relación resulta positiva), cubierta con β·BTC; mismo horario que T1.
*División temporal:* desarrollo = primera mitad de los fines de semana; examen = segunda mitad. Mismo criterio que T1.

**T3 — Choque contra el techo del funding (cambio de intervalo).**
Cuando el funding alcanza su límite, Binance acorta el intervalo de pago (8h → 4h → 1h): es el momento de máximo apalancamiento atrapado.
470 eventos en 326 monedas (`l23_cambios_intervalo.csv`), división aleatoria por moneda (semilla 2030).
*Descriptivo:* rentabilidad frente a BTC a +1 h, +24 h, +72 h y +7 días, y funding pagado, según el signo de la última tasa.
*Regla:* tomar el lado que COBRA el funding (largo si la tasa es negativa), cubierto con BTC, 72 h; stop si se mueve un 30 % en contra frente a BTC.
Costes 0,28 %. *Criterio:* criba: media neta > 0 con t ≥ 2 y PF ≥ 1,3; examen: t ≥ 3 y PF ≥ 1,3.

**T4 — Prima del perpetuo despegada del índice (convergencia).**
El perpetuo debe converger a su índice (media del spot de varios exchanges). *Regla:* si la prima horaria (premiumIndex) cierra < −0,5 %:
largo perpetuo + corto spot; si > +0,5 %: largo spot + corto perpetuo. Salida cuando |prima| < 0,1 % o a las 24 h. Se cobra o paga funding real.
Costes 0,38 % ida y vuelta (spot 0,10 % + perpetuo 0,05 % + deslizamiento, por lado). Desarrollo = monedas antiguas con spot; examen = nuevas con spot.
Mismos criterios que la criba y el examen de la Lección 17.
