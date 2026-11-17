# Informe final — 22 lecciones de investigación de estrategias en Binance

## 1. Método
Cada idea se probó con: reglas fijadas y commiteadas ANTES de ver resultados; costes reales (comisiones, deslizamiento, funding);
universo point-in-time con monedas deslistadas (sin sesgo de supervivencia); criba en desarrollo y examen UNA vez en datos no vistos
(monedas nuevas o periodos nuevos); corrección por pruebas múltiples (Benjamini-Hochberg y Deflated Sharpe sobre ~400 pruebas);
auditorías que detectaron y corrigieron varios errores (unidades de tiempo, precios congelados de monedas deslistadas, sesgo de
supervivencia, ejecución de stops, cobro del funding al segundo).
Datos: 923 perpetuos USDT de Binance (700 criptos tras excluir acciones y materias primas), spot, funding, interés abierto, libro de
órdenes, operaciones individuales, Hyperliquid, futuros trimestrales, índice de volatilidad implícita y datos en cadena de BTC.

## 2. Lo que funciona: la cartera de cuatro bloques (1/4 cada uno)
| Bloque | Qué hace | Por qué funciona | Cuándo gana | Evidencia |
|---|---|---|---|---|
| **A Carry de funding** | largo spot + corto perpetuo cuando el funding es alto | los especuladores pagan por apalancarse en largo | euforia | 4 conjuntos independientes; rejilla estable (Sharpe 3,7–5,1) |
| **E Carry inverso** | largo perpetuo + corto spot prestado cuando el funding es muy negativo | los cortos pagan en el miedo | pánico, mercados bajistas | examen corregido en monedas nuevas; aguanta interés del 150 %; rejilla 4,4–4,7 |
| **B Corto de altcoins débiles frente a BTC** | corto altcoin + largo BTC al romper a la baja su ratio | emisión de tokens, desbloqueos, rotación a BTC | desplomes y concentración en BTC | PF 1,38–1,71 en 4 conjuntos; examen en 482 monedas nuevas; rejilla 0,98–1,45 |
| **D Tendencia en BTC y ETH** | largo en rupturas con stop dinámico | momentum de serie temporal | subidas largas | la más débil: Sharpe esperado ≈ 0,7 |

Correlaciones mensuales entre bloques: −0,21 a +0,06. En ninguna de las seis grandes crisis (mayo 2021, LUNA, 3AC, FTX, agosto 2024,
10-oct-2025) la cartera perdió más de un 0,5 %; en 2022 (BTC −64 %) ganó un +28 %.

## 3. Expectativa realista
| | Histórico (dentro de muestra) | **Esperado (con descuento: Sharpe de cada bloque a la mitad)** |
|---|---|---|
| Rentabilidad anual | 34 % | **≈ 15 %** a 1x, ≈ 23 % a 1,5x |
| Caída máxima | 7,7 % | **≈ 11 %** a 1x; 32 % de probabilidad de una caída > 20 % en 3 años a 1,5x |
| Probabilidad de perder en un año | 0,4 % | **≈ 11–12 %** |
| Win rate | carry 72–83 %, carry inverso 40–57 %, S1 45 %, tendencia ≈ 40 % | |

## 4. Lo que NO funciona (descartado con pruebas)
Scalping en 1–5 min (4 hipótesis, ni siquiera ventaja bruta); grid trading (−32 % anual); retrocesos y reversiones (RSI, VWAP, ratio alt/BTC);
momentum relativo semanal; patrones de calendario (0 de 96); libro de órdenes y adelanto de BTC (predicen, pero 5–15 veces menos que los
costes); captura del pago de funding; corto tras pumps, mechas hacia arriba y "lotería"; tendencia bajista como cobertura; venta de
volatilidad sin cubrir; cortos tras listados (la caída existe pero el corto está saturado); modelos de aprendizaje automático (Sharpe
neto ≤ 1,4, no superan el filtro de suerte). Candidatas sin aprobar: pescar mechas en monedas consolidadas; modelo direccional con posicionamiento.

## 5. Riesgos que los datos no resuelven
1. **Disponibilidad del préstamo** para el carry inverso (límites de Binance por moneda y usuario).
2. **Riesgo de exchange:** casi todo el capital en Binance.
3. **Degradación:** las primas pueden comprimirse (el carry normal ya rinde poco desde 2025).
4. **Ejecución:** dos patas simultáneas, reequilibrio de márgenes, monedas pequeñas en S1.
5. **Régimen:** una temporada de altcoins castiga a S1 (2021: −18 %).

## 6. Reglas de operación recomendadas
- Apalancamiento de la cartera: **1x al empezar, máximo 1,5x.**
- Fases: testnet → real con capital pequeño (verificar préstamo y ejecución) → escalar si el real se parece a lo esperado.
- Parada: revisar todo si la cartera cae un 15 % desde su máximo; detener si cae un 25 %.
- El bot debe ejecutarse fuera de esta sesión (Binance bloquea la API de margen desde esta región).

## 7. Ampliación (Lecciones 23–24): primer hallazgo propio
**Reversión del fin de semana en perpetuos de acciones de EE. UU.** De viernes a domingo, los perpetuos de acciones y ETFs de EE. UU. que
cotizan 24/7 en Binance se mueven sin que los creadores de mercado puedan cubrirse (la bolsa y los futuros del CME están cerrados); ese
movimiento revierte ≈ 55 % al reabrir los futuros el domingo por la noche. Corr −0,39 / −0,45 en dos conjuntos de activos, +0,9 % por fin de
semana (t 3,4), 95 de 105 activos positivos. El efecto NO existe entre semana (cuando sí pueden cubrirse) → mecanismo confirmado.
Límites: 29 fines de semana de historia y capacidad moderada. **Candidata a quinta pieza, a operar en pequeño.**
La prima del perpetuo frente al índice (Lección 23) mejora el momento de entrada del carry inverso; no es una pieza aparte.
