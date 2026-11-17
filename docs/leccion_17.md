# Lección 17 — Piezas para las caídas: ganar cuando la cartera pierde

## 0. Diagnóstico de 2026
Funding medio del mercado: −0,009 % por 8h (el más negativo de la serie; 2022: −0,005 %). Cada día ~13 monedas tienen funding medio
de 3 días por debajo de −0,03 % por 8h (los cortos pagan ≈ 33 % anual): máximo histórico. BTC −13 % en el año, solo 74 de 304 días sobre su
media de 200. Nuestro carry cobra a los largos en euforia; **en 2026 son los cortos quienes pagan**.

## 1. Pre-registro (antes de ver resultados)

**R1 — Carry inverso (largo en el perpetuo + corto en spot con préstamo de margen).**
*Mecanismo:* en pánico, los cortos apalancados pagan funding a los largos; con la cobertura en spot, el precio no importa.
*Reglas:* espejo exacto del carry de la Lección 8: rendimiento neto = −funding − interés del préstamo; entrar si su media de 3 días
> 0,015 % por 8h; salir si < 0,005 %. 4 huecos del 25 %; pata corta (spot prestado) a 2x con la misma simulación de liquidación (+45 %)
y reequilibrio (+20 %). Mismos costes por pata.
*Interés del préstamo (desconocido históricamente):* **15 % anual** (0,0137 % por 8h) como caso base; sensibilidad al 30 % y al 50 %.
*Datos:* desarrollo = 211 monedas antiguas con spot; **examen = criptos nuevas con spot** (se descarga ahora). Universo top 20 / top 30.
*Criba:* Sharpe ≥ 1,2, dos mitades positivas, PF ≥ 1,3. *Examen:* Sharpe ≥ 1,0, PF ≥ 1,3, Deflated Sharpe ≥ 0,90 con 396 pruebas.
*Aviso:* no todas las monedas se pueden pedir prestadas, y el interés sube cuando todos quieren ponerse cortos.

**R2 — Tendencia bajista en BTC y ETH** (espejo exacto del bloque D: cierre diario bajo la EMA50, ruptura del mínimo de 120 velas de 4h,
chandelier de 5 ATR, 5 % de riesgo sobre el bloque). Solo dos activos: sin examen posible; informativo.

**R3 — Pescar mechas sin stop en monedas consolidadas** (las 218 antiguas, donde funcionó; fracasó en las nuevas). Informativo, dentro de muestra.

**Evaluación como complemento** de la cartera P (1/3 carry, 1/3 S1, 1/3 tendencia):
correlación mensual con P; rentabilidad en los 12 peores meses de P, en 2022 y en 2026; y cartera con la pieza al 25 % (resto al 75 %).
Una pieza es útil como cobertura si su correlación con P es ≤ 0 y mejora el Sharpe y la caída máxima de la cartera.
