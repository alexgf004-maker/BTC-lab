# Lección 39 — "La biblia del trading con velas": ruptura, retroceso, pin bar y confluencias

## 0. La estrategia (price action clásico)
Tendencia → el precio rompe una resistencia → vuelve a probarla (ahora soporte) → aparece una **pin bar** de rechazo en ese nivel,
idealmente con **confluencia** (media móvil de 21 periodos como soporte dinámico y retroceso de Fibonacci del 50–61,8 %) → entrada
"conservadora" en el 50 % de la pin bar, stop bajo la mecha, objetivo amplio (el libro muestra 1:5). Ejemplos del libro en velas de 4 h.

## 1. Pre-registro (antes de calcular ningún resultado). Velas de 4 h. Largos y cortos simétricos (se describe el largo).
- **Tendencia:** cierre > media de 21 > media de 50.
- **Nivel y ruptura:** nivel = máximo de las 40 velas anteriores; ruptura = una vela cierra por encima del nivel.
- **Retroceso con pin bar:** en las 20 velas siguientes a la ruptura, una vela con **mecha inferior ≥ 2/3 de su rango** y cierre en el tercio
  superior, cuyo mínimo toca la zona del nivel (a menos de 0,5 ATR(14) por encima o por debajo) sin cerrar por debajo del nivel − 0,5 ATR.
- **P1 — Base:** tendencia + ruptura/retroceso + pin bar en el nivel.
- **P2 — Máxima confluencia:** P1 + el mínimo de la pin bar a menos de 1 ATR de la media de 21 + profundidad del retroceso entre el 38,2 % y
  el 78,6 % de Fibonacci (impulso: del mínimo de las 40 velas previas a la ruptura al máximo alcanzado tras la ruptura).
- **Entrada conservadora:** orden limit en el 50 % de la pin bar, válida 3 velas. **Entrada agresiva (solo P1):** al cierre de la pin bar.
- **Stop:** mínimo de la pin bar − 0,1 ATR. **Objetivo:** 2 o 5 veces el riesgo. Máximo 60 velas (10 días). Si en una vela se tocan stop y
  objetivo → pérdida; si la vela que ejecuta la limit toca también el stop → pérdida.
- **Pruebas:** P1 conservadora 1:2 y 1:5; P2 conservadora 1:2 y 1:5; P1 agresiva 1:2. Pruebas nuevas: 5 (× 2 mercados).
**Mercados y costes:**
- Forex: 10 pares de la Lección 35 (2012–2026), mismos costes (0,5–1,5 pb por lado + 0,3 pb de deslizamiento en stops y entradas a mercado).
  Desarrollo 2012–2018; **examen 2019 → 2026-10.**
- Cripto: BTC, ETH y las 20 más líquidas de cada mes (perpetuos de Binance, con deslistadas). Limit y objetivo 0,02 %; mercado y stop
  0,07 %. Desarrollo 2020-03 → 2023-06; **examen 2023-07 → 2026-10.**
**Criterio (en cada mercado por separado):** esperanza neta > 0 con t ≥ 3 (agrupando por día) en el examen y positiva en desarrollo.

## 2. Resultados — `l39_salida.txt`
**Forex (10 pares, 4 h):**
| | Desarrollo 2012–2018 | **Examen 2019–2026** | Examen sin costes |
|---|---|---|---|
| P1 conservadora 1:2 | −0,34R / 27 % acierto | **−0,34R (t −6,7) / 28 %** | −0,17R |
| P1 conservadora 1:5 | −0,28R / 15 % | **−0,33R (t −4,2) / 14 %** | −0,14R |
| P2 confluencia 1:2 | −0,13R (n 15) | **−0,56R (n 35)** | −0,28R |
| P2 confluencia 1:5 | −0,33R (n 15) | **−0,82R (n 35)** | −0,52R |
| P1 agresiva 1:2 | −0,22R / 30 % | **−0,26R (t −5,9) / 29 %** | −0,12R |
**Cripto (BTC, ETH y top 20, 4 h):**
| | Desarrollo 2020–2023 | **Examen 2023–2026** |
|---|---|---|
| P1 conservadora 1:2 | −0,02R / 34 % | **−0,14R (t −2,2) / 31 %** |
| P1 conservadora 1:5 | +0,16R / 20 % | **−0,10R / 17 %** |
| P2 confluencia 1:2 | +0,44R (t 2,5) / 49 % (n 94) | **−0,01R / 36 % (n 67)** |
| P2 confluencia 1:5 | +0,98R (t 3,2) / 34 % (n 94) | **+0,07R (t 0,7) / 21 % (n 67)** |
| P1 agresiva 1:2 | −0,04R / 34 % | **−0,12R (t −2,3) / 32 %** |

**NO aprobada en ningún mercado.**
- **Forex:** pierde incluso sin costes. Con objetivo 1:2 hace falta acertar el 33 % para no perder y acierta el 27–29 %: en divisas, los
  retrocesos al nivel roto suelen ser rupturas fallidas, no "segundas oportunidades".
- **Cripto: la lección más valiosa.** La versión con máxima confluencia (P2) parecía excelente en 2020–2023 (+0,98R por operación, t 3,2):
  exactamente el tipo de resultado que se publica en un libro. En los años siguientes, con las mismas reglas, se quedó en cero.
  Con pocas operaciones (94) y muchas condiciones, es fácil que el pasado "confirme" una estrategia por azar.
- **La confluencia reduce mucho las señales** (de ~700 a ~50–90 en 6 años) sin mejorar el resultado en datos nuevos.
