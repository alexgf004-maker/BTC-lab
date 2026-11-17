# Lección 15 — Estrategias en corto, con un examen nuevo de 705 perpetuos nunca usados

## 0. Lo que ya sabemos de los cortos
Pierden: vender tras subidas explosivas (H3b), vender mechas hacia arriba (W2), la tendencia bajista en todos los regímenes (Lección 3),
el retroceso en tendencia bajista (Lección 2). En cripto las subidas violentas CONTINÚAN.
El corto más consistente: altcoin débil contra BTC (lado corto de N1: PF 1,39 y 1,43 en dos conjuntos, separado a posteriori).

## 1. Examen nuevo
Binance tiene 923 perpetuos USDT; hemos usado 218. Los **705 restantes** forman el conjunto de examen (`l15_simbolos.json`).
**Filtro de activos no cripto (regla fijada antes de descargar):** acciones, ETFs, materias primas y divisas cotizan en mercados que
cierran el fin de semana. Se excluye todo símbolo cuya variación absoluta media horaria en sábado y domingo sea < 50 % de la de lunes
a viernes (calculada sobre su historia), y además BTCDOM, DEFI, USDC, USDEX, USDBRL, PAXG, XAUT, XAU, XAG, XPT, XPD.
Universo point-in-time: los 30 más líquidos de cada mes entre los que superan el filtro.

## 2. Hipótesis (pre-registro; desarrollo = 218 monedas ya usadas, top 20 point-in-time; examen = nuevas, top 30)
**S1 — Debilidad relativa frente a BTC.** Exactamente el lado corto de N1 (Lección 12): ratio alt/BTC en 4h; filtro: ratio diario bajo su
EMA50; entrada en la ruptura del mínimo de 120 velas; chandelier de 5 ATR; corto alt + largo BTC; 1 % de riesgo, máx. 10.
Ya tiene evidencia en dos conjuntos → **pasa directamente al examen.**

**S2 — Tendencia bajista solo en mercado bajista.** Corto directo (sin cobertura) si BTC cierra por debajo de su SMA200 diaria y la moneda
cierra bajo su EMA50 diaria y rompe el mínimo de 120 velas de 4h. Chandelier de 5 ATR; 1 % de riesgo; máx. 10.
*Mecanismo:* en mercados bajistas desaparece la deriva alcista que hace fracasar los cortos.

**S3 — Pump fallido.** Diario: la moneda sube ≥ 25 % en los 3 días previos y hoy cierra por debajo del mínimo de ayer (la continuación
ha fallado) → corto al cierre. Stop en el máximo de los últimos 3 días × 1,02. Salida a los 7 días. 0,5 % de riesgo; máx. 10.
*Mecanismo:* las subidas de compra minorista se mantienen mientras entra dinero; cuando falla, los compradores atrapados venden.

**S4 — Saturación de largos.** Diario: funding medio de 3 días ≥ 0,05 % por 8h **y** interés abierto +30 % en 7 días **y** precio en 7 días ≤ +5 %
→ corto al cierre; salida a las 72 h; stop a 2 × ATR diario; 0,5 % de riesgo; máx. 10. Se cobra el funding.
*Mecanismo:* muchos largos apalancados, pagando caro y sin que el precio avance: combustible para liquidaciones.

**S5 — Cesta corta de "lotería" (efecto MAX).** Cada lunes, en el universo: corto en las 5 monedas con mayor subida de 4h en los 7 días previos,
largo en BTC con el mismo beta (90 días) → neutral al mercado. Bruto 100 %. Semana completa.
*Mecanismo:* preferencia por la lotería (Bali, Cakici y Whitelaw, 2011); Lección 11: IC −0,072 (t −11,8). Fuga declarada: el signo es conocido.

**Criterios.** Criba: Sharpe ≥ 1,2, rentabilidad positiva en las dos mitades, PF ≥ 1,3.
Examen (una vez): Sharpe ≥ 1,0, PF ≥ 1,3, Deflated Sharpe ≥ 0,90 con 387 + 5 pruebas. Costes: 0,14 % ida y vuelta por pata + funding real.

## 3. Datos del examen
Archivo de Binance: 923 perpetuos USDT; 218 ya usados; **705 nuevos**. Excluidos: 5 con nombre en caracteres chinos (no se pueden descargar con
la herramienta; declarado), 161 no cripto por la regla del fin de semana (acciones, ETFs, materias primas, índices; la regla también
excluyó por error algunas criptos poco activas, como ANC o MDT) y 57 con menos de 60 días de historia. Quedan **482 criptos nuevas**,
incluidas deslistadas.

## 4. Criba (218 monedas de desarrollo) — `l15_salida_criba.txt`
| | Sharpe | CAGR | DD máx. | n | Win rate | PF | Mitades | Veredicto |
|---|---|---|---|---|---|---|---|---|
| S2 tendencia bajista en mercado bajista | 0,22 | 2,4 % | 33,4 % | 406 | 41 % | 1,19 | +21 % / −6 % | ❌ |
| S3 pump fallido | 0,17 | 0,2 % | 2,2 % | 72 | 58 % | 1,15 | −0,4 % / +1,9 % | ❌ |
| S4 saturación de largos | 0,62 | 0,2 % | 0,3 % | **8** | 62 % | 2,19 | +0,5 % / 0 % | ❌ (casi sin señales) |
| S5 cesta corta de lotería | −0,21 | −11,9 % | 72,1 % | 342 sem. | 53 % | 0,92 | −43 % / −24 % | ❌ (2021: −69 %) |

## 5. Examen de S1 (482 criptos nuevas, top 30 point-in-time, una vez) — `l15_salida_examen.txt`
| Sharpe | CAGR | DD máx. | Trades | Win rate | PF | E por trade | Deflated Sharpe |
|---|---|---|---|---|---|---|---|
| **1,56** | 65,4 % | 30,7 % | 1616 | 45 % | **1,71** | +0,221R | **0,924 → APROBADA** |

Por año: 2020 +11 %, 2021 −9 %, 2022 +37 %, 2023 +146 %, 2024 +204 %, 2025 +63 %, 2026 +14 %. Exposición nocional máxima 3x.

## 6. Auditoría de S1 — `l15_salida_auditoria_S1.txt`
| Prueba | Sharpe | PF | E por trade |
|---|---|---|---|
| Tal cual | 1,56 | 1,71 | +0,221R |
| Costes ×2 (0,56 % ida y vuelta) | 1,30 | 1,56 | +0,185R |
| Costes ×3 (0,84 %) | 1,04 | 1,43 | +0,150R |
| Sin funding (efecto del funding) | 1,66 | 1,76 | +0,234R |
| Solo monedas con volumen ≥ 20 M$/día | 1,23 | 1,56 | +0,172R |
| Solo monedas con volumen ≥ 50 M$/día | 1,04 | 1,52 | +0,158R |
| Sin los 20 mejores trades | — | 1,40 | +0,127R |

- Agrupando por día de entrada: t = 4,66 (822 días). 167 de 285 monedas positivas. No depende de las monedas recién listadas
  (< 180 días: +0,19R; ≥ 180 días: +0,24R). Volumen mediano al entrar: 31 M$/día.
- El funding cuesta al corto ≈ 0,1 de Sharpe (los cortos en altcoins débiles pagan funding negativo a veces).

**S1 en las 218 monedas de desarrollo (informativo, ya vistas):** Sharpe 0,90, PF 1,38, 2026 −32 %. Correlación mensual con el examen: 0,44.
La ventaja es mayor en altcoins nuevas y pequeñas que en las establecidas.

## 7. Conclusiones
1. **S1 (corto en altcoins débiles cubierto con BTC) es la segunda estrategia aprobada del proyecto**, tras el carry.
   Evidencia acumulada: PF 1,39 (57 monedas), 1,43 (161), 1,38 (218 juntas) y 1,71 (482 nuevas). Win rate del 44–45 %.
   Mecanismo: emisión continua de tokens, desbloqueos y ventas de los fundadores; el capital rota hacia BTC.
2. Sus riesgos: 2021 negativo en los dos conjuntos (temporada de altcoins), 2026 negativo en las monedas establecidas,
   caídas del 31–37 %, exposición de hasta 3x, cortos en monedas pequeñas (subidas violentas, límites de posición).
3. Los cortos sin cobertura o basados en "esto ha subido demasiado" pierden; el corto que funciona es contra la debilidad
   estructural y relativo a BTC.
