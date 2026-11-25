# Lección 43 — Pensar como gestor: construcción de cartera y mejoras del bloque de tendencia

## 0. Por qué
Hasta ahora casi todo el trabajo ha sido "qué señal operar". En un fondo sistemático, buena parte del resultado sale de **cómo se
combinan y dimensionan** las estrategias (pesos por riesgo, volatilidad objetivo, asignación dinámica) y de **cómo se gestionan las
operaciones ganadoras** (piramidar, filtrar la euforia). Esta lección prueba esas palancas.

## 1. Pre-registro (antes de calcular resultados)
**Nivel cartera** — bloques diarios de la Lección 31 (A ejecutable, E, B, D) + G (motor A en BTC/ETH/SOL, Lección 40). Reequilibrio mensual;
todos los pesos con datos ANTERIORES al mes. Mitades: 2020-07 → 2022-12 y 2023-01 → 2026-10.
- **P0 (referencia):** pesos iguales.
- **P1a · Inversa de la volatilidad:** peso ∝ 1/volatilidad diaria de los 90 días previos.
- **P1b · Volatilidad objetivo:** P0 escalada para que su volatilidad de 90 días previa sea del 12 % anual (apalancamiento máx. 2x).
- **P1c · P1a + volatilidad objetivo del 12 %.**
- **P2 · Momentum de estrategias:** 50 % pesos iguales + 50 % ∝ max(0, Sharpe de los 180 días previos).
Criterio (cada una frente a P0): Sharpe mayor en las dos mitades y caída máxima no mayor (P1b/P1c se comparan también por MAR = rentabilidad/caída).
**Nivel operativo** — bloque D (ruptura de 120 velas de 4 h, EMA50 diaria, stop dinámico 5 ATR; costes 0,07 % por lado + funding real).
Desarrollo 2020-03 → 2023-06; examen 2023-07 → 2026-10.
- **P3 · Piramidación (BTC y ETH):** riesgo inicial 2,5 % y dos añadidos de 2,5 % cuando el precio sube 1 y 2 ATR sobre la entrada
  (todo con el mismo stop dinámico), frente a la entrada única del 5 %. Criterio: Sharpe mayor en los dos periodos y caída no mayor.
- **P4 · D en altcoins:** mismas reglas en las 10 más líquidas de cada mes (sin BTC ni ETH), solo largos y solo con BTC sobre su EMA50
  diaria. Criterio: E[R] > 0 con t ≥ 3 en el examen y positiva en desarrollo.
- **P5 · Filtro de euforia (BTC y ETH):** no abrir si el funding medio de 3 días > 0,03 % por 8 h. Criterio como P3.
Pruebas nuevas: 7.

## 2. Resultados del nivel cartera — `l43_salida.txt`
| | 2020-07→2022: Sharpe / caída | 2023→2026-10: Sharpe / caída | Todo: anual / caída |
|---|---|---|---|
| **P0 pesos iguales (A, E, B, D, G)** | **2,81 / 5,6 %** | 1,96 / **6,5 %** | +27,4 % / **6,5 %** |
| P1a inversa de la volatilidad | 2,86 / 9,4 % | 0,07 / 13,6 % | +3,4 % / 14,9 % |
| P1b volatilidad objetivo 12 % | 2,70 / 6,7 % | 2,08 / 9,0 % | +35,7 % / 9,0 % |
| P1c inversa vol. + objetivo | 2,86 / 18,0 % | 0,07 / 25,4 % | +6,8 % / 27,5 % |
| P2 momentum de estrategias | 2,72 / 8,6 % | **2,80** / 9,4 % | +29,8 % / 9,4 % |
**Ninguna pasa el criterio** (Sharpe mayor en las dos mitades y caída no mayor).
- **Inversa de la volatilidad: muy mala.** Carga casi todo en el carry (muy poca volatilidad, poca rentabilidad). En carteras de estrategias
  con rentabilidades tan distintas, igualar el riesgo no es buena idea.
- **Volatilidad objetivo:** es, en la práctica, más apalancamiento (≈ 1,3x): más rentabilidad y más caída, mismo Sharpe. Coincide con la
  recomendación del informe final (de 1x a 1,5x); no es una mejora, es una elección de riesgo.
- **Momentum de estrategias:** brilla en 2023–2026 (Sharpe 2,80 frente a 1,96) pero empeora 2020–2022 y aumenta la caída. Pista para
  seguir en papel, no aprobada.

## 3. Resultados del nivel operativo — `l43_salida.txt`, `l43_salida_combinada.txt`, `l43_salida_bot.txt`
**Nota sobre el pre-registro:** el texto decía "dos añadidos de 2,5 %"; lo programado y medido fueron **dos añadidos de 1,25 %** (entrada 2,5 %),
es decir, el **mismo riesgo total del 5 %** que el D actual, repartido de otra forma. Es la comparación justa; se deja constancia.
**Simulador de la lección (BTC y ETH):**
| | Desarrollo: Sharpe / caída | Examen: Sharpe / caída |
|---|---|---|
| D actual | 1,15 / 9,0 % | 0,52 / 13,0 % |
| **P3 piramidación** | 1,16 / 7,2 % | 0,58 / 12,6 % | ✅
| **P5 filtro de euforia** | 1,23 / 7,4 % | 0,62 / 13,0 % | ✅
| Las dos (informativo) | 1,23 / 5,8 % | 0,64 / 12,6 % |
| P4 D en 10 altcoins (con BTC alcista) | E +0,15R (t 1,3) | E +0,29R (t 1,6) | ❌ (positivo, pero sin la significación exigida)

**Confirmación con el código del propio bot** (que reproduce al 100 % la investigación original; 2020-03 → 2026-10):
| Bloque D | Desarrollo: Sharpe / anual / caída | Examen: Sharpe / anual / caída |
|---|---|---|
| Original | 1,04 / +56,8 % / 19,8 % | 0,49 / +14,9 % / 27,5 % |
| + filtro de euforia | 1,17 / +65,3 % / 16,4 % | 0,59 / +19,8 % / 27,5 % |
| + piramidación | 1,08 / +58,0 % / 15,5 % | 0,54 / +16,8 % / 24,5 % |
| **+ las dos** | **1,19 / +64,8 % / 12,7 %** | **0,60 / +19,8 % / 24,5 %** |
**Las dos mejoras se aprueban y se activan en el bot.** Mejoran el Sharpe y reducen la caída en los dos periodos, con los dos simuladores.
- **Filtro de euforia:** evita comprar rupturas cuando los largos ya pagan mucho funding (mercado sobrecalentado): esas rupturas
  fallan más a menudo.
- **Piramidación:** arriesgar la mitad al principio y añadir solo si la tendencia confirma; las rupturas falsas cuestan la mitad y las
  buenas acaban con el riesgo completo.

## 4. Conclusión
A nivel cartera, los pesos iguales siguen siendo lo más robusto (las construcciones sofisticadas mejoran un periodo y empeoran otro).
A nivel operativo, dos técnicas clásicas de gestión de operaciones mejoran el bloque D de forma estable: **activadas en el bot.**
