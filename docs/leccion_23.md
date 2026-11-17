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

## 2. T1 y T2 — resultados — `l23_salida_T1_T2.txt`
| | Desarrollo: corr(W, R) / neto por fin de semana (t) | Examen: corr(W, R) / neto por fin de semana (t) |
|---|---|---|
| T1 todos | −0,02 / −0,05 % (−0,15) | −0,00 / −0,08 % (−0,32) |
| T1 Asia | **−0,33** / +1,46 % (+3,54) | **−0,25** / +0,14 % (+0,20) |
| T1 EE. UU. | +0,01 / −0,16 % | +0,04 / −0,18 % |
| T2 acciones-BTC | +0,21 / −0,44 % (−1,03) | +0,12 / −0,38 % (−0,93) |
**T1 y T2: NO aprobadas.** En Asia la reversión aparece en los dos conjuntos (correlaciones −0,33 y −0,25), pero el resultado operable del examen no es significativo.

## 3. T1b (prueba NUEVA, registrada después de ver T1): la ventana correcta para EE. UU.
*Razonamiento:* los futuros de índices de EE. UU. (CME) reabren el domingo a las 22:00 UTC (horario de verano) o 23:00 (invierno).
A las 13:00 del lunes los perpetuos ya han incorporado esa información: la reacción debe medirse el domingo por la noche.
*Ventanas:* W = viernes 21:00 → domingo 21:00; R = domingo 21:00 → lunes 03:00. Activos de EE. UU. (no Asia, no materias primas).
Misma regla y criterio que T1, misma división por activo. Cuenta como prueba adicional.

### Resultado de T1b — `l23_salida_T1b.txt`, `l23_auditoria_T1b.txt`
| | Activos | Corr(W, R) | Pendiente | Operaciones | Neto por operación | t (por fin de semana) | Acierto |
|---|---|---|---|---|---|---|---|
| Desarrollo | 59 | −0,39 | −0,56 | 434 | +1,24 % | +2,66 | 61 % |
| **Examen** | 53 | **−0,45** | −0,55 | 358 | **+0,99 %** | **+3,64** | 63 % |
**T1b APROBADA (exploratoria).** El movimiento de fin de semana de los perpetuos de acciones y ETFs de EE. UU. revierte en torno a un 55 %.

**Auditoría:**
- Precio de cierre: +1,17 % (t 2,86); precio medio ponderado por volumen: +1,11 % (t 3,65) → no es rebote de un precio aislado.
- Entrada 1 / 2 / 3 h más tarde: +1,03 % / +0,87 % / +0,72 % → la ventaja dura horas.
- Costes de 0,3 %: +0,96 % (t 2,46); de 0,5 %: +0,76 % (t 1,78).
- La reversión se concentra entre el lunes 00:00 y 03:00 UTC (pendiente −0,37), con la sesión asiática y los futuros de EE. UU. ya abiertos.
- Cortos (fin de semana al alza): +0,77 %, 58 % de acierto; largos (a la baja): +1,80 %, 67 % → no es un sesgo direccional.
- 95 de 105 activos positivos; ETFs apalancados +1,72 %, resto +1,08 %. Sin los 3 mejores fines de semana: +0,50 % (t 2,40).
- **Límites:** solo ~29 fines de semana (2026); volumen en la hora de entrada: mediana 52 k$, p25 9 k$ → **capacidad muy pequeña**
  (operaciones de pocos miles de dólares por activo). Mecanismo plausible: el fin de semana el precio lo fijan traders sin cobertura;
  al reabrir los mercados de referencia, los creadores de mercado devuelven el precio a su valor.

## 4. T3 — Choque contra el techo del funding — `l23_salida_T3.txt`
326 monedas (primer choque de cada una). Descriptivo (mediana, frente a BTC):
| | 24 h | 72 h | 7 días | Funding en 7 días |
|---|---|---|---|---|
| Tasa negativa (cortos pagan), n = 177 | −8,9 % | −10,9 % | **−18,0 %** | −10,6 % |
| Tasa positiva (largos pagan), n = 101 | −2,3 % | −4,3 % | −11,3 % | +0,2 % |
Operación pre-registrada (el lado que cobra, 72 h): media +2,7 %, mediana −2,1 %, t 0,98, PF 1,38 → **no pasa la criba.**
Observación (no examinable, se vio en todas las monedas): cuando el funding negativo choca con el techo, los cortos tienen razón;
la caída posterior supera lo que pagan de funding.

## 5. T4 — Prima del perpetuo despegada del índice — `l23_salida_T4.txt`, `l23_auditoria_T4.txt`
**Tal como se pre-registró** (entrar al precio del mismo cierre en que se observa la prima):
| | n | Neto medio | t | Win rate | PF |
|---|---|---|---|---|---|
| Desarrollo (203 monedas) | 6548 | +0,65 % | +17,8 | 70 % | 5,4 |
| Examen (172 monedas) | 2647 | +1,44 % | +18,0 | 85 % | 8,9 |
Pasa criba y examen. **La auditoría lo matiza mucho:**
| Entrada | Perpetuo barato (exige spot prestado): neto / win rate / convergencia / funding | Perpetuo caro (sin préstamo): neto |
|---|---|---|
| Mismo cierre (pre-registro) | dev +1,05 % / 76 % · examen +1,69 % / 89 % | dev +0,09 % · examen −0,13 % |
| 1 h después | dev +0,51 % / 46 % / +0,49 % / +0,42 % · examen +1,33 % / 67 % / +0,65 % / +1,08 % | dev −0,14 % · examen −0,48 % |
| 2 h después | dev +0,35 % · examen +1,18 % | dev −0,04 % · examen −0,27 % |
1. **La mitad de la convergencia ocurre en la primera hora** (la prima pasa de 1,1 % a 0,6 %): el resultado real depende de la velocidad del bot.
2. **Solo funciona el lado que exige vender spot prestado**; el lado sin préstamo pierde en cuanto la entrada se retrasa.
3. **Gran parte del beneficio es funding negativo cobrado** (+0,4 % a +1,1 % por operación): es la misma prima que el carry inverso.
**Veredicto: real, pero NO es una pieza independiente.** Es el carry inverso visto con una lupa de una hora: sirve como **regla de
entrada** para el carry inverso (entrar cuando el perpetuo se abarata frente al spot), no como estrategia aparte.

## 6. Conclusiones de la lección
1. **Hallazgo nuevo y propio: T1b.** Los perpetuos de acciones de EE. UU. exageran el fin de semana y revierten ~55 % al reabrir los mercados.
   Robusto en la auditoría, pero con poca historia (29 fines de semana) y capacidad pequeña: **candidato a operar en pequeño y validar en real.**
2. T4 mejora el carry inverso (momento de entrada), no añade una pieza.
3. T1 en Asia, T2 y T3: no aprobadas.
4. Pruebas acumuladas: ~405.
