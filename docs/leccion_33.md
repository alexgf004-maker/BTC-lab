# Lección 33 — Validar estrategias de redes sociales: CRT + CISD ("Smart Money / ICT")

## 0. Contexto
En un grupo de Facebook de traders aparecen tres afirmaciones:
1. Una captura de MetaTrader con 25 operaciones de forex en 12 días (+6,2 %), sin reglas.
2. **"CRT + CISD: 60 % de acierto con relación 1:2, validado en los últimos 7 años"** (esperanza +0,8R por operación).
3. Una reversión a la media con 112 operaciones en 6,5 meses de backtest manual (61,6 % de acierto, 1:1, PF 1,60), sin reglas.
Solo la 2 se puede convertir en reglas exactas. Una esperanza de +0,8R por operación sería de las mejores del mundo: hay que comprobarla.

## 1. Definiciones (versión estándar de los conceptos)
**CRT (Candle Range Theory):** una vela de marco alto C1 marca un rango [mínimo, máximo]. La vela siguiente C2 **barre** un extremo
(supera el máximo o pierde el mínimo, solo uno de los dos) y **cierra de vuelta dentro del rango**. Se opera en contra del barrido
(barrido del máximo → corto) buscando el **extremo opuesto del rango de C1**; stop en el extremo del barrido.
**CISD (Change in State of Delivery):** confirmación en un marco menor. Tras el barrido del máximo, se toma la racha de velas alcistas
consecutivas del marco menor que llevó al máximo; la entrada llega cuando una vela del marco menor **cierra por debajo de la apertura
de esa racha** (y al revés en el barrido del mínimo).

## 2. Pre-registro (antes de calcular ningún resultado)
**T1 — CRT 4h:** entrada al cierre de C2; stop en el extremo de C2; objetivo en el extremo opuesto de C1. Riesgo mínimo 0,5 % del precio.
**T2 — CRT diario:** igual con velas diarias; riesgo mínimo 1 %.
**T3 — CRT 4h + CISD en 1h:** la confirmación debe llegar en las 4 h siguientes al cierre de C2 y antes de que el precio toque el stop
o el objetivo; entrada al cierre de esa vela de 1h; mismo stop y objetivo.
**T4 — CRT diario + CISD en 4h:** igual, con la confirmación en las 24 h siguientes.
Salida máxima: 3 velas del marco alto después de C2 (a mercado). Si en la misma vela de 1h se alcanzan stop y objetivo → pérdida.
**Costes:** entrada a mercado 0,07 % (taker + deslizamiento); objetivo con orden limit 0,02 %; stop o salida por tiempo 0,07 %.
**Activos:** BTC, ETH y las 20 criptos más líquidas de cada mes (point-in-time, con deslistadas), perpetuos USDT de Binance.
**Periodos:** desarrollo 2020-03 → 2023-06; **examen 2023-07 → 2026-10** (una vez).
**Criterio:** esperanza neta > 0 con t ≥ 3 (agrupando por día) en el examen y positiva en desarrollo. Se informa también acierto,
relación beneficio/riesgo media, PF y el resultado solo en BTC y ETH. Pruebas nuevas: 4.
