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

## 2. Resultados — `l17_salida.txt`, `l17_auditoria_R1.txt`, `l17_salida_R1_realista.txt`, `l17_salida_cartera.txt`

### R1 — Carry inverso
**Criba (211 antiguas con spot, interés 15 %):** Sharpe 3,66, CAGR 13,0 %, DD 2,0 %, 340 episodios, PF 9,0, 2026 +26 %. ✅
Con interés del 30 % / 50 %: Sharpe 3,31 / 2,94.

**Primer examen (nuevas): INVALIDADO.** Resultado aparente: 2025 +878 %, 2026 +191 %. La auditoría mostró artefactos: el mejor episodio
(ALPACA, +2250 % en 8 días) es una moneda en proceso de retirada con el perpetuo en pleno estrangulamiento (funding −4 % por pago)
mientras el precio de spot quedaba congelado en la simulación; varias otras con spot casi sin volumen (préstamo imposible en la práctica).

**Segundo examen (declarado como tal), con reglas de realismo:** precio de spot de como mucho 8 h de antigüedad; spot con ≥ 5 M$/día de
volumen medio; sin entradas en los 45 días previos a la retirada de una moneda.
| | Sharpe | CAGR | DD máx. | Episodios | PF | 2025 | 2026 | DSR |
|---|---|---|---|---|---|---|---|---|
| Desarrollo (antiguas), 15 % | 3,38 | 11,5 % | 2,0 % | 335 | 8,2 | +3 % | +18 % | 1,00 |
| **Examen corregido (nuevas), 15 %** | **5,12** | 26,0 % | 0,7 % | 311 | 20,0 | +119 % | +88 % | **1,00 → aprobada** |

**Sensibilidad al interés del préstamo:** al 150 % anual, desarrollo Sharpe 1,84 y examen 3,67. Aguanta porque la regla de entrada ya exige
que el funding supere el interés. El funding cobrado por episodio (examen), anualizado: mediana 48 %, p25 19 %, p75 112 %.

**Duda principal (no se puede resolver con datos históricos): la disponibilidad del préstamo.** Si pedir prestado fuera fácil, alguien
arbitraría el funding negativo hasta hacerlo desaparecer; su persistencia sugiere límites de préstamo. Binance limita la cantidad
prestable por moneda y usuario, y puede suspenderla. Solo operando se sabrá cuánto se puede capturar.

### R2 — Tendencia bajista en BTC y ETH
Sharpe 0,19, PF 1,19, DD 52 %. Gana en las caídas (2022 +32 %, 2026 +40 %) pero pierde el resto de años. Como pieza al 25 % **empeora**
el Sharpe de la cartera (1,79 → 1,65). Seguro caro: descartada.

### R3 — Mechas sin stop en monedas consolidadas (dentro de muestra)
Sharpe 2,61, 2026 +31 %, positiva en 11 de los 12 peores meses de la cartera, pero correlación +0,22 y sin examen limpio superado
(falló en las nuevas). Se mantiene como candidata, no entra.

## 3. Cartera actualizada (dentro de muestra)
Correlaciones del carry inverso: −0,19 con el carry, −0,14 con S1, −0,02 con la tendencia.
| | Sharpe | CAGR | DD máx. | Peor mes | Meses + | 2025 | 2026 | Bajo el máximo a oct-2026 |
|---|---|---|---|---|---|---|---|---|
| Anterior (carry, S1, tendencia; 1/3) | 1,80 | 34,7 % | 14,9 % | −5,8 % | 65 % | +20 % | −12 % | −13,7 % |
| **Nueva (+ carry inverso; 1/4)** | **2,26** | 33,3 % | **7,2 %** | −4,0 % | 70 % | +30 % | **+5 %** | −4,0 % |

Por año (nueva): 2020 +59 %, 2021 +28 %, 2022 +28 %, 2023 +44 %, 2024 +34 %, 2025 +30 %, 2026 +5 %.

## 4. Conclusiones
1. **El carry inverso es la pieza que faltaba para las caídas:** cobra a los cortos cuando el mercado tiene miedo, justo cuando el carry
   normal está parado. Juntos forman un "carry en ambos sentidos".
2. Con él, la caída máxima de la cartera se reduce a la mitad (15 % → 7 %) y 2026 pasa de −12 % a +5 %.
3. Todo esto es dentro de muestra y el carry inverso depende de poder pedir prestado: **es la primera pieza que hay que verificar en real.**
4. Las coberturas direccionales (tendencia bajista en BTC/ETH) cuestan más de lo que protegen.
