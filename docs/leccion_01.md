# Lección 1 — Costes: dónde NO se puede hacer scalping

Datos: futuros perpetuos BTC/ETH/SOL-USDT, velas de 1m, 2025-11-01 → 2026-10-31.
Comisiones VIP0: maker 0,02 %, taker 0,05 %; slippage supuesto 0,01 % por orden a mercado.

## A) Coste por trade en R (stop = 1 ATR14 mediano)

| Activo | Marco | ATR % | taker/taker | maker/taker | maker/maker |
|---|---|---|---|---|---|
| BTC | 1m | 0,053 | **2,27R** | 1,51R | 0,76R |
| BTC | 5m | 0,141 | 0,85R | 0,57R | 0,28R |
| BTC | 15m | 0,266 | 0,45R | 0,30R | 0,15R |
| ETH | 5m | 0,193 | 0,62R | 0,41R | 0,21R |
| SOL | 5m | 0,232 | 0,52R | 0,35R | 0,17R |
| SOL | 15m | 0,426 | 0,28R | 0,19R | 0,09R |

En BTC 1m con órdenes a mercado cada trade cuesta 2,3 veces lo que arriesgas:
**ni con un 100 % de aciertos y RR 1:1 se gana dinero.**

## B) Cuándo se mueve el mercado (BTC, hora UTC)
El rango de la vela de 5m se **duplica** entre las 13:00 y las 17:00 UTC (apertura de EE. UU.)
respecto a 03:00–11:00 UTC (0,21 % frente a 0,105 %). Con más volatilidad el mismo stop "en ATR"
es más ancho en %, así que el coste en R baja a la mitad.

## C) Hipótesis nula (entradas aleatorias, stop 1 ATR, TP 1R)
- Win rate bruto ≈ 50 % y E bruta ≈ 0 en todos los casos → **el motor no tiene sesgo** (validado).
- E neta = −coste: de −3,5R (BTC 1m taker) a −0,10R (SOL 15m maker).
- Esta es la línea base: una estrategia tiene que **superar el coste**, no solo "acertar".

## Reglas de diseño que salen de aquí (obligatorias desde ahora)
1. **Nada por debajo de 5m.** El marco base será 5m, con el contexto en 15m/1h.
2. **Entrada con orden limit (maker)**; el stop será a mercado (taker). El escenario de referencia es maker/taker.
3. **Stop mínimo ≈ 0,35 % del precio** → coste ≤ ~0,25R con maker/taker.
4. **Ventana principal: 13:00–17:00 UTC** (14:00–18:00 en España peninsular en invierno).
5. Objetivo de coste: **c ≤ 0,2R**. Con RR 1:1 eso exige un win rate ≥ 60 % para no perder.
6. Riesgo de la orden limit: si no se ejecuta, se pierde la entrada (y suele ser la mejor). Habrá que medir la tasa de ejecución.
