# Lección 22 — Validación final de la cartera

## 1. Pre-registro
1. **Cartera de conjunto (sin sesgo de elección de parámetros):** B y D se sustituyen por el promedio diario de las 20 combinaciones de
   sus rejillas (cada combinación con 1/20 del capital del bloque). A y E se mantienen (sus rejillas son casi planas).
   Pesos 1/4 por bloque, reequilibrio mensual.
2. **Descuento por degradación:** las estrategias publicadas pierden de media entre un tercio y la mitad de su rendimiento fuera de muestra.
   Se evalúa la cartera restando a cada bloque un rendimiento constante que reduzca su Sharpe a la mitad.
3. **Remuestreo por bloques de 3 meses** (10 000 caminos de 1 y 3 años), con y sin descuento, para apalancamientos 1x, 1,5x y 2x:
   rentabilidad mediana, percentil 5, probabilidad de perder y probabilidad de una caída > 20 % y > 30 %.
4. Recomendación de tamaño: el mayor apalancamiento con P(caída > 30 % en 3 años) ≤ 5 % **en el escenario con descuento**.

## 2. Resultados — `l22_salida.txt`
**Bloques:** S1 como conjunto de 20 combinaciones rinde MÁS que el elegido (Sharpe 1,32 frente a 1,13); la tendencia, MENOS (0,74 frente a 1,06),
como anticipó la Lección 21.

| Cartera (1/4 por bloque) | Sharpe | CAGR | Caída máx. | Peor mes | Meses + |
|---|---|---|---|---|---|
| Original (parámetros elegidos) | 2,23 | 34,9 % | 7,7 % | −3,9 % | 70 % |
| De conjunto (sin sesgo de parámetros) | 2,19 | 33,6 % | 7,7 % | −4,1 % | 70 % |
| **De conjunto con descuento (Sharpe de cada bloque a la mitad)** | **1,12** | **15,4 %** | **10,8 %** | −5,3 % | 59 % |

Por año (conjunto / con descuento): 2020 +55 % / +37 %; 2021 +23 % / +7 %; 2022 +33 % / +14 %; 2023 +40 % / +21 %; 2024 +39 % / +20 %;
2025 +31 % / +13 %; 2026 +7 % / −5 %.

**Remuestreo (10 000 caminos, bloques de 3 meses), escenario CON descuento:**
| Apalancamiento | 1 año: mediana / p5 | P(perder en 1 año) | 3 años: mediana / p5 | P(caída > 20 % en 3 años) | P(caída > 30 % en 3 años) |
|---|---|---|---|---|---|
| 1x | +15 % / −4 % | 11 % | +57 % / +10 % | 4 % | 0,1 % |
| **1,5x** | **+23 % / −7 %** | **12 %** | **+93 % / +14 %** | **32 %** | **2,8 %** |
| 2x | +31 % / −10 % | 12 % | +134 % / +16 % | 74 % | 16 % |
| 3x | +46 % / −16 % | 14 % | +231 % / +17 % | 99 % | 68 % |

**Recomendación (regla pre-registrada): apalancamiento máximo de la cartera 1,5x.** Para empezar, 1x.
