# Lección 14 — Profundizar en las mechas, grid trading y prima de volatilidad

## 1. Pre-registro (antes de calcular resultados)

### Familia W (liquidez a movimientos forzados)
**W1-R — Robustez de W1 (no es una prueba nueva, no selecciona nada):** misma regla con la orden a 3σ, 4σ, 5σ, 6σ y 7σ, sobre las
218 monedas. Si la ventaja solo existe en 5σ, es un artefacto; si varía suavemente con la profundidad, es un mecanismo.

**W2 — Vender las mechas hacia arriba (espejo de W1).** Mecanismo: liquidaciones de cortos (short squeeze).
Venta limit en `cierre anterior × (1 + 5σ)`; objetivo a media vuelta; stop a la misma distancia por encima; 24 h; 0,5 % de riesgo; máx. 10.
Desarrollo = 57 monedas → examen = 161 (este lado no se ha mirado nunca). Criba: Sharpe ≥ 1,2, dos mitades positivas, PF ≥ 1,3.
Examen: Sharpe ≥ 1,0, PF ≥ 1,3, Deflated Sharpe ≥ 0,90 (387 pruebas).

**W3 — W1 sin stop a mercado.** El punto débil de W1 es el deslizamiento del stop. Variante: misma entrada y mismo objetivo; si no se
alcanza, salida a mercado a las 24 h; sin stop. Mismo tamaño de posición que W1. *Aviso:* se evalúa sobre monedas ya vistas con W1;
es una comparación de diseño, no un examen limpio. Se informa de la cola (peor trade, caída máxima).

### G1 — Grid neutral en BTC y ETH (la estrategia automática más popular)
Mecanismo: cobrar las oscilaciones dentro de un rango (equivale a vender volatilidad).
Datos: velas de 1m, 2020-01 → 2026-10. Rejilla geométrica con escalones del 0,5 % alrededor de un precio de referencia.
Cada vez que el precio baja un escalón se compra 1 unidad; cada vez que sube uno, se vende 1 (inventario máximo ±20 unidades = ±10 %).
Unidad = 5 % del capital (exposición máxima 1x). Comisiones maker 0,02 % por ejecución.
Si el precio se aleja un 12 % de la referencia: se cierra todo a mercado (0,07 %) y la rejilla se recentra.
Criterio: Sharpe ≥ 1,0 y resultado positivo en las dos mitades (2020-01 → 2023-05 y 2023-06 → 2026-10). Informativo: escalones del 0,3 % y del 1 %.

### V1 — Prima de volatilidad (medición)
Datos: índice de volatilidad implícita a 30 días de Binance (BVOL) para BTC y ETH, desde 2023-10.
(a) Medición: volatilidad implícita − volatilidad realizada en los 30 días siguientes; media, % de días positivos, por año.
(b) Venta sistemática aproximada: el día 1 de cada mes se vende un straddle en el dinero a 30 días al precio de Black-Scholes con
la volatilidad implícita menos 2 puntos (horquilla); se mantiene hasta el vencimiento sin cubrir.
Resultado = prima − |variación del precio|. También con tramos diarios solapados.
*Aviso:* solo ~36 meses independientes y sin precios reales de opciones: es una medición de si la prima existe, no una aprobación.
