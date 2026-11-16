# Lección 3 — Hipótesis B: seguimiento de tendencia (ruptura + stop dinámico)

## 1. Pre-registro (commiteado ANTES de ver resultados)

**Por qué podría funcionar:** la Lección 2 mostró que entrar al azar a favor de la tendencia diaria
ya tiene PF 1,19. Las criptos tienen **momentum de serie temporal**: las tendencias
duran más de lo que el azar predice (flujos de capital lentos, apalancamiento, FOMO). Para capturarlo
hay que **dejar correr las ganancias** y cortar rápido las pérdidas: win rate bajo, ganancias grandes.

**Universo, datos y división:** idénticos a la Lección 2 (10 perpetuos, 4h a partir de 1h;
en muestra 2020-2023, fuera de muestra 2024-01 → 2026-10, se mira una sola vez).

**Reglas (largos; los cortos son el espejo y se evalúan aparte):**
1. Filtro: último cierre diario COMPLETO > EMA50 diaria.
2. Entrada: cierre 4h > máximo de las N velas anteriores (ruptura de Donchian). Se entra a
   la APERTURA de la vela siguiente con orden a mercado (taker 0,05 % + slippage 0,02 %).
3. Stop inicial: entrada − m·ATR14(4h). Ese riesgo define 1R.
4. Stop dinámico (chandelier): al cierre de cada vela, stop = max(stop, máximo desde la entrada − m·ATR).
   Nunca baja. Se aplica desde la vela siguiente. Sin objetivo fijo ni límite de tiempo.
5. Salida: si se toca el stop → taker + slippage; si hay gap, a la apertura.
6. Una posición por activo. Funding histórico real.

**Rejilla (solo en muestra):** N ∈ {30, 60, 120, 180} velas (5, 10, 20, 30 días), m ∈ {2, 3, 4, 5} → 16 combinaciones.
**Elección:** ≥ 300 trades en muestra; máxima media de E neta de la celda y sus vecinas.
**Control:** mismo número de entradas, al azar dentro de la tendencia diaria, con las MISMAS salidas.
**Variante de win rate (informativa, no cambia la elección):** cerrar el 50 % en +1R (limit, maker)
y dejar correr el resto. Mide cuánta esperanza cuesta subir el win rate.

**Aprobación fuera de muestra:** PF neto ≥ 1,3; ≥ 300 trades (sumando activos); E > control;
E > 0 en la mayoría de activos y años.
