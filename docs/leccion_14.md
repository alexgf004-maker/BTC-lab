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

## 2. Resultados — `l14_salida_W.txt`, `l14_salida_W3_estres.txt`, `l14_salida_G1_V1.txt`

### W1-R — Robustez a la profundidad (todas las candidatas, 218 monedas)
| Profundidad | n | Con stop: E / PF | **Sin stop: E / PF / win rate** |
|---|---|---|---|
| 3σ (−3,3 %) | 43 215 | −0,007R / 0,98 | +0,147R / 1,44 / 84 % |
| 4σ (−4,4 %) | 19 152 | −0,001R / 1,00 | +0,173R / 1,60 / 82 % |
| 5σ (−5,4 %) | 10 336 | +0,017R / 1,05 | +0,207R / 1,82 / 81 % |
| 6σ (−6,5 %) | 6 284 | +0,019R / 1,05 | +0,230R / 2,02 / 80 % |
| 7σ (−7,6 %) | 4 188 | +0,031R / 1,09 | +0,270R / 2,41 / 81 % |

La ventaja crece suavemente con la profundidad: es un mecanismo, no un artefacto de 5σ.
(Las cifras "con stop" incluyen todas las candidatas, también las recompras hora tras hora durante un desplome; la cartera de W1 toma solo la primera por moneda y por eso rendía +0,079R.)

### W2 — Vender las mechas hacia arriba: RECHAZADA
Criba: Sharpe −1,38, PF 0,84, pierde todos los años. Asimetría confirmada (como en H3b): las subidas violentas continúan; las caídas violentas rebotan.

### W3 — Mechas sin stop a mercado (comparación de diseño, monedas ya vistas con W1)
| | Sharpe | Win rate | PF | E por trade | Años positivos | Peor trade |
|---|---|---|---|---|---|---|
| Diseño (57) | 2,51 | 81 % | 1,99 | +0,216R | 7 de 7 | −8,3R |
| Examen (161) | 2,01 | 80 % | 1,81 | +0,190R | 7 de 7 | −6,2R |

Salidas: 78 % en el objetivo, 22 % a las 24 h. **Quitar el stop multiplica la ventaja por tres:** en una mecha de liquidación el stop
vende en el suelo justo antes del rebote. El riesgo pasa de "muchas pérdidas pequeñas" a "pocas pérdidas grandes".

**Pruebas de estrés (tamaño y peor caso intrahorario, midiendo la caída en los mínimos de cada hora):**
| Riesgo nominal por trade | CAGR diseño / examen | DD en cierres | DD en mínimos (peor caso) | Peor día | Exposición máx. |
|---|---|---|---|---|---|
| 0,50 % | 77 % / 48 % | 25 % / 29 % | **68 % / 81 %** | −24 % / −29 % | 2,7x / 1,5x |
| 0,25 % | 34 % / 22 % | 12,5 % / 14,5 % | 34 % / 40 % | −12 % / −14,5 % | 1,2x / 0,7x |
| 0,10 % | 12,5 % / 8,5 % | 5,0 % / 5,8 % | 14 % / 16 % | −4,8 % / −5,8 % | 0,5x / 0,3x |

Días de desplome (todas las candidatas): 2021-05-19 +0,78R de media; 2024-08-05 +0,34R; 2022-05-11 (LUNA) −0,19R;
**2022-11-08 (FTX) −1,74R; 2025-10-10 −2,18R** (el peor día: −5,8 % con el 0,10 % de riesgo).
82 % de meses positivos. Deflated Sharpe con 387 pruebas: ver salida (informativo; no es un examen limpio).

**Estado de W3: candidata fuerte, no aprobada formalmente.** A favor: réplica en dos conjuntos, variación suave con la profundidad,
causa económica, simulación sin el problema del deslizamiento del stop. En contra: (1) es la tercera variante de una familia ya vista
en estas monedas; (2) perfil de vendedor de seguros: la cola (dos desplomes en 6,6 años) está poco muestreada y la próxima puede ser peor;
(3) exige exposición total ≤ 1x y sin apalancamiento real para sobrevivir a un 2025-10-10.

### G1 — Grid neutral: RECHAZADA
| Escalón | BTC | ETH | 50/50 |
|---|---|---|---|
| 0,3 % | −52 % anual | −85 % anual | −57 % anual |
| 0,5 % | −25 % anual | −62 % anual | −32 % anual (DD 94 %) |
| 1,0 % | −9,5 % anual | −30 % anual | −16 % anual |

Más de 200 salidas de rango por activo en 6,8 años: cada una borra cientos de escalones cobrados. Solo gana en años laterales (2023, 2025).
La estrategia automática más popular entre minoristas es, en un ciclo completo, una máquina de perder.

### V1 — Prima de volatilidad (2023-06 → 2026-10)
| | Implícita media | Realizada media | Prima | Días con prima positiva |
|---|---|---|---|---|
| BTC | 51,2 | 43,9 | +7,2 puntos | 75 % |
| ETH | 65,4 | 61,5 | +3,9 puntos | 64 % |

La prima existe, pero vender straddles sin cubrir no la captura: BTC +0,09 % mensual (69 % de meses ganadores, PF 1,03, peor mes −35 %);
ETH negativo. Capturarla exige cobertura delta diaria con opciones: fuera del alcance actual. En 2026 la prima de BTC es de solo 1,6 puntos.

## 3. Conclusiones
1. La familia de las mechas es real y asimétrica: comprar caídas forzadas funciona; vender subidas forzadas no.
2. **W3 (sin stop) es la segunda mejor estrategia del proyecto tras el carry**, con la advertencia de que su riesgo es de cola.
3. Grid y venta de volatilidad sin cubrir: rechazadas.
