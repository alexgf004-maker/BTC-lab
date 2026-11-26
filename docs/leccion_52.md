# Lección 52 — Patrones chartistas: hombro-cabeza-hombro, dobles techos y suelos, triángulos

Nunca se habían probado (la L39 vio velas y price action; la L26, soportes y resistencias). Se detectan por ordenador, sin mirar
el gráfico, siguiendo la idea de Lo, Mamaysky y Wang (2000): primero se marcan los giros del precio y luego se buscan las figuras
con reglas geométricas fijas.

## 1. Pre-registro (subido antes de calcular ningún resultado)
**Mercados y velas de 4 h:** cripto (top 30 mensual de perpetuos de Binance, 2020 → 2026-10) y oro + 10 pares de divisas (HistData,
2012 → 2026-10). Costes: 0,07 % por lado + funding en cripto; 0,02 % por lado en oro y divisas.
Desarrollo: cripto 2020–2022, oro/divisas 2012–2018. Examen: cripto 2023 → 2026-10, oro/divisas 2019 → 2026-10.

**Giros (zigzag sin mirar al futuro):** un máximo queda confirmado cuando el precio cae 3 × ATR(14) desde él (y al revés con los
mínimos). Solo se usan giros ya confirmados en el momento de decidir.

**Figuras** (h = altura de la figura; tolerancias relativas a h):
- **HCH (techo):** giros M1, m2, M3, m4, M5 con M3 > M1 y M3 > M5; |M1 − M5| ≤ 0,25h; |m2 − m4| ≤ 0,25h; h = M3 − (m2+m4)/2.
  Entrada corta al cierre bajo la línea de cuello (recta m2–m4). Stop en M5. Objetivo: entrada − h.
- **HCH invertido (suelo):** espejo → largo.
- **Doble techo:** M1, m2, M3 con |M1 − M3| ≤ 0,15h, h = (M1+M3)/2 − m2. Corto al cierre bajo m2. Stop en máx(M1, M3). Objetivo − h.
- **Doble suelo:** espejo → largo.
- **Triángulo ascendente:** dos máximos casi iguales (|Ma − Mb| ≤ 0,15h) y mínimos crecientes (mb > ma + 0,25h); h = techo − ma.
  Largo al cierre sobre el techo. Stop en mb. Objetivo + h.
- **Triángulo descendente:** espejo → corto.
- **Triángulo simétrico:** máximos decrecientes y mínimos crecientes (cada uno ≥ 0,25h); se opera la ruptura del último máximo
  (largo) o del último mínimo (corto). Stop en el giro opuesto. Objetivo ± h.
Común: la ruptura debe llegar en las 30 velas siguientes a la confirmación del último giro; salida por stop, objetivo o a las 60
velas. Una operación por mercado a la vez. Stop conservador si en la misma vela se tocan stop y objetivo.

**Placebo por familia** (¿aporta algo la forma de la figura?): las mismas rupturas y salidas **sin** las condiciones geométricas
(cualquier secuencia de 5 giros para HCH, de 3 para dobles, de 4 para triángulos).

**Medida:** resultado neto por operación en R (riesgo = distancia al stop), sumando todos los mercados.
**Criterio** (7 pruebas): media en R > 0 en desarrollo **y** examen, t ≥ 2,5 (agrupado por semana) en todo el periodo, y mejor
que el placebo de su familia en los dos periodos.

## 2. Resultados — `l52_salida.txt` (neto por operación, en R)
| Figura | Desarrollo | Examen | Total t | Cripto / oro y divisas | Placebo (desarrollo / examen) |
|---|---|---|---|---|---|
| HCH (techo) | +0,095R (n 221) | +0,029R (n 336) | +0,97 | +0,157R / −0,128R | +0,002R / −0,004R |
| HCH invertido | −0,069R | −0,043R | −1,14 | −0,055R / −0,052R | +0,037R / −0,005R |
| **Doble techo** | **+0,072R** (n 535) | **+0,048R** (n 721) | **+1,82** | +0,111R / −0,001R | +0,006R / +0,008R |
| Doble suelo | +0,018R | −0,036R | −0,45 | −0,014R / −0,013R | +0,015R / −0,016R |
| Triángulo ascendente | −0,022R | −0,109R | −1,39 | −0,061R / −0,090R | +0,009R / −0,019R |
| Triángulo descendente | +0,025R | −0,065R | −0,53 | +0,031R / −0,174R | ídem |
| Triángulo simétrico | −0,047R | −0,134R | −1,57 | −0,127R / −0,025R | ídem |

**Rechazadas las siete.** Ninguna llega a t ≥ 2,5.
- Lo más cercano es el **doble techo**: positivo en los dos periodos y mejor que su placebo, pero solo +0,05 a +0,07R por operación
  (t 1,82), y casi todo en cripto. El **HCH** se comporta igual, más débil.
- Las figuras **alcistas** (HCH invertido, doble suelo, triángulos ascendente y simétrico) pierden en el examen.
- En oro y divisas, ninguna figura gana.
- Observación posterior (no es un hallazgo): las figuras bajistas funcionan algo mejor que las alcistas en cripto, coherente con lo
  que ya se sabe (los cortos en debilidad, bloque B, son de lo que mejor funciona).
