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

## 1b. Pre-registro adicional (escrito tras ver O2, antes de calcular O4–O5)
O2 usa opciones de 7 días; la prima medida por el DVOL es a 30 días, así que el plazo podría importar.
**O4 — Iron condor mensual (≈ 28 días):** entrada el viernes situado 28 días antes de cada vencimiento mensual (último viernes del mes),
con las opciones de ese vencimiento; σ√(28/365); mismas reglas de strikes (1σ/2σ), ejecución, comisiones y liquidación que O2. Una posición a la vez.
**O5 — Spread de put vendido mensual (≈ 28 días):** solo la pata de put de O4 (vender put a −1σ, comprar put a −2σ).
Mismos periodos y criterio (con t ≥ 2 por el menor número de operaciones). BTC y ETH. Pruebas nuevas: 4.

## 2. Resultados — `l30_salida.txt`, `l30_salida_mensual.txt`
**O1 — La prima de volatilidad existe, pero se ha encogido:**
| | Implícita (DVOL) | Realizada 30 d siguientes | Prima media / mediana | Días con implícita > realizada |
|---|---|---|---|---|
| BTC 2021-03→2022 | 81,5 % | 66,9 % | +14,6 / +18,7 pts | 79 % |
| BTC 2023→2026 | 49,5 % | 44,7 % | +4,8 / +6,6 pts | 72 % |
| ETH 2021-03→2022 | 99,4 % | 88,7 % | +10,7 / +20,5 pts | 71 % |
| ETH 2023→2026 | 61,7 % | 59,2 % | +2,5 / +4,4 pts | 64 % |

**O2–O5 — Venderla con riesgo limitado: todas pierden** (E[R] = beneficio medio por operación / pérdida máxima)
| Estructura | BTC desarrollo | BTC examen | ETH desarrollo | ETH examen | Ganadoras |
|---|---|---|---|---|---|
| O2 iron condor semanal 1σ/2σ | −0,051 (t −2,1) | **−0,067 (t −2,7)** | −0,046 | **−0,080 (t −3,2)** | 73–78 % |
| O3 = O2 solo con implícita > realizada | −0,056 | −0,126 | −0,039 | −0,092 | 72–78 % |
| O4 iron condor mensual | −0,087 | −0,081 | −0,132 | −0,056 | 61–73 % |
| O5 spread de put mensual | −0,050 | −0,038 | −0,034 | −0,029 | 82–86 % |
| Robustez semanal 0,75σ/1,5σ y 1,25σ/2,5σ | −0,024 / −0,045 | −0,080 / −0,057 | −0,110 / −0,045 | −0,083 / −0,060 | |
Comprobación: **a precio marcado, sin diferencial ni comisiones**, el condor semanal también queda en −0,02/−0,03 (BTC) y −0,02/−0,05 (ETH).

## 3. Por qué la prima existe y aun así no se puede cobrar así
1. **La prima está en las colas, y el seguro las devuelve.** El DVOL pondera mucho las opciones muy fuera del dinero (como el VIX).
   Gran parte de la prima es el precio del seguro contra desplomes y subidas violentas. El iron condor **compra** ese seguro (las alas),
   así que devuelve justo la parte cara. Las opciones de los strikes vendidos (a 1σ) están, en promedio, **bien valoradas**.
2. **Gana el 75–86 % de las veces y aun así pierde.** El crédito es solo un 11–14 % del riesgo. Hace falta acertar más del 88 % para
   compensar, y cada pérdida suele ser completa (peor caso −1,0).
3. **Los costes de cuatro patas** (diferencial y comisión en cada una) se comen lo poco que queda.
4. Vender la cola sin seguro sí cobraría la prima, pero eso es venta de volatilidad sin cubrir, ya rechazada en la Lección 14 por sus caídas.

**Veredicto: opciones descartadas** como fuente de rentabilidad con riesgo limitado, para un particular con costes de taker.
Coherente con la regla general: la prima existe porque paga por un riesgo de cola real; si te cubres de ese riesgo, desaparece.
