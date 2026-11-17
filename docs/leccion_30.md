# Lección 30 — Opciones: cobrar la prima de volatilidad con riesgo limitado

## 0. Por qué
En la Lección 14 medimos que la volatilidad implícita de BTC suele estar por encima de la realizada (prima de volatilidad), pero vender
volatilidad **sin cubrir** se rechazó: las colas de cripto la destrozan. Con opciones se puede vender esa prima **con la pérdida máxima
fijada de antemano** (iron condor: vender una call y una put fuera del dinero y comprar otras más lejanas como seguro).
Binance tiene opciones europeas de BTC y ETH liquidadas en USDT, pero no publica su historia; se usa **Deribit** (el mercado de referencia,
>85 % del volumen mundial), con precios reales de cada operación (precio marcado y volatilidad implícita) y su precio oficial de liquidación.

## 1. Pre-registro (antes de descargar ni calcular resultados)
**O1 — Medición de la prima de volatilidad:** DVOL (índice de volatilidad implícita a 30 días de Deribit, desde 2021-03) frente a la
volatilidad realizada de los 30 días siguientes (velas 1h de BTCUSDT). Media, mediana y % de días con implícita > realizada.

**O2 — Iron condor semanal (BTC).** Cada viernes, en la ventana 08:10–09:10 UTC (justo tras el vencimiento semanal de las 08:00), con las
opciones que vencen el viernes siguiente (7 días):
- σ = mediana de la volatilidad implícita de las operaciones con strike a menos del 3 % del índice; T = 7/365.
- Cortas: call en S·e^{+1·σ√T} y put en S·e^{−1·σ√T}; largas (seguro): call en S·e^{+2·σ√T} y put en S·e^{−2·σ√T}.
  En cada caso, el strike negociado en la ventana más cercano al objetivo (alas siempre más lejos que las cortas).
- Precio de cada pata: mediana del precio marcado de sus operaciones en la ventana (en BTC × índice → USD, como en Binance, que liquida en USDT).
- **Ejecución conservadora:** vender a precio marcado − medio diferencial y comprar a + medio diferencial, con medio diferencial =
  max(0,00025 BTC, 4 % del precio). Comisión 0,0003 BTC por pata (tope 12,5 % del precio) + liquidación 0,00015 BTC si vence dentro del dinero.
- Liquidación al vencimiento con el precio oficial de entrega de Deribit. Sin gestión intermedia (se mantiene hasta el vencimiento).
- **Capital:** la pérdida máxima (anchura del ala mayor − crédito neto). Resultado por operación = beneficio / pérdida máxima.
  Curva con un 10 % del capital del bloque en riesgo cada semana.
**O2-ETH:** lo mismo en ETH (réplica independiente).
**O3 — Filtro de prima:** O2 solo las semanas en que σ (implícita ATM) > volatilidad realizada de los 30 días previos.
**Robustez (informativa, no se elige):** cortas/alas a (0,75σ, 1,5σ) y (1,25σ, 2,5σ).
**Periodos:** desarrollo 2019-01 → 2022-12; **examen 2023-01 → 2026-11** (una vez).
**Criterio:** esperanza por operación > 0 con t ≥ 2,5 en el examen **y** positiva en desarrollo; peor año del examen > −30 % del capital
del bloque (10 % en riesgo por semana). Pruebas nuevas: 3 (O2 BTC, O2 ETH, O3).
