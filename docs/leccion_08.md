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

## 2. Criba (desarrollo, 57 activos) — `l08_salida_criba.txt`

| Hipótesis | Sharpe total | 2020-23 | 2024-26 | CAGR | DD máx. | Win rate | PF | Veredicto |
|---|---|---|---|---|---|---|---|---|
| H1a carry transversal diario | 0,54 | 0,63 | 0,41 | 12,6 % | 53,8 % | 51 % | 1,09 | ❌ |
| H1b carry transversal semanal | 0,35 | 0,29 | 0,49 | 6,3 % | 66,5 % | 50 % | 1,06 | ❌ |
| **H2 carry spot-perpetuo, umbral bajo** | **5,08** | 6,11 | 3,98 | 15,6 % | 1,0 % | 71 % | 111 | ✅ |
| H3a cascada, largo | 0,95 | 1,42 | 0,33 | 33,7 % | 42,6 % | 55 % | 1,45 | ❌ (se debilita) |
| H3b cascada, corto | −1,02 | −0,68 | −1,69 | −30,6 % | 91,5 % | 49 % | 0,74 | ❌ |
| H4 estacionalidad BTC 21-23h | −0,35 | −0,19 | −0,68 | −6,7 % | 59,9 % | 46 % | 0,94 | ❌ |
| H6 ratio alt/BTC | −1,40 | −2,01 | −0,21 | −48,2 % | 98,9 % | **58 %** | 0,73 | ❌ |
| H9 reversión diaria | −1,75 | −1,96 | −1,42 | −49,2 % | 99,1 % | 46 % | 0,76 | ❌ |
| H10 corto en nuevos listados | 0,63 | 0,83 | — | 5,3 % | 8,6 % | 67 % | 2,04 | ❌ (36 trades, t = 1,8) |

Lecturas:
- **H6 es la lección del win rate:** acierta el 58 % de las veces y pierde un 48 % al año. Las pocas veces que el ratio no
  revierte (una altcoin que se hunde frente a BTC) borran todas las ganancias pequeñas.
- **En cripto, a escala de horas y días, domina la continuación, no la reversión:** H3b, H6 y H9 pierden con fuerza.
  Sus inversas tampoco son operables (H9 inversa no cubre costes; "comprar tras cualquier movimiento extremo" es beta alcista).
- **H1:** cobrar funding solo con perpetuos expone al precio de los activos más calientes; el riesgo anula el carry.
  La cobertura con spot (H2/S3) es lo que hace que funcione.
- **H10:** efecto grande (+20 % por trade) pero 10 de 36 trades acaban en stop (−95 % el peor) y no es significativo.
- H2 no resuelve la inactividad: ocupación del 1 % en 2025 y 0 % en 2026. El funding está bajo en todo el mercado.

## 3. Examen (129 símbolos nuevos, top 10 point-in-time, una vez) — `l08_salida_examen.txt`
| | Sharpe | 2020-23 | 2024-26 | CAGR | DD máx. | Win rate | PF | Deflated Sharpe |
|---|---|---|---|---|---|---|---|---|
| **H2 carry, umbral bajo** | **4,24** | 5,32 | 2,28 | 10,4 % | 2,3 % | **80 %** | 37,8 | **1,00 ✅** |

Episodios por año: 2020: 8, 2021: 12, 2022: 2, 2023: 14, 2024: 8, 2025: 4, 2026: 1. Peor episodio: −10,6 % sobre el nocional.

## 4. Conclusiones
1. **El carry de funding queda confirmado por tercera vez** en un conjunto independiente (57 → 32 → 129 activos).
   Es la única ventaja que ha sobrevivido a 351 pruebas.
2. **Ninguna de las otras 8 hipótesis supera la criba.** No hay "estrategia brutal" escondida en velas horarias públicas:
   lo que funciona es cobrar una prima con causa económica (carry) y, con menos fuerza, la tendencia en BTC y ETH.
3. Límite estructural: en 2025-26 el funding de Binance es bajo y el carry apenas opera.
4. Vías que quedan (necesitan datos que aún no tenemos): carry entre exchanges (el funding difiere entre Binance, Bybit,
   OKX y Hyperliquid), interés abierto y liquidaciones como señal, y microestructura (libro de órdenes).
