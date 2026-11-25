# Lección 45 — Gestión de cartera: asignación por régimen y control de caídas

## 1. Pre-registro (antes de calcular resultados)
Bloques diarios A (ejecutable), E, B, D y G como en la Lección 43; reequilibrio mensual; mitades 2020-07 → 2022-12 y 2023-01 → 2026-10.
Referencia: **P0 pesos iguales.**
**R1 — Asignación por régimen:** régimen = BTC sobre (alcista) o bajo (bajista) su media simple de 200 días, con el dato del último
día del mes anterior. Alcista: D, G y A pesan 1,5 y B y E 0,5; bajista: al revés (luego se normaliza a suma 1).
**R2 — Control de caídas:** cartera P0, pero si su caída desde el máximo (medida al cierre del día anterior) supera el 5 %, la exposición
pasa a 0,5 hasta que la caída vuelva a ser menor del 2,5 %.
**Criterio:** Sharpe mayor en las dos mitades y caída máxima no mayor que P0. Pruebas nuevas: 2.

## 2. Resultados — `l45_salida.txt`
| | 2020-07→2022: Sharpe / caída | 2023→2026-10: Sharpe / caída |
|---|---|---|
| P0 pesos iguales | 2,81 / 5,6 % | 1,96 / 6,5 % |
| R1 asignación por régimen | 2,75 / 5,9 % | 1,79 / 9,6 % |
| R2 control de caídas | 2,75 / 5,3 % | 1,81 / 5,9 % |
**Las dos se rechazan.** El régimen de BTC (media de 200 días) llega tarde: los bloques ya se adaptan solos (D deja de comprar en caídas,
B y E se activan con el pánico). El control de caídas recorta algo la caída pero se pierde parte del rebote; con caídas tan pequeñas
(≈ 6 %) no compensa. Junto con la Lección 43: **los pesos iguales siguen siendo la mejor construcción.**

## 3. Pre-registro adicional (antes de calcular): G1 — filtro de euforia en el bloque G
Igual que el aprobado en D (Lección 43): G no abre si el funding medio de 3 días de la moneda > 0,03 % por 8 h. BTC, ETH y SOL, reglas
idénticas del motor A. Desarrollo 2020-03 → 2023-06; examen 2023-07 → 2026-10. Criterio: E[R] mayor en los dos periodos y con al menos el
80 % de las operaciones de G conservadas. Prueba nueva: 1.
