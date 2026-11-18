# Lección 38 — Validar la estrategia ICT del Nasdaq (tomas de liquidez + ventanas macro + IFVG)

## 0. La afirmación
Publicación en un grupo de trading: 1 000 operaciones en futuros micro del Nasdaq (MNQ) de 2021 a 2025, con un simulador manual
(FX Replay). Acierto 69,6 %, "ratios 1:1", +276 %, 55 de 57 meses positivos. Reglas: **tomas de liquidez de Asia, Londres y
preapertura; ventanas macro (ICT); gatillo IFVG (ICT); objetivo 1:1.**
Incoherencia en sus propios datos: ganancia media 0,71 % frente a pérdida media 0,34 % (2:1, no 1:1). Con 70 % de acierto y 2:1, la
esperanza sería +0,39 % por operación: extraordinaria.

## 1. Definiciones (versión estándar de los conceptos ICT), hora de Nueva York (con horario de verano)
- **Liquidez de sesión:** máximo y mínimo de Asia (20:00–00:00 del día anterior), Londres (02:00–05:00) y preapertura (08:00–09:30).
- **Toma de liquidez:** después de las 09:30, el precio supera uno de esos máximos (toma de liquidez compradora → se busca corto) o pierde uno
  de esos mínimos (→ se busca largo). Cuenta la última toma antes del gatillo.
- **Ventanas macro (ICT):** 09:50–10:10 y 10:50–11:10.
- **FVG (fair value gap):** tres velas de 1 min en las que el mínimo de la tercera queda por encima del máximo de la primera (FVG alcista)
  o el máximo de la tercera por debajo del mínimo de la primera (FVG bajista).
- **IFVG (FVG invertido), gatillo:** tras una toma de liquidez compradora, un FVG alcista formado desde las 09:30 queda **invertido** cuando una
  vela de 1 min cierra por debajo de su borde inferior → corto al cierre de esa vela. Simétrico para largos (FVG bajista que se cierra por encima).

## 2. Pre-registro (antes de descargar los datos)
**Z1 — Modelo ICT 1:1:** gatillo IFVG dentro de una ventana macro, con toma de liquidez previa en la dirección contraria.
Stop: el extremo de la toma (máximo desde las 09:30 para cortos; mínimo para largos). Objetivo: a la misma distancia (1:1).
Máximo una operación por ventana; cierre forzoso a las 16:00. Riesgo mínimo: 5 puntos del índice.
**Z2 — Igual con objetivo 2:1** (lo que muestran sus estadísticas de ganancia y pérdida media).
**Costes (MNQ):** comisión y deslizamiento ≈ 0,75 puntos por operación completa (1 tick de deslizamiento en la entrada y en el stop + comisión).
Si en la misma vela de 1 min se tocan stop y objetivo → pérdida.
**Datos:** Nasdaq 100 (NSXUSD) en velas de 1 minuto de HistData, 2012 → 2026-10 (sigue al futuro con una diferencia de base constante dentro del día).
**Periodos:** desarrollo 2012–2019; **examen 2020 → 2026-10** (incluye su periodo 2021–2025). Una vez.
**Criterio:** esperanza neta > 0 con t ≥ 3 (agrupando por día) en el examen y positiva en desarrollo. Se informa el acierto y el resultado
de 2021–2025 por separado para compararlo con la publicación. Pruebas nuevas: 2.

## 3. Resultados — `l38_salida.txt` (Nasdaq 100, 4,9 millones de velas de 1 min, ≈ 5 000 operaciones)
| | Desarrollo 2012–2019 | **Examen 2020–2026** | **Periodo de la publicación 2021–2025** |
|---|---|---|---|
| Z1 ICT 1:1 | −0,132R / 47 % acierto | **−0,029R (t −1,4) / 50 %** | −0,014R / **51 %** |
| Z2 ICT 2:1 | −0,131R / 34 % | **+0,003R (t 0,6) / 36 %** | +0,018R / **37 %** |
**NO aprobada.** Con las reglas escritas, el modelo acierta el **50–51 % con 1:1** (no el 70 %) y el **37 % con 2:1**: exactamente lo que
daría el azar. Sin costes rondaría cero. Ningún año pasa de +0,07R.

## 4. Qué nos dice
1. **El 70 % de acierto no aparece** cuando las reglas se aplican igual a todas las situaciones. La diferencia entre el 51 % y el 70 %
   es, muy probablemente, el efecto del simulador manual: al repasar el gráfico vela a vela, la persona decide qué "toma de liquidez" o qué
   "IFVG" cuenta, y sin querer elige las que funcionaron (sesgo retrospectivo). Por eso "el reto es ejecutarla en vivo": en vivo no se puede elegir.
2. Los conceptos ICT (tomas de liquidez, FVG, IFVG, ventanas macro) no dan ventaja en el Nasdaq de 2012 a 2026, igual que CRT + CISD en
   cripto y en forex (Lecciones 33 y 35).
3. Limitación: es una versión estándar de esos conceptos; el autor podría usar variantes. Pero si su ventaja dependiera de detalles no
   escritos, no sería una regla verificable sino criterio personal.
