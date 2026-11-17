# Lección 19 — Barrido sistemático de patrones de calendario

## 1. Pre-registro
**Series:** (a) BTC; (b) cesta a partes iguales del universo point-in-time top 30 (absoluta); (c) la misma cesta menos BTC (relativa).
**Desarrollo:** las 218 monedas antiguas (y BTC 2020-01 → 2023-06). **Examen:** las 482 criptos nuevas (y BTC 2023-07 → 2026-10).
**Efectos:** rentabilidad de cada hora del día (24), de cada día de la semana (7) y de los 3 primeros días del mes frente al resto (1)
→ 32 efectos × 3 series = **96 pruebas**. Estadístico: media de la rentabilidad del efecto en cada ocurrencia y t (las ocurrencias son
independientes: un valor por día o por semana). **Benjamini-Hochberg al 5 %** sobre las 96.
**Para ser operable:** significativo en desarrollo, mismo signo y significativo (p < 0,05) en el examen, y media mayor que el coste de
entrar y salir (BTC: 0,09 % con entrada limit; cesta: 0,14 %).

## 2. Resultados — `l19_salida.txt`, `l19_calendario.csv`
**0 de 96 efectos son significativos en desarrollo** tras la corrección; ninguno se replica ni cubre costes.
Los más fuertes (sin superar la corrección):
| Serie | Efecto | Media desarrollo (t) | Media examen (t) |
|---|---|---|---|
| cesta − BTC | hora 23 UTC | +0,025 % (+2,4) | +0,044 % (+3,4) |
| cesta − BTC | hora 05 UTC | +0,023 % (+2,1) | +0,038 % (+2,6) |
| cesta − BTC | domingo | −0,20 % (−1,8) | −0,49 % (−3,0) |
| BTC | hora 08 UTC | +0,009 % (+0,4) | +0,033 % (+2,7) |
Los efectos horarios son de 0,02–0,04 %, entre 3 y 7 veces menores que el coste de entrar y salir.

## 3. Conclusión
**No hay patrones de calendario operables** en cripto con datos horarios: el mercado es eficiente en esta dimensión.
Única observación a vigilar (no operable según las reglas): las altcoins tienden a rendir peor que BTC los domingos.
