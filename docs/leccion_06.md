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
