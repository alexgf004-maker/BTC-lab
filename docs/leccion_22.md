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
