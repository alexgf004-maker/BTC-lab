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
