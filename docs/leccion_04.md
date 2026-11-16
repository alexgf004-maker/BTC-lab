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
