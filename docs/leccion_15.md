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
