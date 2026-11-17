# Lección 18 — Eventos de listado en Binance

## 0. Eventos (fechas exactas, contadas antes de mirar rentabilidades) — `l18_eventos.csv`
472 monedas tienen perpetuo y spot en Binance. Primera vela de cada mercado = fecha de listado.
- **E1 — llega el spot a una moneda que ya tenía perpetuo** (≥ 3 días después): 67 eventos (2023: 1, 2024: 5, 2025: 44, 2026: 17).
- **E2 — llega el perpetuo a una moneda que ya estaba en spot** (≥ 3 días después): 255 eventos (2020–2025).
División aleatoria por moneda (semilla 2029) en desarrollo y examen: `l18_division.json`.

## 1. Pre-registro
**Hipótesis E1 — "vender la noticia":** el listado en spot libera oferta (los tenedores ya pueden vender en Binance). Corto en el perpetuo
+ largo en BTC por el mismo importe al cierre de la primera hora tras el listado en spot; salida a los 14 días; stop si la moneda sube un
50 % frente a BTC.
**Hipótesis E2 — fin de la restricción a los cortos (Miller, 1977):** cuando no se puede vender en corto, el precio refleja solo a los optimistas;
el perpetuo permite expresar opiniones bajistas. Corto en el perpetuo + largo en BTC al cierre de las primeras 24 h del perpetuo; salida a los
30 días; mismo stop.
Costes: 0,28 % ida y vuelta (dos patas) + funding real de ambas patas.
**Descriptivo:** rentabilidad acumulada frente a BTC de −7 a +60 días alrededor del evento (E1) y de +1 a +90 días (E2).
**Criterios (por evento, neto):** criba: media > 0 con t ≥ 2 y PF ≥ 1,3; examen (una vez): media > 0 con t ≥ 3 y PF ≥ 1,3.
Con pocos eventos (E1: ~33 en el examen) el umbral de t = 3 es exigente a propósito.

## 2. Resultados (criba) — `l18_salida.txt`
| | n | Media | Mediana | t | Win rate | PF | Stops | Veredicto |
|---|---|---|---|---|---|---|---|---|
| E1 corto tras listado en spot (14 d) | 33 | −5,1 % | +6,6 % | −0,87 | 61 % | 0,68 | 9 | ❌ |
| E2 corto tras listado del perpetuo (30 d) | 127 | +5,8 % | +19,6 % | +1,66 | 69 % | 1,42 | 29 | ❌ (t < 2) |
Ninguna pasa la criba: no se ejecuta el examen.

**Rentabilidad acumulada frente a BTC (mediana):**
- E1: −3 días −10 %, −1 día −8 % (cae ANTES del listado: se descuenta en el anuncio), +14 días −14 %, +60 días −37 %.
- E2: +7 días −10 %, +30 días −20 %, +90 días −33 %.

## 3. Lectura
1. **La deriva bajista tras los listados es enorme y real** (medianas de −14 % a −37 %), coherente con S1 y H10.
2. **Pero el corto está saturado:** tras el listado en spot, los cortos pagan de media un **−4,75 % de funding en 14 días**, y 9 de 33 trades
   acaban en stop por subidas violentas. Los que ganan con este evento son quienes **cobran** ese funding: es el carry inverso de la
   Lección 17, al que se llega aquí por otro camino.
3. E2 tiene una mediana muy favorable (+19,6 %, 69 % de aciertos) pero colas de −73 %: otra vez win rate alto con cola grande.
