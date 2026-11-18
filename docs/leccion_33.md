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

## 2b. Pre-registro adicional (tras ver T1–T4, antes de calcular T5)
T3 acierta el 60 %, pero con un objetivo de solo 0,5 veces el riesgo. La afirmación original es "60 % con 1:2".
**T5 — T3 con objetivo fijo a 2 veces el riesgo** (en lugar del extremo opuesto de C1). Todo lo demás igual. Mismo criterio. Prueba nueva: 1.

## 3. Resultados — `l33_salida.txt`, `l33_salida_T5.txt` (≈ 120 000 operaciones simuladas)
| Prueba | Desarrollo: E / acierto | **Examen: E / acierto** | Objetivo/riesgo | PF examen |
|---|---|---|---|---|
| T1 CRT 4h | −0,100R / 46 % | **−0,124R (t −13) / 46 %** | 1,24 | 0,78 |
| T2 CRT diario | −0,016R / 47 % | **−0,053R (t −2,1) / 46 %** | 1,35 | 0,90 |
| T3 CRT 4h + CISD 1h | −0,068R / 61,5 % | **−0,086R (t −8,9) / 60,7 %** | 0,52 | 0,76 |
| T4 CRT diario + CISD 4h | −0,023R / 58 % | **−0,025R (t −1,9) / 59 %** | 0,67 | 0,93 |
| T5 = T3 con objetivo 1:2 | −0,046R / 43 % | **−0,087R (t −4,7) / 41 %** | 2,00 | 0,83 |
Solo BTC y ETH: mismo panorama (examen entre −0,04R y −0,15R). **Ninguna se aprueba; todas pierden en el examen.**
Los costes (0,09–0,14 % del precio) suponen ≈ 0,1R por operación: **sin costes, la estrategia quedaría en torno a cero**, es decir,
no hay ventaja que proteger.

## 4. Qué nos enseña
1. **El 60 % de acierto es real… y no sirve.** CRT + CISD acierta el 60 % (exactamente lo que dice el post), pero porque el objetivo
   (el otro extremo de la vela anterior) queda a solo 0,5 veces el riesgo. Con 60 % de acierto y 0,5:1, la esperanza es negativa.
2. **"60 % con 1:2" no aparece en ninguna versión.** Al poner el objetivo a 2R, el acierto cae al 41 % (solo el 14 % llega al objetivo).
   Acierto y relación beneficio/riesgo no son independientes: subir uno baja el otro. Quien dice tener ambos (esperanza +0,8R) casi
   siempre ha cometido un error de backtest: mirar el futuro dentro de la vela, elegir a mano las operaciones, o reglas que cambian.
3. **Coherente con la Lección 26:** los extremos de la vela anterior se rompen MÁS que niveles al azar (stops y liquidaciones detrás).
   Apostar a que el barrido "falla" va contra ese efecto.
4. **Las otras publicaciones no se pueden validar:** 25 operaciones en 12 días con lotes variables (las ganadoras grandes coinciden con
   una subida fuerte del USDJPY) y una reversión a la media de 112 operaciones con backtest manual de 6,5 meses (t ≈ 2,5, un solo
   periodo, sin reglas ni costes). Sin reglas escritas no hay prueba posible, y la reversión a la media ya se rechazó en cripto 5 veces.

**Señales de alarma en estas afirmaciones:** acierto alto + relación alta a la vez; "validado en X años" sin datos; backtest manual;
capturas de pocos días; lotes que cambian entre operaciones; y sobre todo, que no publiquen las reglas para que otros las prueben.
