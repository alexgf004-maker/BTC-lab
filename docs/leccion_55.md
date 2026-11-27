# Lección 55 — Replicar las observaciones posteriores en monedas nunca usadas + momentum intradía

Varias lecciones dejaron observaciones hechas **después** de ver los resultados, que no podían aprobarse con los mismos datos.
La forma limpia de validarlas es repetir la regla, sin tocarla, en monedas que nunca se usaron: los puestos **31 a 100** por volumen
de cada mes (point-in-time, con deslistadas). Todas las lecciones anteriores usaron el top 30 (o el top 50 excluido en la L48 C).

## 1. Pre-registro (subido antes de calcular y antes de descargar los datos spot nuevos)
Universo nuevo: puestos 31–100 por volumen de 30 días de cada mes, 2020 → 2026-10. Costes 0,07 % por lado + funding real
(0,10 % por lado en R1–R3, monedas menos líquidas). Desarrollo 2020–2022; examen 2023 → 2026-10.
Criterio de cada prueba: media neta > 0 en desarrollo **y** examen, y t ≥ 2,5 (agrupado por semana) en todo el periodo.

**R1 — Capitulación con volumen spot (inversa de la L50-S).** Cada hora: cierre bajo el mínimo de los 7 días anteriores y z de la
cuota de volumen spot (24 h, frente a 60 días) ≥ 1,5 → **largo** al cierre. Salida: z ≤ 0 doce horas seguidas, o 5 días. Stop:
entrada − 3 ATR (24 velas de 1 h), que sube con el máximo desde la entrada a 2,5 ATR.

**R2 — Bloque J tal cual está ahora (L46 + L54).** Cierre diario al otro lado de un redondo defendido 3 días → en contra de la ruptura
a la apertura siguiente; ganancia con el cierre diario de vuelta al otro lado del nivel; stop 2 ATR(14) diario; máximo 20 días.

**R3 — Doble techo (L52).** Mismo detector (giros de 3 ATR en 4 h, |M1 − M3| ≤ 0,15h); corto al cerrar bajo el valle; stop en el
máximo de los dos techos; objetivo − h; máximo 60 velas.

**R4 — Momentum intradía en BTC y ETH (idea nueva, Wen y otros 2022).** Cada día UTC: si la rentabilidad de la primera hora
(00:00–01:00) es positiva, largo en la última hora (23:00–24:00); si es negativa, corto. Variante R4b para la sesión de EE. UU.:
primera hora 14:00–15:00 UTC → posición en 20:00–21:00 UTC. Costes 0,07 % por lado + funding. Desarrollo 2020–2022, examen
2023 → 2026-10. Placebo: la hora 12:00–13:00 como "primera hora".
(R4 cuenta como 2 pruebas; total de la lección: 5.)

## 2. Resultados — `l55_salida_R2_R3_R4.txt`, `l55_salida_R1.txt`
Universo nuevo: 525 monedas pasaron por los puestos 31–100 entre 2020 y 2026 (403 con par spot para R1).

| Prueba | Desarrollo | Examen | Total t | ¿Pasa? |
|---|---|---|---|---|
| R1 Capitulación con volumen spot (largo) | −0,52 % (n 392) | −0,12 % (n 1075) | −0,93 | No |
| R2 Bloque J actual | −0,07 % (n 4847) | −0,04 % (n 8810) | −0,18 | **No se replica** |
| R3 Doble techo (corto) | **+1,42 %** (n 503) | **+1,07 %** (n 1092) | **+1,51** | No (t), pero mismo signo |
| R4 Momentum intradía 00–01 → 23–24 | −0,13 % | −0,13 % | −8,96 | No |
| R4b Momentum intradía EE. UU. 14–15 → 20–21 | −0,16 % | −0,16 % | −11,78 | No |
| Placebo R4 (12–13 → 23–24) | −0,10 % | −0,14 % | −10,75 | — |

- **R1:** la capitulación no da ventaja en ningún sentido (la L50 vio que el corto perdía; el largo también pierde).
- **R2:** el bloque J no se sostiene fuera del top 30: lo visto en la L46/L54 fue, muy probablemente, suerte. Se mantiene en
  seguimiento solo como experimento, sin expectativa de pasar a la cartera.
- **R3:** el doble techo es la única observación que se repite en monedas nuevas: positivo en los dos periodos, como en el top 30
  (L52: +0,07R y +0,05R, t 1,82). Las dos pruebas juntas, independientes, se acercan al listón (z combinado ≈ 2,3). **Candidato a
  seguimiento.**
- **R4:** la primera hora no anticipa la última en BTC/ETH (bruto ≈ 0; el placebo da lo mismo). Los costes lo hunden.
