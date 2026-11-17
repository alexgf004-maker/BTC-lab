# Lección 13 — Tres líneas con mecanismos y datos nuevos

## 1. Pre-registro (antes de calcular ningún resultado)

**W1 — Pescar las mechas (dar liquidez a vendedores forzados).**
*Origen:* comprar DESPUÉS de una cascada se quedó cerca (H3a Sharpe 0,95; N4 WR 66 %, PF 2,26) pero entra tarde y a mercado.
Aquí la orden ya está en el libro y quien vende en la mecha es el liquidado.
*Reglas (velas de 1h, universo point-in-time top 20):* al empezar cada hora, para cada moneda sin posición, compra limit en
`L = cierre anterior × (1 − 5σ)`, con σ = desviación típica de las rentabilidades horarias de los 30 días previos.
Se ejecuta si el mínimo de la hora atraviesa L (maker 0,02 %). D = cierre anterior − L.
Objetivo: limit en L + 0,5·D (media vuelta), desde la hora siguiente, válido 24 h (maker). Stop: L − D (taker 0,05 % + 0,02 %);
si en la misma vela de entrada el mínimo toca el stop, se da por perdido. Si en 24 h no pasa nada, salida a mercado.
Riesgo: 0,5 % del capital por trade (pérdida en el stop), máximo 10 posiciones. Solo largos.
*Datos:* desarrollo = 57 monedas; examen = las otras 161.
*Criba:* Sharpe ≥ 1,2, positivo en las dos mitades y PF ≥ 1,3. *Examen:* Sharpe ≥ 1,0, PF ≥ 1,3, Deflated Sharpe ≥ 0,90 (384 pruebas).

**B1 — Carry con futuros trimestrales (rendimiento fijado al entrar).**
*Origen:* el carry es la única ventaja aprobada; con perpetuos depende de que el funding siga alto. Con un futuro con vencimiento,
la diferencia de precio con el spot (la base) se cobra íntegra al vencer.
*Reglas:* BTC y ETH, 50 % del capital cada uno. Cada día a las 00:00 UTC, si no hay posición: entre los trimestrales USDT con
≥ 20 días hasta el vencimiento, el de mayor base anualizada; si es ≥ 8 %, comprar spot y vender el futuro por el mismo importe
(spot 2/3 del hueco, margen 1/3 → corto a 2x). Mantener hasta el vencimiento.
Costes: spot 0,12 % al entrar y al salir, futuro 0,07 % al entrar y 0,02 % al vencer; 0,10 % del nocional cada vez que el precio sube
un 20 % (reponer margen); penalización del 1,5 % si sube un 45 % en un día sin reponer.
*Evaluación:* no es una apuesta estadística sino un arbitraje con convergencia garantizada: se informa del rendimiento realizado por año,
del tiempo invertido y de la caída máxima a mercado. Informativo también con umbrales del 5 % y del 12 %.

**C1 — Valoración en cadena + tendencia para BTC (swing largo / posición).**
*Datos nuevos:* ratio MVRV (valor de mercado / valor realizado = precio medio al que se movió cada moneda por última vez), diario desde 2011.
*Reglas (umbrales publicados y de uso común, no ajustados):* invertido al 100 % en BTC si (precio > media de 200 días **y** MVRV < 3,5)
o si MVRV < 1,0 (valor profundo, aunque la tendencia sea bajista); en otro caso, fuera. Decisión con datos del día anterior; 0,10 % por cambio.
*Comparación:* comprar y mantener, y solo tendencia (precio > media de 200 días).
*Periodos:* 2011–2019 (referencia) y **2020–2026 (prueba)**. Se aprueba como filtro si en 2020–2026 mejora a la vez el Sharpe y la caída
máxima frente a solo tendencia. *Aviso:* hay muy pocos ciclos (3–4): la evidencia estadística es débil por construcción.

## 2. Resultados

### W1 — Pescar las mechas — `l13_salida_W1_examen.txt`, `l13_salida_W1_auditoria_completa.txt`
| | Sharpe | CAGR | DD máx. | Trades | Win rate | PF | E por trade | Años positivos |
|---|---|---|---|---|---|---|---|---|
| Diseño (57 monedas) | 1,38 | 25,4 % | 16,8 % | 4134 | 68 % | 1,26 | +0,079R | 6 de 7 |
| Examen (161 monedas) | 1,24 | 19,5 % | 12,9 % | 3123 | 68 % | 1,26 | +0,079R | 7 de 7 |

- **Desviación declarada del protocolo:** la criba exigía PF ≥ 1,30 y dio 1,26; se llevó a examen de todos modos, sin cambiar los criterios del examen.
- **Examen: NO aprobada** (PF 1,26 < 1,30; Deflated Sharpe 0,69 < 0,90).
- Réplica casi exacta entre dos conjuntos independientes (E, win rate, PF y reparto de salidas idénticos); agrupando por día, t = 8,4 y 6,5.
- Salidas: 67 % objetivo, 29 % stop, 4 % tiempo. Distancia media de la orden: 4,6–6,2 % bajo el precio. Duración mediana: 35 min.

**Auditoría de ejecución: los 7256 trades repetidos minuto a minuto**
| Cómo se ejecuta el stop | E por trade | Win rate | PF |
|---|---|---|---|
| Simulación original (1h) | +0,079R | 68 % | 1,26 |
| 1 min, al precio exacto del stop | +0,068R | 71 % | 1,25 |
| 1 min, a mitad del recorrido del minuto | +0,034R | 71 % | 1,11 |
| 1 min, al mínimo del minuto (peor caso) | 0,000R | 71 % | 1,00 |

La simulación de 1h era correcta, pero **toda la ventaja depende de cómo se ejecuten los stops**: en plena cascada, un stop a mercado
se desliza de media hasta 0,26R en el peor caso. Valor realista: entre 0 y +0,07R por trade (≈ 0 a +20 % anual con 0,5 % de riesgo).
**Estado: ventaja real pero fina; candidata a medirse en real con tamaño mínimo** (el deslizamiento real de los stops solo se conoce operando).

### B1 — Carry con futuros trimestrales — `l13_salida_B1.txt`
| Umbral de base anual | CAGR sobre el capital | DD máx. a mercado | Trades | Todos positivos | Tiempo invertido |
|---|---|---|---|---|---|
| 5 % | 4,5 % | 3,7 % | 34 | sí | 77 % |
| **8 %** | **4,0 %** | 3,7 % | 25 | **sí (25 de 25)** | 50 % |
| 12 % | 3,3 % | 3,7 % | 19 | sí | 33 % |

Por año (umbral 8 %): 2021 +7,9 %, 2022 +1,3 %, 2023 +1,2 %, 2024 +9,9 %, 2025 +3,3 %, 2026 0 %.
Base anualizada media disponible: 2021 19 %, 2022 2 %, 2023 6 %, 2024 13 %, 2025 7 %, **2026 3–4 %**.
**Funciona como arbitraje (nunca pierde al vencimiento) pero rinde poco, y no resuelve 2026:** la prima de apalancamiento está baja
en todos los instrumentos (perpetuos de Binance, de Hyperliquid y trimestrales). Útil como alternativa de menor riesgo operativo al carry con perpetuos.

### C1 — Valoración en cadena + tendencia (BTC diario desde 2010) — `l13_salida_C1.txt`
| 2020–2026 (prueba) | CAGR | Sharpe | DD máx. |
|---|---|---|---|
| Comprar y mantener | 41,7 % | 0,89 | 77 % |
| Solo tendencia (media de 200 días) | 34,5 % | 0,91 | 62 % |
| C1 tendencia + MVRV | 41,9 % | 1,00 | 68 % |

Mejora el Sharpe pero empeora la caída máxima → **no aprobada** como filtro (se exigían ambas). En 2011–2019 fue peor que solo tendencia.
El MVRV no ha superado 3,5 desde 2021 y solo bajó de 1,0 en 2022: muy pocos episodios para concluir nada.

## 3. Conclusiones
1. Ninguna de las tres queda aprobada (384 pruebas acumuladas).
2. **W1 es el mejor candidato no relacionado con el carry de todo el proyecto**: se replica con exactitud, tiene causa económica
   (dar liquidez a liquidaciones forzadas) y win rate del 68–71 %. Su rentabilidad real depende de un único dato que ningún backtest
   puede dar: el deslizamiento de los stops en una cascada.
3. La prima de carry está baja en todo el mercado en 2026; ningún instrumento la recupera.
