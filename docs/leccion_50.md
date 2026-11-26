# Lección 50 — Ideas de Gemini (tercera tanda): continuación, flujos forzados y mercados cerrados

Gemini recibió los resultados de las lecciones 48–49 y propuso 6 ideas alineadas con lo que funciona (`docs/l50_gemini_ideas.md`).

| # | Idea | Decisión |
|---|---|---|
| 1 | Reversión del fin de semana en oro tokenizado (PAXG) | **Esta tanda (P).** La lección 23 solo vio perpetuos de oro recientes (20–45 fines de semana); PAXG spot da ~320 desde 2020 |
| 2 | Fuga de TVL real (DefiLlama) → continuación bajista | **Esta tanda (T)** |
| 3 | Skew de 25 delta de Deribit extremo → continuación bajista | Aplazada: reconstruir la superficie de volatilidad desde 2020 es un proyecto en sí |
| 4 | Líderes congestionados que pierden soporte → corto | **Esta tanda (W)** |
| 5 | Ruptura bajista con ventas lideradas por spot → corto | **Esta tanda (S)** |
| 6 | Interés abierto en contratos inversos (Coin-M) como fragilidad | Aplazada: decenas de miles de archivos diarios |

## 1. Pre-registro (subido antes de descargar los datos nuevos)
Comunes: costes 0,07 % por lado en perpetuos (0,12 % en spot), funding real; t agrupado por semana; una posición por moneda a la vez.
**Criterio (las 4):** media neta por operación > 0 en desarrollo **y** examen, t ≥ 2,5 en todo el periodo, y mejor que el placebo
en los dos periodos.

**P — Fin de semana en PAXG (spot, 2020-09 → 2026-10).** R = precio dom 20:00 / vie 20:00 − 1 (cierres horarios UTC); σ = desviación
de los 20 fines de semana anteriores. Si |R| ≥ máx(0,8 %, 1,5σ): entrada dom 20:00 en contra del movimiento. Salida lun 14:00 UTC, o
antes si vuelve al precio del viernes (objetivo); stop 1,5 × |R| (máximo 2,5 %). Los cortos pagan un préstamo de margen del 10 % anual.
Placebo: la misma regla de martes 20:00 a jueves 20:00 (oro abierto), saliendo el viernes 14:00.
Desarrollo 2020-09 → 2022; examen 2023 → 2026-10.

**T — Fuga de TVL real.** Top 30 mensual con mapeo fijo a DefiLlama (fijado aquí, antes de descargar): cadenas ETH→Ethereum,
SOL→Solana, BNB→BSC, AVAX→Avalanche, TRX→Tron, MATIC/POL→Polygon, ADA→Cardano, NEAR→Near, FTM/S→Fantom/Sonic, SUI→Sui,
APT→Aptos, ARB→Arbitrum, OP→Optimism, TON→TON, INJ→Injective, SEI→Sei, ALGO→Algorand, KAVA→Kava, LUNA→Terra; protocolos UNI→uniswap,
AAVE→aave, CRV→curve-dex, MKR→makerdao, LDO→lido, COMP→compound-finance, SNX→synthetix, CAKE→pancakeswap, SUSHI→sushi,
DYDX→dydx, GMX→gmx, PENDLE→pendle, JUP→jupiter, RAY→raydium. Lo que no se pueda descargar se omite (se declara).
A las 00:00 UTC, con el TVL y el cierre del día anterior: ΔTVLreal = ln(TVL/P) − ln(TVL/P hace 14 días). Corto si ΔTVLreal ≤ −10 %,
cierre < media de 30 días y funding de 7 días > −0,05 %. Salida: ΔTVLreal ≥ 0, cierre > media de 30 días, o 21 días. Stop: entrada +
3 ATR(14 días) (máximo +12 %), que baja con el mínimo desde la entrada. Placebo: la misma regla de precio con ΔTVLreal ≥ 0.
Desarrollo 2020–2022; examen 2023 → 2026-10.

**W — Líderes congestionados.** A las 00:00 UTC, en el top 30: lista de vigilancia si rentabilidad de 14 días en el tercio superior y
> +10 %, interés abierto **en monedas** +25 % en 14 días y funding medio de 7 días > +0,015 %. Cada hora, corto si una moneda de la
lista cierra bajo su VWAP de 7 días y bajo el mínimo de las 48 h anteriores. Salida: interés abierto en monedas −20 % desde la entrada,
o 7 días. Stop: entrada + 3 ATR (24 velas de 1 h), que baja con el mínimo desde la entrada a 2,5 ATR.
Placebo: la misma ruptura en monedas del tercio superior con interés abierto en monedas ≤ 0 % en 14 días y funding ≤ +0,01 %.
El interés abierto existe desde ~2022 en la mayoría: desarrollo hasta 2023-12, examen 2024 → 2026-10.

**S — Ruptura liderada por spot.** Top 30 con par spot USDT. Cada hora, cuota spot = volumen spot 24 h / (spot + perpetuo 24 h), z frente
a los 60 días anteriores. Corto si el cierre < mínimo de los 7 días anteriores, z ≥ 1,5 y funding medio de 24 h > −0,05 %. Salida: z ≤ 0
doce horas seguidas, o 5 días. Stop: entrada + 3 ATR (24 velas de 1 h), que baja con el mínimo desde la entrada a 2,5 ATR. Se excluye
BTCUSDT de 2022-07 a 2023-03 (spot sin comisiones). Placebo: la misma ruptura con z ≤ −1 (caída liderada por perpetuos).
Desarrollo 2020–2022; examen 2023 → 2026-10.

## 2. Resultados — `l50_salida_P_T.txt`, `l50_salida_W.txt`, `l50_salida_S.txt`
Correcciones antes de leer resultados: interés abierto con horas duplicadas (se toma el último valor) y una descarga spot
interrumpida por el proxy; S se repitió con las 227 monedas con par spot (la salida provisional con 51 se descarta).

| Idea | Desarrollo | Examen | Total t | Placebo (desarrollo / examen) | ¿Pasa? |
|---|---|---|---|---|---|
| P · Fin de semana en PAXG | −0,49 % (n 5) | +0,27 % (n 10) | +0,03 | −0,23 % / −0,29 % | No (casi nunca se activa) |
| T · Fuga de TVL real | **+1,10 %** (n 167) | **+0,24 %** (n 167) | +1,14 | −0,31 % / −0,13 % | No (t insuficiente) |
| W · Líderes congestionados | −2,08 % (n 15) | +0,47 % (n 16) | −0,66 | −0,53 % / −0,14 % | No |
| S · Ruptura liderada por spot | −1,23 % (n 231) | −0,76 % (n 378) | **−3,50** | −0,04 % / −0,04 % | No (pierde) |

- **P:** el oro tokenizado rara vez se mueve ≥ 0,8 % en un fin de semana (15 casos en 6 años); imposible de validar.
- **T:** es la primera idea de Gemini con el signo correcto en los dos periodos y mejor que su placebo, pero el efecto es débil
  (t 1,14 frente a 2,5 exigido). Candidata a seguimiento en papel, no a la cartera.
- **W:** la combinación de condiciones casi nunca se da (31 casos) y el resultado no es estable.
- **S:** al revés de lo previsto y con fuerza. Cuando una ruptura bajista llega con una cuota anormal de volumen spot, el precio
  **rebota**: las ventas en spot de ese momento son capitulación, no distribución. (Observación posterior; no se opera sin datos nuevos.)

## 3. Conclusión
Tercera tanda: 0 de 4 aprobadas, pero mejor orientada que las anteriores (una con el signo correcto en los dos periodos).
