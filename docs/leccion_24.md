# Lección 24 — Ampliar la reversión de los "mercados que duermen"

## 0. Datos descriptivos previos
- **El índice de los perpetuos de acciones NO se congela el fin de semana:** la prima media es ≈ 0,05 % tanto el martes como el sábado
  (TSLA, NVDA, QQQ, XAU…). La idea 3 de la lección anterior (prima frente a un índice congelado) queda descartada sin necesidad de prueba.
- El funding de fin de semana es pequeño (≈ 0,02 % por pago; máximo hasta 2 %).
- **Corrección de T1b:** la ventana de reacción (domingo 21:00 → lunes 03:00) incluye el pago de funding de las 00:00; no se había contado.

## 1. Pre-registro
Misma división de activos que la Lección 23 (semilla 2030). Precio = apertura de cada hora; se incluye el funding de la ventana de reacción.
Costes 0,14 % ida y vuelta. Criterio en todas: desarrollo y examen con resultado neto medio por periodo > 0 y t ≥ 2.
1. **T1b corregido** (con funding): corrección, no prueba nueva.
2. **Entrada más temprana en el fin de semana** (pruebas nuevas): W de viernes 21:00 hasta la entrada; R hasta el lunes 03:00.
   (a) entrada el sábado 21:00; (b) entrada el domingo 09:00. Umbral |W| ≥ 1 %.
3. **Noches entre semana, EE. UU.** (prueba nueva): W = 21:00 → 07:00 del día siguiente; R = 07:00 → 15:00 (preapertura y apertura).
   Noches de lunes a jueves. Umbral |W| ≥ 1 %. *Aviso:* entre semana los futuros del CME siguen cotizando y los creadores de mercado
   pueden cubrirse con ellos → se espera menos efecto que en el fin de semana.
4. **Materias primas, fin de semana** (prueba nueva): W = viernes 21:00 → domingo 21:00; R = domingo 21:00 → lunes 03:00. Umbral |W| ≥ 0,5 %.
5. **Asia, noches entre semana** (prueba nueva): W = 09:00 → 00:00 del día siguiente; R = 00:00 → 03:00. Umbral |W| ≥ 1 %.
6. **Festivos de EE. UU. entre semana:** solo descriptivo (muy pocos casos).

## 2. Resultados — `l24_salida.txt`, `l24_salida_pieza.txt`
| Prueba | Desarrollo: corr / neto por periodo (t) | Examen: corr / neto por periodo (t) | Veredicto |
|---|---|---|---|
| 1 T1b corregido con funding (dom 21:00 → lun 03:00) | −0,39 / +1,02 % (+3,00) | −0,45 / +0,90 % (+4,04) | ✅ (el funding no cambia nada: ±0,005 %) |
| 2a Entrada sábado 21:00 | −0,31 / +1,03 % (+2,53) | −0,39 / +1,01 % (+4,78) | ✅ |
| 2b Entrada domingo 09:00 | −0,22 / +0,86 % (+2,56) | −0,36 / +0,98 % (+4,46) | ✅ |
| 3 Noches entre semana EE. UU. | +0,06 / −0,42 % (−1,79) | +0,04 / −0,34 % (−1,48) | ❌ |
| 4 Materias primas, fin de semana | +0,18 / −0,42 % | −0,04 / +0,10 % (+0,61) | ❌ |
| 5 Noches entre semana Asia | +0,01 / +0,17 % (+0,60) | +0,13 / −0,00 % | ❌ |

**Festivos (descriptivo):** fines de semana largos por viernes festivo: correlación W–R de −0,74 (19-jun), −0,84 (3-jul), −0,85 (3-abr);
lunes festivos: −0,54 (25-may) y +0,27 (7-sep). Pocos casos.

## 3. La prueba del mecanismo
El efecto aparece **solo** cuando los creadores de mercado no pueden cubrirse:
- **Fin de semana** (futuros del CME cerrados): reversión fuerte, con cualquier hora de entrada, y más fuerte aún en los puentes por festivo.
- **Noches entre semana** (los futuros del CME cotizan casi 24 h): no hay reversión; si acaso, una ligera continuación.
- **Materias primas:** el oro y el petróleo tienen otros mercados 24/7 de referencia (PAXG, XAUT, futuros en otras plataformas) → no hay efecto.
Que el efecto esté justo donde la teoría lo predice y desaparezca donde la teoría dice que debe desaparecer es la mejor evidencia
de que es real y no casualidad.

## 4. Como pieza operable (ambos conjuntos, 29 fines de semana, con funding)
- Rendimiento medio por fin de semana: **+0,93 %** (desviación 1,49 %, t 3,38), 62 % de fines de semana positivos, peor −1,31 %.
- ≈ 24 activos por fin de semana. Por trimestre: 2026-T2 +0,42 %, T3 +1,11 %, T4 +2,14 % (el efecto crece a medida que hay más activos).
- **Capacidad** (5 % del volumen de las 6 h alrededor de la entrada): mediana 79 k$ por operación, p10 6 k$.
- El Sharpe anualizado aparente (4,5) está calculado sobre solo 29 fines de semana: **no es una estimación fiable**; lo fiable es que el efecto
  es significativo (t > 3 en el conjunto), se replica en dos conjuntos de activos y tiene un mecanismo verificado.

## 5. Estado
**Quinta pieza candidata: reversión del fin de semana en perpetuos de acciones de EE. UU.** Aprobada en las pruebas, con historia corta.
Recomendación: operarla con tamaño pequeño desde el principio, como medición en real, y ampliarla a medida que se acumulen fines de semana.
