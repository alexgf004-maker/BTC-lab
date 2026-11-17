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
