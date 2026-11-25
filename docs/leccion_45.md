# Lección 45 — Gestión de cartera: asignación por régimen y control de caídas

## 1. Pre-registro (antes de calcular resultados)
Bloques diarios A (ejecutable), E, B, D y G como en la Lección 43; reequilibrio mensual; mitades 2020-07 → 2022-12 y 2023-01 → 2026-10.
Referencia: **P0 pesos iguales.**
**R1 — Asignación por régimen:** régimen = BTC sobre (alcista) o bajo (bajista) su media simple de 200 días, con el dato del último
día del mes anterior. Alcista: D, G y A pesan 1,5 y B y E 0,5; bajista: al revés (luego se normaliza a suma 1).
**R2 — Control de caídas:** cartera P0, pero si su caída desde el máximo (medida al cierre del día anterior) supera el 5 %, la exposición
pasa a 0,5 hasta que la caída vuelva a ser menor del 2,5 %.
**Criterio:** Sharpe mayor en las dos mitades y caída máxima no mayor que P0. Pruebas nuevas: 2.
