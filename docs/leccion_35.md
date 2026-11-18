# Lección 35 — Forex intradía y swing: lo que falló en cripto, lo de las redes sociales y lo propio de las divisas

## 0. Por qué repetirlo en forex
En cripto, muchas ideas de corto plazo murieron por los **costes**: 0,07 % por lado (taker + deslizamiento). En forex con un bróker ECN,
el coste por lado en los pares principales es de **0,5–1,5 puntos básicos (0,005–0,015 %)**, entre 5 y 14 veces menos. Una ventaja pequeña
que en cripto no compensaba podría compensar aquí. Además se prueban las estrategias de las publicaciones de redes sociales y dos clásicas
del forex minorista.

## 1. Datos
Velas de 1 minuto (precio de compra) de HistData.com, agregadas a 1 hora: EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD, EURJPY,
EURGBP, GBPJPY, 2012-01 → 2026-10. Hora original: EST fija (UTC−5), convertida a UTC.
(Dukascopy rechazó las descargas por límite de peticiones; se descartaron los pares EUR/GBP/AUD frente a USDT de Binance porque se
desvían 11–30 pb del tipo oficial.)

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

## 3. Resultados — `l35_salida.txt` (con costes) y `l35_salida_sin_costes.txt` (informativo)
Datos verificados: el EURUSD de HistData se desvía 0,7 pb del tipo oficial de la Reserva Federal (correlación diaria 0,998).
| Estrategia | Desarrollo 2012–2018 | **Examen 2019–2026 (con costes)** | Acierto | Examen **sin costes** |
|---|---|---|---|---|
| Y1 CRT 4h | −0,151R | **−0,141R (t −17)** | 50 % | −0,008R |
| Y2 CRT 4h + CISD 1h | −0,120R | **−0,119R (t −12)** | 57 % | −0,007R |
| Y3 CRT diario | −0,056R | **−0,070R (t −4)** | 50 % | −0,011R |
| Y4 Reversión a la media 1:1 | −0,124R | **−0,131R (t −8)** | 46 % | −0,051R |
| Y5 Ruptura de Londres | −0,050R | **−0,073R (t −8)** | 51 % | **+0,034R (t 2,7)** |
| Y6 Tendencia (bloque D) | −0,019R | **−0,079R (t −3,5)** | 34 % | −0,063R |
| Y7 Números redondos | −0,142R | **−0,137R** (placebo −0,098R) | 47 % | −0,061R (placebo −0,022R) |
**Ninguna se aprueba.** Más de 200 000 operaciones simuladas en 10 pares.

## 4. Conclusiones
1. **Sin costes, casi todo da cero:** CRT, CRT + CISD y CRT diario no tienen ventaja ni siquiera gratis. La reversión a la media 1:1 y los
   números redondos pierden incluso sin costes (el precio, al alejarse 2 desviaciones o al tocar un nivel redondo, tiende a seguir).
2. **La única ventaja real es la ruptura de Londres** (+0,03 a +0,045R por operación sin costes, en los dos periodos), pero es más pequeña
   que el coste de un particular (≈ 0,1R). Pista abierta, no aprobada: solo sería operable con costes institucionales.
3. **CRT + CISD vuelve a acertar el 57–63 %**, como en cripto y como dice la publicación, y vuelve a perder: el acierto alto viene de un
   objetivo cercano.
4. **Ni con costes 5–14 veces menores que en cripto aparecen ventajas intradía en forex.** El mercado de divisas está dominado por bancos
   y algoritmos de alta frecuencia; los patrones de velas visibles para todos no dejan margen.
