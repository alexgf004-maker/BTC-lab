# Lección 8 — Torneo de hipótesis: siete fuentes de ventaja distintas

## 0. Método
Probar muchas ideas sube la probabilidad de encontrar una "ganadora" por azar. Por eso:
1. Cada hipótesis tiene **una causa económica** y **una especificación fijada aquí**, antes de ver datos.
2. **Criba** en el conjunto de desarrollo (57 activos, universo point-in-time top 20): solo pasa lo que tenga
   Sharpe ≥ 1,2 (t ≈ 3 en 6,6 años; umbral de Harvey, Liu y Zhu, 2016), Sharpe > 0 en las dos mitades y PF ≥ 1,3, todo neto de costes.
3. **Examen** de las que pasen en símbolos NUEVOS (`data/universo_examen2.txt`, nunca usados), una sola vez:
   Sharpe ≥ 0,5, PF ≥ 1,3 y Deflated Sharpe ≥ 0,90 con todas las pruebas acumuladas (342 + las de esta lección).

Costes: taker 0,05 % + slippage 0,02 % por lado y por pata (0,14 % ida y vuelta por pata), salvo que se indique. Funding real.

## 1. Hipótesis pre-registradas (9 pruebas)

**H1 — Carry transversal solo con perpetuos (neutral al mercado, siempre invertido).**
Causa: el funding mide quién paga por apalancarse; cobrar a los más saturados y pagar a los menos.
Cada rebalanceo, entre los miembros del universo: corto en el quintil de mayor funding medio de 7 días, largo en el quintil de
menor; 50 % del capital por lado. Rentabilidad = precio + funding − costes de rotación. H1a: rebalanceo diario. H1b: semanal (lunes).

**H2 — Carry spot-perpetuo con umbral bajo** (para que no pase años parado).
Igual que la Lección 7 (2x, 4 huecos), pero entra con funding medio de 3 días > 0,015 %/8h y sale con < 0,005 %.

**H3 — Reversión tras cascadas de liquidaciones (1h).**
Causa: las liquidaciones forzadas empujan el precio más allá de su valor y los proveedores de liquidez cobran por absorberlas.
H3a (largo): vela 1h con rentabilidad < −4σ (σ = desviación de 7 días) y volumen > 3× la media de 7 días → comprar al cierre,
vender 24 h después. H3b (corto): el espejo tras subidas > +4σ. Una posición por activo; 10 % del capital por trade.

**H4 — Estacionalidad intradía de BTC.**
Causa documentada: rentabilidades positivas concentradas en 21:00–23:00 UTC (cierre de EE. UU., antes de Asia).
Largo en BTC de 21:00 a 23:00 UTC todos los días. Costes: entrada maker + salida taker (0,09 %).

**H6 — Reversión del ratio altcoin/BTC (neutral al mercado).**
Causa: las altcoins líquidas se mueven con BTC; las desviaciones bruscas del ratio tienden a corregirse.
En 4h, z = (log(alt/BTC) − media de 30 días) / desviación de 30 días. Si z < −2: largo alt + corto BTC; si z > +2: al revés.
Salida: z cruza 0, |z| > 4 (stop) o 30 días. 10 % del capital por pata. Costes: 0,28 % (dos patas).

**H9 — Reversión transversal diaria.**
Causa: sobrerreacción de corto plazo. Cada día: largo en el quintil con peor rentabilidad de ayer, corto en el mejor; 50 % por lado.

**H10 — Corto en nuevos listados, cubierto con BTC.**
Causa: los listados nuevos salen con valoraciones infladas y oferta bloqueada que se va liberando; caen frente al mercado.
Para cada perpetuo listado después de julio de 2020: 7 días tras el listado, corto en el activo + largo en BTC por el mismo importe
(5 % del capital). Salida a los 60 días o si el precio se duplica (stop). Funding real de ambas patas. Costes: 0,28 %.

(H5, H7 y H8 —adelanto/retraso, flujo de órdenes y base— se descartan de antemano: exigen datos de mayor frecuencia o su señal ya la recoge H1.)
