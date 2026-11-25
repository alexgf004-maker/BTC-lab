# Lección 41 — Mapas de liquidaciones: ¿el precio va a buscar las zonas donde se liquidaría más gente?

## 0. Idea
Los "mapas de calor de liquidaciones" (Coinglass, Hyblock…) estiman dónde están los precios de liquidación de las posiciones abiertas.
Muchos traders los usan como **imán**: "el precio irá a por la zona con más liquidaciones". No son datos reales sino estimaciones
construidas con el interés abierto y supuestos de apalancamiento. Aquí se construye el mismo tipo de mapa y se prueba si predice algo.

## 1. Construcción del mapa (hora a hora, sin mirar el futuro)
Datos: interés abierto horario de Binance (métricas de data.binance.vision, desde 2020-09) y velas de 1 h.
- Si el interés abierto sube ΔOI en la hora t, se abren ΔOI contratos al precio de cierre p (cada contrato tiene un largo y un corto).
  Reparto de apalancamientos: 10x 40 %, 25x 30 %, 50x 20 %, 100x 10 %. Liquidación del largo en p·(1 − 1/L); del corto en p·(1 + 1/L).
- Si el interés abierto baja, todas las posiciones del mapa se reducen en la misma proporción.
- Si el mínimo de la hora alcanza un nivel de liquidación de largos (o el máximo uno de cortos), esa masa desaparece (liquidada).
- Rejilla logarítmica de 0,25 %.

## 2. Pre-registro (antes de calcular resultados). Medición diaria a las 00:00 UTC.
**LM1 — Desequilibrio:** S = liquidaciones de cortos entre el precio y +5 %; L = liquidaciones de largos entre −5 % y el precio;
I = (S − L)/(S + L). Hipótesis "imán": el precio tiende a ir hacia el lado con más masa → rentabilidad de las 24 h siguientes con el signo de I.
Medida: correlación de rangos entre I y la rentabilidad de 24 h. Estrategia: si |I| ≥ 0,5, posición en el sentido de I durante 24 h;
coste 0,14 % por operación.
**LM2 — ¿Qué zona se toca antes?** Mayor acumulación de cortos entre el precio y +10 % (a distancia du) y de largos entre −10 % y el
precio (a distancia dd). Se mira cuál se alcanza primero en los 7 días siguientes. Sin imán, la probabilidad de tocar antes la de arriba
es dd/(du + dd) (paseo aleatorio). Se mide el exceso: (toca primero la zona MÁS GRANDE) − (probabilidad esperada por distancia).
**Activos:** BTC, ETH y las 20 más líquidas de cada mes con métricas disponibles. **Desarrollo 2020-09 → 2023-06; examen 2023-07 → 2026-10.**
**Criterio:** LM1: estrategia con esperanza neta > 0 y t ≥ 3 (por día) en el examen y positiva en desarrollo. LM2: exceso > 0 con z ≥ 3
en los dos periodos. Pruebas nuevas: 2.
