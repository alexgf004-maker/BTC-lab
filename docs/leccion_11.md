# Lección 11 — Investigación sistemática de señales (método cuantitativo profesional)

## 0. Por qué
Las lecciones 2–10 probaron reglas una a una, cada una con una sola especificación. Eso deja dos huecos: una idea puede fallar por
su especificación, y solo se usaron precio, volumen y funding. Aquí se mide **toda una biblioteca de variables a la vez**, con
corrección por pruebas múltiples, y se combinan en un modelo validado hacia delante.

## 1. Pre-registro (antes de calcular ninguna variable)

**Universo:** point-in-time, las 25 monedas más líquidas de cada mes entre los 218 perpetuos descargados (incluye deslistados).
**Frecuencia:** velas de 4h. **Objetivos:** rentabilidad futura a 4h, 24h y 72h, (a) relativa a la media del universo (neutral al
mercado) y (b) absoluta.

**Biblioteca de variables (todas conocidas al cierre de la vela):**
- *Momentum/reversión:* rentabilidad a 4h, 8h, 24h, 3d, 7d, 14d, 30d, 60d; distancia al máximo y al mínimo de 7, 30 y 90 días.
- *Volatilidad y forma:* volatilidad a 1d, 7d, 30d; ratio vol. 1d/30d; asimetría a 7d; mayor subida de 4h en 7d; rango/cierre.
- *Volumen y liquidez:* volumen 1d/30d; iliquidez de Amihud a 7d; volumen en dólares a 30d (tamaño).
- *Flujo agresivo:* proporción de compras agresivas a 4h, 24h y 7d.
- *Relación con BTC:* beta a 30d, correlación a 30d, rentabilidad residual a 1d y 7d.
- *Funding:* último, media a 3d y 7d, cambio 3d frente a 30d.
- *Posicionamiento (datos nuevos de Binance):* cambio del interés abierto a 4h, 24h y 7d; interés abierto / volumen;
  ratio largos/cortos de grandes cuentas (nivel y cambio 24h); ratio largos/cortos global (nivel y cambio 24h);
  ratio de volumen comprador/vendedor agresivo; divergencia precio–interés abierto a 24h.
- *Estado del mercado (solo para objetivos absolutos):* rentabilidad de BTC a 24h y 7d, volatilidad de BTC a 7d,
  amplitud (% de monedas sobre su media de 30d), funding medio del universo.

**Paso A — Capacidad predictiva individual.** Para cada variable y horizonte: correlación de rangos (IC) por fecha entre la
variable y la rentabilidad relativa futura; media, t (con fechas no solapadas) y signo en cada mitad del periodo.
Corrección de **Benjamini-Hochberg al 5 %** sobre todas las pruebas. Descriptivo: decide qué se entiende, no qué se opera.

**Paso B — Modelo combinado, validación hacia delante.** Cada 1 de enero se reentrena con todos los datos anteriores
(dejando un hueco igual al horizonte) y se opera el año siguiente. Variables transformadas a rangos por fecha.
Modelos: (1) regresión ridge; (2) LightGBM (300 árboles, profundidad 4, tasa 0,03, 70 % de filas y columnas; sin búsqueda de hiperparámetros).
- *Cartera neutral:* largo en el quintil con mejor predicción y corto en el peor, a partes iguales, 50 % del capital por lado,
  rebalanceo cada horizonte. Horizontes: 24h y 72h (4h se informa, pero no opera: la rotación lo hace inviable de antemano).
- *Cartera direccional:* para cada moneda, largo si la predicción absoluta está en el tercio superior de su historia de
  entrenamiento, corto si está en el inferior; riesgo igual por moneda, 100 % bruto máximo.
- Costes: 0,07 % por unidad rotada; funding real.
- Dos juegos de variables: **A** sin posicionamiento (prueba 2021–2026) y **B** con posicionamiento (prueba 2022–2026).

**Criterios (rendimiento fuera de muestra, neto):** Sharpe ≥ 1,0, positivo en al menos el 75 % de los años de prueba y
Deflated Sharpe ≥ 0,90 con 358 + 16 pruebas (2 modelos × 2 juegos × 2 carteras × 2 horizontes).
Una sola ejecución: no se ajusta nada después de ver los resultados.

## 2. Resultados — `l11_salida.txt`, `l11_ic.csv`, `l11_modelos.csv`

Panel: 161 monedas, 1,73 millones de velas de 4h; 357 614 dentro del universo point-in-time (2020-03 → 2026-10).
Cobertura de los datos de posicionamiento: 2 % en 2020, 12 % en 2021, 77 % en 2022 y ≥ 95 % desde 2023.

### Paso A — Capacidad predictiva individual (135 pruebas)
**100 de 135 son significativas** tras Benjamini-Hochberg al 5 %, y 98 mantienen el signo en las dos mitades del periodo.
Las más fuertes (IC a 24h, t):

| Variable | IC | t | Lectura |
|---|---|---|---|
| Correlación con BTC a 30d | +0,079 | +13,8 | las monedas que se mueven con BTC rinden más que las "independientes" |
| Volatilidad a 30d / 7d / 1d | −0,089 / −0,085 / −0,071 | −12,7 / −12,3 / −11,1 | **anomalía de baja volatilidad**: las más volátiles rinden peor |
| Mayor subida de 4h en 7d | −0,072 | −11,8 | efecto "lotería": tras un pelotazo, peor rentabilidad |
| Iliquidez (Amihud) | −0,057 | −9,9 | las menos líquidas rinden peor |
| Interés abierto / volumen | +0,064 | +9,3 | única variable de posicionamiento con fuerza |
| Rentabilidad a 4h y 8h (horizonte 4h) | −0,044 | −19 | reversión de muy corto plazo |

El resto del posicionamiento aporta poco: los ratios largos/cortos y sus cambios no son significativos o rozan el umbral.
El momentum de 3 a 60 días no es significativo entre monedas (coherente con la Lección 6).

### Paso B — Modelos combinados, validación hacia delante, neto de costes y funding
| Juego | Cartera | Horizonte | Modelo | Sharpe bruto | Sharpe neto | CAGR | DD máx. | Años + | DSR |
|---|---|---|---|---|---|---|---|---|---|
| A | neutral | 24h | ridge / lgbm | 0,73 / 0,83 | 0,09 / 0,08 | −3 % | 56–62 % | 50 % | 0,01 |
| A | neutral | 72h | ridge / lgbm | 0,91 / 0,95 | 0,64 / 0,58 | 14–17 % | 29–43 % | 50–67 % | 0,15–0,18 |
| A | direccional | 24h | ridge / lgbm | 0,64 / 0,68 | 0,52 / 0,54 | 14–15 % | 61–69 % | 67 % | 0,11 |
| A | direccional | 72h | ridge / lgbm | −0,05 / 0,22 | −0,01 / 0,22 | negativo | 65–86 % | 50–67 % | ≤ 0,03 |
| B | neutral | 24h | ridge / lgbm | 0,86 / 1,06 | 0,06 / 0,17 | ≈ 0 % | 53–62 % | 40 % | ≤ 0,03 |
| B | neutral | 72h | ridge / lgbm | 0,49 / 1,15 | 0,13 / 0,66 | −1 / +16 % | 40–47 % | 40–60 % | ≤ 0,22 |
| B | direccional | 24h | ridge | 1,41 | 1,17 | 50 % | 38,6 % | 80 % | 0,63 |
| B | direccional | 24h | lgbm | 1,24 | 1,02 | 49 % | 63,1 % | 60 % | 0,50 |
| **B** | **direccional** | **72h** | **ridge** | 1,40 | **1,37** | 58 % | 35,3 % | 80 % | **0,78** |
| B | direccional | 72h | lgbm | 0,50 | 0,42 | 9 % | 50,3 % | 80 % | 0,09 |

**Ninguno de los 16 supera los tres criterios** (Sharpe ≥ 1,0, ≥ 75 % de años positivos y Deflated Sharpe ≥ 0,90).

## 3. Conclusiones
1. **Predecir no es lo mismo que ganar.** Hay 98 señales estadísticamente reales y estables, pero al operarlas en una cartera
   neutral el Sharpe neto queda entre 0,1 y 0,7. Motivos: (a) los costes de rotar el 70–80 % de la cartera en cada rebalanceo;
   (b) las señales fuertes obligan a ponerse corto en las monedas más volátiles e ilíquidas, que de vez en cuando suben un 100 %
   y pagan funding; (c) una correlación de rangos del 5–9 % es pequeña frente a la dispersión de las rentabilidades.
2. **El mejor candidato: modelo direccional lineal con datos de posicionamiento, a 72h.** Sharpe neto 1,37, 4 de 5 años positivos
   (2022 +75 %, 2023 −17 %, 2024 +103 %, 2025 +59 %, 2026 +37 %, sumas simples), win rate por periodo del 54 %, PF 1,48.
   Pero: Deflated Sharpe 0,78 (< 0,90), caída máxima del 35 %, y su versión con LightGBM cae a Sharpe 0,42 (poco robusto al modelo).
   El mismo modelo sin posicionamiento, en los mismos años, rinde parecido: gran parte del resultado es la ventana 2022–2026.
   **Estado: candidato a prueba hacia delante, no aprobado.**
3. Los datos de posicionamiento aportan poco: solo interés abierto / volumen tiene fuerza.
4. Tras 374 pruebas, el carry de funding sigue siendo la única ventaja aprobada.
