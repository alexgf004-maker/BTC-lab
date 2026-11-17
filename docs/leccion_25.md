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
