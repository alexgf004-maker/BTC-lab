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

## 2. Resultados en muestra (2020-2023) — `l03_salida_diseno.txt`

**Largos:** las 16 combinaciones de la rejilla ganan; PF entre 1,08 y 2,67. Mejora con stops más anchos (m)
y rupturas más largas (N). Elegida por la regla pre-registrada: **N = 120 (20 días), m = 5**.

| | Trades | Win rate | E neta | PF |
|---|---|---|---|---|
| Estrategia | 311 | 40 % | **+0,57R** | **2,66** |
| Control (azar en tendencia, mismas salidas) | 2693 | 37 % | +0,35R | 2,18 |
| Variante 50 % en +1R | 311 | 46 % | +0,32R | 1,98 |

- Supera al control: la ruptura **sí** añade valor sobre el azar. Pero el control también gana mucho:
  gran parte de la ventaja está en la **salida** (dejar correr con un stop dinámico).
- 2021 aporta 122 de los 177R; 2022 (bajista) −0,17R. 8 de 10 activos positivos.
- Perfil típico de tendencia: trade mediano −0,33R; el 10 % mejor aporta más que el total.
- Cerrar el 50 % en +1R sube el win rate del 40 % al 46 %, pero **reduce la esperanza un 44 %**.
- Aviso: el óptimo está en el borde de la rejilla (m = 5). No ampliamos la rejilla para no sobreajustar.

**Cortos:** la combinación elegida (N = 120, m = 2) tiene PF 1,26 < 1,3 → **rechazados en muestra**. No se validan fuera de muestra.

**Congelado:** `l03_parametros_congelados.json` = LARGOS N = 120, m = 5. Se commitea ANTES de mirar 2024-2026.

## 3. Validación fuera de muestra (2024-01 → 2026-10, ejecutada UNA vez) — `l03_salida_validacion.txt`

| | Trades | Win rate | E neta | PF |
|---|---|---|---|---|
| **Estrategia** | 211 | 40 % | **+0,39R** | **2,19** |
| Control (azar en tendencia) | 1986 | 33 % | +0,11R | 1,32 |
| Variante 50 % en +1R | 211 | 44 % | +0,24R | 1,73 |

| Criterio pre-registrado | Resultado | |
|---|---|---|
| PF ≥ 1,3 | 2,19 | ✅ |
| ≥ 300 trades | **211** | ❌ |
| E > control | 0,39 frente a 0,11 | ✅ |
| E > 0 en la mayoría de activos | 10 de 10 | ✅ |
| E > 0 en la mayoría de años | 3 de 3 (2026 flojo: +0,07R) | ✅ |

**Robustez:** IC 95 % de E [+0,10; +0,78]R, P(E ≤ 0) ≈ 0,1 %. Sin XRP (que aportó 35R): E +0,25R, PF 1,76.
Sin los 5 mejores trades: PF 1,39. Sin los 10 mejores: PF 1,08 → la ventaja depende de **pocas tendencias grandes**:
no se puede saltar ni una señal.

## 4. Veredicto: APROBADA CON RESERVAS
Supera 4 de 5 criterios; falla el mínimo de trades (211 < 300). El rendimiento fuera de muestra es
un 30 % inferior al de muestra (normal) y sigue muy por encima del control.

**Riesgo nuevo detectado:** hasta **10 posiciones abiertas a la vez** (media ~3,7), todas muy correlacionadas.
Con un 3 % por trade, eso puede ser un 30 % de la cuenta en riesgo simultáneo cuando las criptos caen juntas.
Las estadísticas "por trade" y el Monte Carlo de la Lección 1c **subestiman** el drawdown real.

## 5. Próximo paso (Lección 4)
Simulación de **cartera**: capital único, interés compuesto, límite de riesgo total abierto,
walk-forward en ventanas móviles y curva de capital real con el 1 % y el 3 %. Después, el bot en testnet.
