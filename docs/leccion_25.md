# Lección 25 — Arbitraje mecánico del fin de semana y el "hueco del CME"

## 1. Pre-registro (antes de calcular ningún resultado de estrategia)
**U1 — ETFs apalancados frente a su subyacente, fin de semana.** Un ETF apalancado diario cumple, desde el cierre anterior,
r_ETF ≈ L · r_subyacente. El lunes, con la bolsa abierta, la relación se restablece por construcción; el fin de semana, los dos perpetuos
cotizan sin ancla.
*Pares (EE. UU., relación mecánica verificada en horario de bolsa):* NVDL/NVDA (2), TSLL/TSLA (2), TQQQ/QQQ (3), SQQQ/QQQ (−3), KORU/EWY (3),
SOXL/SOXS (−1), TZA/IWM (−3), MSTU/MSTR (2). Se excluyen los 2x de Samsung y SK Hynix (cotizan en otra bolsa y divisa: la relación medida es 1,6, no mecánica).
*Desviación:* D = r_ETF − L·r_sub (rentabilidades simples desde el viernes 21:00 hasta la entrada).
*Regla:* si |D| ≥ 0,5 % el domingo a las 21:00: si D > 0, corto en el ETF y largo L veces el subyacente (al revés si D < 0).
Salida el lunes a las 16:00 UTC (bolsa ya abierta en los dos horarios). Costes 0,14 % por unidad de nocional en cada pata; funding incluido.
Resultado expresado por unidad de nocional del ETF. Variante informativa: entrada el lunes a las 13:00.
*Estadístico:* media por fin de semana (promedio de los pares) y t. División temporal: primera mitad de los fines de semana / segunda mitad.
Criterio: neto > 0 y t ≥ 2 en las dos mitades. **Muestra muy corta (≈ 18 fines de semana): exploratoria.**
Se informa también de qué fracción de la desviación desaparece (pendiente del cambio de D sobre D).

**U2 — Lo mismo en las noches entre semana:** D de 21:00 a 07:00; salida a las 15:00. Noches de lunes a jueves.

**U3 — El "hueco del CME" en BTC y ETH.** El CME cierra de viernes 21:00 a domingo 22:00 UTC. Creencia popular: el precio vuelve a "rellenar el hueco".
*Hipótesis propia:* **es falso**, porque BTC cotiza con liquidez y cobertura 24/7: no hay precio sin ancla que corregir.
*Medidas:* W = viernes 21:00 → domingo 22:00; R = domingo 22:00 → lunes 21:00. (a) Pendiente de R sobre W. (b) Regla: si |W| ≥ 2 %,
posición −signo(W), salida el lunes 21:00; costes 0,09 %. (c) Probabilidad de que el precio toque el nivel del viernes 21:00 en los 5 días
siguientes, frente a la misma probabilidad para movimientos de igual tamaño en ventanas de 49 h que empiezan un martes (base).
División: 2020–2022 desarrollo / 2023–2026 examen. Criterio de (b): neto > 0 y t ≥ 2 en las dos mitades.

## 2. Resultados — `l25_salida.txt`
**U1 (ETFs apalancados, fin de semana):** 100 observaciones en 18 fines de semana. La desviación se cierra el lunes en un **79 %**
(pendiente −0,79): el mecanismo se cumple. Pero la desviación media es solo **0,31 %**, menor que el coste de las dos patas
(0,28–0,56 %): 16 operaciones, +0,11 % de media, t 1,84 y 0,83 en las dos mitades → **NO aprobada.**
Lectura: los dos perpetuos se pueden operar a la vez, así que **cada pata cubre a la otra** y los creadores de mercado mantienen la relación
aunque la bolsa esté cerrada. Confirma el principio desde el lado contrario: hay ineficiencia solo cuando NO hay cobertura posible
(una acción sola en fin de semana); cuando la hay (un par con relación conocida), el precio se mantiene alineado.
**U2 (noches entre semana):** NO aprobada (fallo de diseño en KORU/EWY: su subyacente coreano cotiza durante la noche de EE. UU.).

**U3 (hueco del CME):**
| | Pendiente R sobre W | Operación contraria (|W| ≥ 2 %) | "Relleno" en 5 días: fin de semana / base |
|---|---|---|---|
| BTC 2020–2022 | −0,16 | +0,24 % (t +0,29) | 60 % / 41 % |
| BTC 2023–2026 | +0,20 | −1,19 % (t −1,61) | 53 % / 38 % |
| ETH 2020–2022 | −0,01 | +0,52 % (t +0,79) | 70 % / 56 % |
| ETH 2023–2026 | +0,02 | −0,38 % (t −0,68) | 54 % / 40 % |
**No es operable.** El "relleno" más frecuente es una **ilusión por volatilidad**: la semana que sigue a un fin de semana es más volátil
(BTC 9,3 % frente a 6,8 %), así que un 2 % del fin de semana es un movimiento pequeño para lo que viene (z medio 0,54 frente a 0,83).
Comparando movimientos del mismo tamaño relativo a la volatilidad siguiente, las probabilidades se igualan (p. ej. BTC, z 0,25–0,5:
58 % frente a 57 %). La creencia popular es cierta como frecuencia y falsa como forma de ganar dinero.

## 3. Conclusión
El principio queda delimitado con precisión: **la ineficiencia aparece cuando un precio se forma sin posibilidad de cobertura
(acciones sueltas en fin de semana) y desaparece en cuanto existe cobertura** (pares de ETFs, BTC con mercado 24/7, noches con el CME abierto).
