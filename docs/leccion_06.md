# Lección 6 — Universo realista y nuevas fuentes de ventaja (carry y momentum relativo)

## 0. Por qué esta lección
La Lección 5 demostró que el universo elegido "a dedo" (los grandes de hoy) infla los resultados por
**sesgo de supervivencia**. Aquí se corrige la base y se prueban dos fuentes de ventaja distintas de la tendencia,
elegidas por su potencial de **win rate y PF**.

Literatura:
- **Liu, Tsyvinski y Wu (2022), "Common Risk Factors in Cryptocurrency", Journal of Finance 77(2):**
  mercado, tamaño y **momentum** explican los rendimientos cripto; el momentum semanal (largo-corto) es más fuerte con
  3 semanas de historia y en monedas grandes. Rendimientos BRUTOS; los autores avisan de costes de rotación.
- **Carry de funding (cash-and-carry):** largo en spot + corto en el perpetuo = posición neutral al precio que cobra el
  funding. El funding fue positivo ~71 % del tiempo en 9 años (BitMEX). Riesgos: rachas de funding negativo,
  diferencias de base, necesita el doble de capital, el funding se ha comprimido desde la era de los ETF.

## 1. Universo y división (pre-registro)
- 89 perpetuos USDT (`data/universo.txt`), **incluidos deslistados**.
- **Point-in-time:** el día 1 de cada mes, de los activos con ≥ 60 días de historia, se eligen los **K más líquidos**
  por volumen (USDT) de los 30 días anteriores. Solo esos pueden abrir posiciones ese mes (las abiertas siguen).
- **División aleatoria por activo (semilla 2026)** de los 64 activos nunca usados: `l06_division_activos.json`.
  Desarrollo = 25 ya vistos + 32 nuevos (K = 20). **Examen = 32 nuevos nunca tocados** (K = 10), UNA vez al final.

## 2. Estrategias (parámetros fijados de antemano)
**S1 Tendencia (referencia realista):** reglas de la Lección 3 (ruptura de 20 días en 4h, chandelier m = 5, filtro EMA50 diaria),
1 % de riesgo, máximo 10 posiciones, sobre el universo point-in-time.

**S2 Momentum relativo (Liu et al.):** cada lunes a las 00:00 UTC, se ordena el universo del mes por la rentabilidad de las 3 semanas anteriores.
- S2a: largo en el quintil superior, a partes iguales.
- S2b: largo en el quintil superior y corto en el inferior, neutral en dólares.
Exposición bruta 1x del capital. Costes: taker 0,05 % + slippage 0,02 % sobre lo que se rota; funding real.
Control de S2a: el universo entero a partes iguales.

**S3 Carry de funding (neutral al mercado):** para cada activo del universo con mercado spot:
- Entrar si el funding medio de los últimos 3 días es > 0,03 % por 8h (unas 3 veces lo normal, ≈ 33 % TAE).
- Salir si baja de 0,005 % por 8h.
- Máximo 5 posiciones; cada una usa el 20 % del capital (75 % en spot y 25 % de margen del perpetuo a 3x → nocional = 15 % del capital).
- Costes por pata en la entrada y en la salida: spot 0,10 %, perpetuo 0,05 %, slippage 0,02 %.
- Si el precio sube un 20 % desde la referencia, se reequilibra el margen (coste extra de cerrar y reabrir el perpetuo).
- PnL = nocional × (rentabilidad spot − rentabilidad del perpetuo) + funding cobrado. Un trade = un episodio.

## 3. Criterios
**Desarrollo** (2020-2023 y 2024-2026 por separado): Sharpe > 0 en ambas mitades, Sharpe total ≥ 1,0 y PF ≥ 1,3.
**Examen** (solo las que pasen): Sharpe ≥ 0,5, PF ≥ 1,3 y **Deflated Sharpe ≥ 0,90** con todas las pruebas acumuladas.
Se informa siempre del **win rate** (S1/S3 por trade; S2 por semana).

## 4. Resultados en desarrollo (57 activos, universo point-in-time top 20) — `l06_salida_desarrollo.txt`

| Estrategia | Sharpe 20-23 | Sharpe 24-26 | Sharpe total | CAGR | DD máx. | Win rate | PF | Veredicto |
|---|---|---|---|---|---|---|---|---|
| S1 tendencia | 1,30 | 0,64 | 1,07 | 30,3 % | 29,3 % | 37 % | 1,78 | ✅ pasa |
| S2a momentum largo | 1,18 | 0,28 | 0,81 | 41,4 % | **87,4 %** | 49 % (sem.) | 1,36 | ❌ |
| S2b momentum largo-corto | 1,03 | 0,33 | 0,79 | 25,1 % | 35,2 % | 51 % (sem.) | 1,35 | ❌ |
| control: mercado a partes iguales | 0,90 | 0,14 | 0,58 | 16,3 % | 86,0 % | 50 % | 1,25 | — |
| **S3 carry de funding** | **5,69** | **2,79** | **4,58** | 12,7 % | **0,9 %** | **82 %** | **170** | ✅ pasa |

- **S1 con el universo realista:** Sharpe 1,07 (frente a 1,40 con el universo sesgado de la Lección 4). Esta es la expectativa honesta.
- **S2:** el momentum relativo supera al mercado, pero no llega al Sharpe 1,0 y se debilita mucho en 2024-26. El largo sin
  cobertura sufre caídas del 87 %. Rechazado.
- **S3, auditoría:** el beneficio viene del funding (+6,8 % por episodio sobre el nocional), no de la base (+0,1 %); costes 0,4 %.
  El PF altísimo se debe a que las pérdidas son minúsculas (solo comisiones cuando el funding se apaga pronto).
  **Corrección de modelo:** se detectó un salto del +49,5 % en 8h, que liquidaría la pata corta a 3x. Se añadió una simulación
  conservadora de liquidaciones (máximo intravela > +30 % → penalización del 1,5 % + reabrir): 29 liquidaciones en 56 episodios.
  En real se usará un **apalancamiento ≤ 2x** en la pata corta.
- **Límite de S3:** solo está invertido el 27 % del tiempo y en 2024-26 rinde un 2,9 % anual: el funding alto es ahora raro.

**Congeladas para el examen:** S1 y S3 tal cual (parámetros de la sección 2 + simulación de liquidaciones).

## 5. Examen (32 activos nunca usados, top 10 point-in-time, ejecutado UNA vez) — `l06_salida_examen.txt`

| Estrategia | Sharpe 20-23 | Sharpe 24-26 | Sharpe total | CAGR | DD máx. | Win rate | PF | Deflated Sharpe | Veredicto |
|---|---|---|---|---|---|---|---|---|---|
| S1 tendencia | 0,51 | 0,37 | 0,46 | 7,2 % | 22,2 % | 35 % | 1,32 | 0,08 | ❌ |
| **S3 carry de funding** | **5,20** | **1,84** | **4,06** | 10,6 % | **3,0 %** | **83 %** | **20,8** | **1,00** | ✅ **APROBADA** |
| (S2 informativo) momentum largo-corto | 0,16 | 0,42 | 0,31 | 2,4 % | 73 % | 48 % | 1,12 | — | — |

## 6. Conclusiones
1. **Primera estrategia que supera todos los filtros: el carry de funding.** Win rate del 83 %, PF > 20, DD del 3 %
   en activos nunca vistos, y significativa incluso descontando 342 pruebas (DSR ≈ 1,00).
   Su ventaja tiene una causa económica clara: los especuladores pagan por estar apalancados en largo.
2. **Limitaciones del carry:** rinde poco (10,6 % anual en el examen, 2,9 % en 2024-26), está invertido solo el ~26 % del
   tiempo y depende de que vuelvan las fases de euforia. Riesgos operativos: liquidación de la pata corta en subidas
   bruscas (21 simuladas), el riesgo del exchange (todo el capital en Binance) y la ejecución simultánea de las dos patas.
3. **La tendencia solo funciona en los activos grandes:** en las altcoins menores del examen, Sharpe 0,46 y no significativa.
   Encaja con la literatura (el momentum es más fuerte en las monedas grandes).
4. **El momentum relativo semanal no sobrevive a costes reales** con un universo realista.

## 7. Siguiente paso propuesto
- Núcleo **carry** (neutral al mercado, alto win rate) + **tendencia solo en BTC y ETH**, para rentabilizar el capital ocioso.
- Ajustes operativos que solo reducen costes o riesgo (no son nuevos parámetros de señal): apalancamiento ≤ 2x, entradas maker,
  comisiones con BNB.
- Cualquier cambio de umbrales se validará **hacia delante** (testnet/real pequeño), porque ya no quedan datos sin ver.
