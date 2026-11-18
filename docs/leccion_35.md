# Lección 35 — Forex intradía y swing: lo que falló en cripto, lo de las redes sociales y lo propio de las divisas

## 0. Por qué repetirlo en forex
En cripto, muchas ideas de corto plazo murieron por los **costes**: 0,07 % por lado (taker + deslizamiento). En forex con un bróker ECN,
el coste por lado en los pares principales es de **0,5–1,5 puntos básicos (0,005–0,015 %)**, entre 5 y 14 veces menos. Una ventaja pequeña
que en cripto no compensaba podría compensar aquí. Además se prueban las estrategias de las publicaciones de redes sociales y dos clásicas
del forex minorista.

## 1. Datos
Velas de 1 hora (precio de compra) de Dukascopy, banco suizo: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD, EURJPY, EURGBP, GBPJPY,
2012-01 → 2026-10. (Se descartaron los pares EUR/GBP/AUD frente a USDT de Binance: se desvían 11–30 pb del tipo oficial.)

## 2. Pre-registro (antes de calcular ningún resultado)
**Costes por lado** (diferencial + comisión de un bróker ECN): EURUSD 0,5 pb; USDJPY 0,6; GBPUSD, AUDUSD, USDCAD, USDCHF 0,8;
NZDUSD, EURJPY, EURGBP 1,0–1,2; GBPJPY 1,5. **Deslizamiento** de 0,3 pb adicional en stops, salidas por tiempo y entradas a mercado.
Margen del bróker en swaps (solo Y6, que mantiene días): 1 % anual. Si en la misma vela se tocan stop y objetivo → pérdida.
**Y1 — CRT 4h**, **Y2 — CRT 4h + CISD 1h**, **Y3 — CRT diario:** reglas idénticas a la Lección 33 (riesgo mínimo 0,1 % en 4h y 0,2 % en diario,
porque las divisas se mueven menos que las criptos).
**Y4 — Reversión a la media 1:1** (en la línea de la publicación de Héctor, cuyas reglas exactas no se conocen): z = (cierre − media de 20
velas de 1h) / desviación de 20. Si |z| ≥ 2 con el mercado abierto: entrada en contra con orden limit al cierre; objetivo en la media;
stop a la misma distancia al otro lado (1:1); máximo 24 h. Una operación a la vez por par.
**Y5 — Ruptura de Londres:** rango asiático 00:00–07:00 UTC; entre 07:00 y 12:00, la primera ruptura del máximo (compra) o del mínimo (venta);
stop en el otro extremo del rango; objetivo a 1 rango; cierre a las 20:00 UTC.
**Y6 — Bloque D del bot en divisas:** ruptura de 120 velas de 4h a favor de la tendencia diaria (EMA de 50), stop dinámico de 5 ATR.
Largos y cortos.
**Y7 — Números redondos (Osler, 2000: el estudio original es en divisas):** primer toque de múltiplos de 50 pips (0,0050; 0,50 en pares con JPY);
orden limit en el nivel, objetivo y stop a 2 ATR (1:1). Con placebo (niveles desplazados al azar).
**Periodos:** desarrollo 2012–2018; **examen 2019 → 2026-10** (una vez).
**Criterio:** esperanza neta > 0 con t ≥ 3 (agrupando por día) en el examen y positiva en desarrollo; Y7 además mejor que su placebo.
Pruebas nuevas: 7.
