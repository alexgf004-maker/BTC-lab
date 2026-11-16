# Lección 4 — Cartera: tamaño de posición, riesgo simultáneo y walk-forward

## 1. Pre-registro (commiteado ANTES de ver resultados)

**Estrategia:** la de la Lección 3, congelada (largos, N = 120, m = 5), en los 10 activos.

**Simulación de cartera:**
- Un solo capital inicial (1,0), interés compuesto. Eventos (entradas/salidas) en orden cronológico.
- Tamaño: `riesgo $ = riesgo % × saldo realizado en el momento de entrar`; unidades = riesgo $ / R.
- Curva de capital **marcada a mercado** cada 4h (incluye las ganancias que se devuelven al subir el stop).
- **Límite de posiciones simultáneas K:** si ya hay K abiertas, la señal nueva se descarta.
- Corta-circuitos (Lección 1c): con DD > 15 % el riesgo baja a la mitad; con DD > 30 % no se abren más
  posiciones hasta recuperar el DD < 15 %. (Se simula con y sin ellos.)

**Configuraciones:** riesgo ∈ {1 %, 2 %, 3 %} × K ∈ {10 (sin límite), 5, 3}.
**Métricas:** CAGR, DD máximo (a mercado), peor mes, meses en pérdida desde el máximo, apalancamiento nocional
máximo (suma de nocionales / capital) y Monte Carlo por bloques de 3 meses (10 000 caminos de 3 años) → DD p95.

**Regla de elección:** la configuración de mayor CAGR mediano en Monte Carlo con **DD p95 ≤ 35 %** y
apalancamiento nocional máximo ≤ 3x.

**Walk-forward (prueba del PROCESO de elección, no de unos parámetros):** ventana creciente.
Para cada año Y de 2022 a 2026: se elige (N, m) en la rejilla de la Lección 3 con la regla de las vecinas
usando SOLO datos hasta el 31-dic de Y−1 (mínimo 30 trades por año de entrenamiento), y se opera Y.
Se aprueba si el resultado encadenado tiene PF ≥ 1,3 y la mayoría de años son positivos.

## 2. Resultados — salida completa en `l04_salida.txt`

**Cordura:** sin límites, la cartera toma 525 trades (311 + 211 de la Lección 3 más los que cruzan el corte), E +0,49R, PF 2,45. ✅

### Periodo completo 2020-2026 (incluye los años de diseño) — selección
| Riesgo | K | Frenos | CAGR | DD máx. | DD p95 (MC) | Apal. máx. | Capital final |
|---|---|---|---|---|---|---|---|
| **1 %** | **10** | **no** | **37 %** | **26 %** | **31 %** | **1,5x** | **8,6x** |
| 1 % | 5 | no | 27 % | 19 % | 26 % | 1,0x | 5,2x |
| 2 % | 3 | no | 29 % | 27 % | 33 % | 1,3x | 5,6x |
| 2 % | 10 | no | 71 % | 42 % | 51 % | 2,8x | 39,8x |
| 3 % | 3 | no | 43 % | 37 % | 45 % | 2,0x | 11,4x |
| 3 % | 10 | no | 103 % | **54 %** | **66 %** | 4,0x | 124,9x |

### Solo fuera de muestra 2024-2026 (lo más fiable)
| Riesgo | K | CAGR | DD máx. | DD p95 (MC) | P(perder en 3 años) |
|---|---|---|---|---|---|
| **1 %** | **10** | **26 %** | **26 %** | **36 %** | **9 %** |
| 2 % | 10 | 45 % | 42 % | 59 % | 12 % |
| 3 % | 3 | 16 % | 37 % | 54 % | 27 % |
| 3 % | 10 | 59 % | 54 % | 74 % | 15 % |

### Hallazgos
1. **Repartir el riesgo vence a concentrarlo:** 1 % con hasta 10 posiciones (CAGR 37 %, DD 26 %) es mejor que
   3 % con un máximo de 3 (CAGR 43 %, DD 37 %). Limitar K obliga a saltarse señales, y la ventaja vive en unas pocas tendencias.
2. **El 3 % sin límite** multiplica el capital en el backtest, pero con DD real del 54 % y del 66–74 % en un mal escenario.
3. **Los corta-circuitos tal y como se pre-registraron son PERJUDICIALES:** con el 3 %, el bot se detuvo en
   julio de 2022 y nunca volvió a operar (sin operar no puede recuperar el DD). Hay que rediseñarlos
   (p. ej. pausa de duración fija o reinicio del máximo), y validarlos de nuevo antes de usarlos.
4. Siempre hay unos 13 meses seguidos sin nuevos máximos: es parte normal de la estrategia.

### Walk-forward (proceso de elección, ventana creciente)
| Año | Elegidos con datos previos | Trades | E | PF |
|---|---|---|---|---|
| 2022 | N 180, m 5 | 46 | −0,15R | 0,67 |
| 2023 | N 180, m 5 | 85 | +0,18R | 1,58 |
| 2024 | N 180, m 5 | 81 | +0,57R | 2,54 |
| 2025 | N 180, m 5 | 49 | +0,36R | 2,33 |
| 2026 | N 180, m 5 | 54 | 0,00R | 1,00 |
| **Encadenado** | | **315** | **+0,23R** | **1,65** |

PF ≥ 1,3 ✅ y 3 de 5 años positivos ✅ → **el proceso es robusto**: elige siempre la misma zona
(rupturas largas, stops anchos) y gana sin conocer el futuro. Los años bajistas o laterales (2022, 2026) quedan planos o en pérdida.

## 3. Decisión (por la regla pre-registrada)
Mayor CAGR mediano con DD p95 ≤ 35 % y apalancamiento ≤ 3x → **riesgo 1 % por trade, hasta 10 posiciones, sin corta-circuitos**
(sustituidos por un límite manual: revisar si el DD supera el 35 %).

El 3 % solicitado por el usuario queda como **techo**, no como punto de partida: con los datos actuales
implica caídas esperables del 45–70 %.
