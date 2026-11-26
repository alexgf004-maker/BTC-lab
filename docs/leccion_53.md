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
