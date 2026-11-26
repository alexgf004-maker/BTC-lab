# Lección 53 — Patrones chartistas como ayuda para los bloques que ya funcionan

Pregunta del usuario: aunque los patrones no ganen solos (L52), ¿mejoran alguna estrategia existente? Idea: un doble techo o un HCH
(las figuras bajistas, las únicas con algo de señal en L52) podrían avisar de que un largo de D o de G va a salir mal, o reforzar un
corto de B; y las figuras alcistas podrían avisar de que un corto de B es peligroso.

## 1. Pre-registro (subido antes de calcular ningún resultado)
Detector de figuras: exactamente el de la L52 (giros 3 ATR en velas de 4 h, mismas tolerancias). "Figura bajista" = ruptura de un doble
techo o de un HCH; "figura alcista" = ruptura de un doble suelo, HCH invertido o triángulo ascendente. "Reciente" = en las 30 velas
de 4 h anteriores (5 días). Las figuras se buscan en el gráfico en dólares de la moneda.

**C1 — D sale antes si aparece una figura bajista.** D actual (piramidación + filtro de euforia, lección 43/45). Si estando dentro se
rompe un doble techo o un HCH en esa moneda, se cierra al cierre de esa vela.
**C2 — D no entra si hubo una figura bajista reciente.**
Criterio C1 y C2 (el de la L43): Sharpe mayor que D actual en desarrollo (2020-03 → 2023-06) **y** examen (2023-07 → 2026-10), y
caída máxima no mayor.

**C3 — B no abre el corto si la altcoin tuvo una figura alcista reciente.**
**C4 — B arriesga 1,5 veces más si la altcoin tuvo una figura bajista reciente.**
Criterio C3 y C4 (el de la L44): Sharpe mayor que B actual en las dos mitades (2020-03 → 2022-12 y 2023-01 → 2026-10) y caída
máxima no mayor.

**C5 — G no compra si hubo una figura bajista reciente en la moneda.** G actual (con filtro de euforia).
Criterio (el de la L45, G1): ganancia media por operación mayor en desarrollo (2020–2022) y examen (2023 → 2026-10), conservando al
menos el 80 % de las operaciones. (Simplificación declarada: las operaciones de G se filtran después de simularlas; quitar una no
libera hueco para otra.)

Pruebas nuevas: 5.

## 2. Resultados — `l53_salida.txt`
| Variante | Desarrollo | Examen | ¿Pasa? |
|---|---|---|---|
| D actual | Sharpe 1,23 · caída 5,8 % | Sharpe 0,64 · caída 12,6 % | — |
| C1 D sale con figura bajista | 1,20 · 5,8 % | 0,60 · 12,7 % | No (peor) |
| C2 D no entra tras figura bajista | 1,23 · 6,0 % | 0,64 · 12,6 % | No (igual; casi no actúa) |
| B actual | Sharpe 1,56 · caída 30,4 % | Sharpe 0,82 · caída 33,8 % | — |
| C3 B sin cortos tras figura alcista | 1,50 · 29,2 % | 0,85 · 31,3 % | No (peor en 2020–22) |
| C4 B riesgo ×1,5 tras figura bajista | 1,60 · 31,2 % | 0,79 · 37,1 % | No |
| G actual (con euforia) | +0,708R (n 150) | +0,827R (n 239) | — |
| **C5 G sin compras tras figura bajista** | **+0,739R** (n 142, 95 %) | **+0,885R** (n 229, 96 %) | **Sí** |

**C5 pasa el criterio**, pero con una muestra pequeña: quita 18 operaciones en 6 años (2 en 2020 con +0,67R de media, 6 en 2022 con
−0,01R, 5 en 2025 con +0,11R, 5 en 2026 con −1,12R). Las operaciones quitadas fueron peores que la media en 3 de esos 4 años. Mejora
pequeña y coherente con la L52 (las figuras bajistas avisan algo en cripto).

Paridad del detector: el módulo del bot (`bot/patrones.py`) encuentra exactamente las mismas rupturas que la investigación
(BTC 48, ETH 44, SOL 25). **Doble comprobación con el código del bot** (repetición hora a hora de 2022, el año en que más actúa):
| | Investigación | Bot |
|---|---|---|
| Sin filtro de figuras | 50 operaciones, +0,318R | 50 operaciones, +0,319R (saldo 2.400 → 2.473) |
| Con filtro de figuras | 44 operaciones, +0,363R | 44 operaciones, +0,343R (saldo 2.400 → 2.470; 7 señales omitidas) |
Mismo sentido: menos operaciones y mejor resultado medio por operación, con el mismo beneficio total (el filtro quita riesgo, no
añade ganancia). En los 6 años de la investigación, el total en R es casi el mismo (303,9R sin filtro, 307,6R con filtro).

**Activado en el bot** (`filtro_figuras: true` en G; se puede apagar). Es una mejora pequeña: G opera ~5 % menos con el mismo
resultado.
