# Lección 49 — Ideas de Gemini (segunda tanda): reglas de ejecución y fuentes poco usadas

Documento de Gemini: `docs/l49_gemini_ideas.md` (3 reglas de ejecución + 5 ideas). Filtro:

| # | Idea | Decisión |
|---|---|---|
| 1 | Entrar con órdenes límite "post-only" persiguiendo 3 min (0,02 % en vez de 0,07 %) | **No se puede validar en papel** (el riesgo es no llenarse justo en las buenas: selección adversa). Útil al pasar a real; se mide entonces |
| 2 | Stop por funding pagado en los cortos | **Esta tanda (Q5, sobre el bloque B)** |
| 3 | Reducir tamaño de los cortos si el interés abierto es enorme frente al volumen | **Esta tanda (Q6, sobre el bloque B)** |
| 4 | Consenso de interés abierto entre Binance, Bybit y OKX | **Aplazada:** OKX no publica historia larga de interés abierto |
| 5 | Funding de Hyperliquid frente al de Binance como señal direccional | **Esta tanda (HL)** |
| 6 | MSTR/COIN se adelantan a BTC tras la apertura de Wall Street | **Aplazada:** los perpetuos de acciones solo existen desde 2025 (muestra corta); la lección 23 (T2) ya vio que la relación acción–BTC no era operable |
| 7 | Resaca tras un funding extremo, con caída del interés abierto | **Esta tanda (RF)**; distinta de la lección 12 (N3), que miraba la hora **previa** al cobro |
| 8 | Polymarket como sensor de noticias | **Descartada:** requiere elegir a mano los mercados relevantes (no sistematizable sin sesgo) y solo hay liquidez desde 2024 |

La tabla de "rentabilidad anual estimada" de Gemini parte de una ventaja inventada (35 pb por operación); no se usa.

## 1. Pre-registro (subido antes de calcular ningún resultado)
**Q5 — Stop por sangrado de funding en B.** Mismo simulador que la lección 44 (B actual: corto altcoin / largo BTC en velas de 4 h,
riesgo 1 %, máximo 10 posiciones, top 30). Nueva salida, revisada al cierre de cada vela de 4 h: (a) funding neto acumulado pagado por
el par desde la entrada ≥ 0,60 % del nocional **y** ganancia latente por precio < +2,5 % → salida al cierre; (b) el último funding
cobrado de la altcoin < −0,08 % por 8 h → salida al cierre (el funding *previsto* no tiene historia; se usa el último liquidado).

**Q6 — Tamaño según interés abierto / volumen en B.** En la entrada: `R` = interés abierto en dólares / volumen de 24 h, comparado
con sus 90 días anteriores. Percentil < 75 → tamaño normal; 75–90 → mitad; > 90 → no entra. Sin datos de interés abierto (antes de
~2022 en muchas monedas): tamaño normal (se declara; el efecto se concentra en 2022–2026).

Criterio de Q5 y Q6 (el de la lección 44): Sharpe mayor que B actual en las dos mitades (2020-03 → 2022-12 y 2023-01 → 2026-10)
y caída máxima no mayor.

**HL — Funding de Hyperliquid frente a Binance.** Cada hora, top 30 con datos en los dos (Hyperliquid desde 2023-07).
ΔF = funding de Hyperliquid (horario × 8) − último funding de Binance normalizado a 8 h. Largo si ΔF ≥ +0,04 % tres horas seguidas y la
rentabilidad de 6 h < +4 %; corto si ΔF ≤ −0,04 % tres horas seguidas y la de 6 h > −4 %. Salida: |ΔF| ≤ 0,01 % o 24 h. Stop:
2,5 × ATR(24 velas de 1 h), máximo 5 %. Desarrollo 2023-07 → 2024-12, examen 2025-01 → 2026-10.
Placebo (lo que propone Gemini): la misma regla con ΔF = −funding de Binance (como si Hyperliquid estuviera en cero).

**RF — Resaca tras funding extremo.** Liquidaciones de las 00, 08 y 16 UTC, top 30. A T+1 h: corto si el funding liquidado ≤ −0,06 %,
el interés abierto cayó ≥ 2 % en esa hora y la vela de esa hora cerró en negativo; largo en el caso simétrico (≥ +0,06 %, caída de
interés abierto ≥ 2 %, vela positiva). Salida a las 4 h, o si se rompe el extremo opuesto de la vela de la hora del cobro; stop 2,5 %.
Desarrollo: hasta 2023-12; examen 2024-01 → 2026-10. Placebo: sin el filtro de caída del interés abierto.

Criterio de HL y RF: media neta por operación > 0 en desarrollo y examen, t ≥ 2,5 (agrupado por semana) en todo el periodo, y
mejor que el placebo en los dos periodos. Costes 0,07 % por lado y funding real.

## 2. Resultados — `l49_salida_B.txt`, `l49_salida_HL_RF.txt`
### Q5 y Q6 sobre el bloque B (la base coincide exactamente con la lección 44)
| Variante | 2020–22: Sharpe / caída | 2023–26: Sharpe / caída | E por operación |
|---|---|---|---|
| B actual | 1,56 / 30,4 % | 0,82 / 33,8 % | +0,147R |
| Q5 stop por sangrado de funding | 1,52 / 29,4 % | 0,87 / 27,7 % | +0,132R |
| Q6 tamaño por interés abierto / volumen | 1,25 / 30,4 % | 0,53 / 27,7 % | +0,103R |

**Q5: rechazada por poco.** Mejora el examen (Sharpe 0,87, caída de 33,8 % a 27,7 %) pero empeora un poco 2020–22 (1,52 frente a
1,56): no cumple "mejor en las dos mitades". Se mantiene B sin cambios; se anota como candidata a revisar si en real el funding
pagado por los cortos de B pesa más que en la historia.
**Q6: rechazada.** Quitar o reducir los cortos con mucho interés abierto empeora en los dos periodos: esas monedas "cargadas" son
justo las que más caen.

### HL — Funding de Hyperliquid frente a Binance
| | Desarrollo (2023-07 → 2024) | Examen (2025 → 2026-10) | Total t |
|---|---|---|---|
| Señal | −0,209 % (n 4450) | −0,297 % (n 1171) | **−3,11** |
| Placebo (solo Binance) | −0,105 % | −0,014 % | −0,54 |
**Rechazada.** Seguir a Hyperliquid pierde, y de forma significativa: cuando el funding de Hyperliquid se separa del de Binance, el
precio de Binance va en contra de esa dirección. Hyperliquid no se adelanta; su desvío se corrige. (Observación posterior, no un
hallazgo: apostar en contra tendría que probarse con datos nuevos.)

### RF — Resaca tras funding extremo
| | Desarrollo (hasta 2023) | Examen (2024 → 2026-10) | Total t |
|---|---|---|---|
| Señal (con caída del interés abierto ≥ 2 %) | −0,720 % (n 68) | −0,725 % (n 54) | −2,44 |
| Placebo (sin filtro) | −0,231 % (n 6300) | −0,298 % (n 1009) | −6,95 |
**Rechazada.** Tras un funding extremo no hay resaca contraria en las 4 horas siguientes: el precio sigue en la dirección que
causó el funding extremo, y el filtro de interés abierto lo empeora.

## 3. Conclusión
Ninguna de las cuatro pasa. Q5 es la más cercana: reduce la caída de B en 2023–26, pero no mejora en las dos mitades.
