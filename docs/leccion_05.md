# Lección 5 — Reforzar la estrategia con lo que usan los profesionales (sin sobreajustar)

## 0. Qué dice la investigación
- **Zarattini, Pagani y Barbon (2025), "Catching Crypto Trends"** (SSRN 5209907): sistema solo largos
  sobre el top 20 de criptos líquidas. Combina un **conjunto de canales de Donchian con 9 periodos**
  (5, 10, 20, 30, 60, 90, 150, 250 y 360 días, según una réplica independiente), **stop dinámico** y
  **tamaño por volatilidad** con un objetivo del 25 % anual. Sharpe neto > 1,5 según el resumen del artículo.
- **Moskowitz, Ooi y Pedersen (2012), "Time Series Momentum"**: el momentum de serie temporal es un
  efecto amplio (58 mercados); se usa con tamaño inverso a la volatilidad.
- **Bailey y López de Prado (2014), "Deflated Sharpe Ratio"**: cuantas más variantes se prueban, mayor
  Sharpe se obtiene por pura suerte. El Sharpe debe "desinflarse" según el número de pruebas.
- **Funding:** evidencia mixta; la señal aparece sobre todo en los extremos (posiciones saturadas de largos).

## 1. El problema y cómo lo resolvemos
Los datos de 2024-2026 de los 10 activos **ya se miraron** en la Lección 3, así que no sirven como examen final.
Solución: **15 activos nuevos, nunca usados**, incluidos colapsos reales (LUNA, FTT) y deslistados
(EOS, MATIC) para evitar el sesgo de supervivencia:
DOT, LUNA, MATIC, ATOM, TRX, ETC, BCH, FIL, UNI, AAVE, EOS, XLM, ALGO, NEAR, FTT.
Este conjunto se ejecuta **UNA sola vez**, al final, con la configuración ya congelada.

## 2. Pre-registro (commiteado ANTES de ver resultados)
**Base (V0):** Lección 3/4, ruptura de 20 días (120 velas de 4h), chandelier m = 5, 1 % de riesgo, sin límite de posiciones.

Variantes, **cada una con un parámetro fijado de antemano por la literatura o por una regla económica**
(nada se optimiza):
| | Variante | Regla |
|---|---|---|
| V1 | Conjunto de periodos | 9 subsistemas con N = 5, 10, 20, 30, 60, 90, 150, 250 y 360 días; cada uno arriesga 1 %/9; misma salida |
| V2 | Filtro de régimen BTC | los activos distintos de BTC solo entran si BTC cierra por encima de su SMA de 200 días |
| V3 | Filtro de funding | no entrar si el funding medio de los últimos 3 días supera el 0,03 % por 8h (3 veces lo normal) |
| V4 | Objetivo de volatilidad | riesgo del trade × clip(25 % / vol. realizada de la cartera a 60 días; 0,5; 1,5) |
| V5 | Piramidación | al tocar +2R, añadir una segunda unidad con un 1 % de riesgo hasta el stop vigente; misma salida |

**Datos de desarrollo:** los 10 activos originales, 2020-2026, divididos en dos mitades (2020-2023 y 2024-2026).
**Métrica principal:** Sharpe anualizado de la curva diaria marcada a mercado. También: CAGR, DD máximo, MAR (CAGR/DD), win rate.
**Regla de adopción:** una variante se adopta solo si mejora **Sharpe y MAR en LAS DOS mitades** frente a V0.
**Combinación:** se unen todas las adoptadas; la combinación debe mejorar también a V0 en las dos mitades.
**Examen final (15 activos nuevos, una vez):** combinación frente a V0. Aprobación: Sharpe > V0, PF ≥ 1,3,
y **Deflated Sharpe ≥ 0,90** contando todas las pruebas hechas desde la Lección 2.

## 3. Resultados en desarrollo (10 activos) — `l05_salida_desarrollo.txt`

Cordura: V0 reproduce exactamente la Lección 4 (CAGR 36,9 %, DD 25,5 %). ✅

| Variante | Sharpe 20-23 | Sharpe 24-26 | MAR 20-23 | MAR 24-26 | DD máx. | Win rate | Veredicto |
|---|---|---|---|---|---|---|---|
| V0 base | 1,59 | 1,11 | 2,07 | 1,00 | 25,5 % | 40 % | referencia |
| V1 conjunto de periodos | 1,47 | 0,97 | 1,94 | 0,80 | 18,8 % | 39 % | rechazada |
| V2 régimen BTC | 1,57 | 1,22 | 2,53 | 0,91 | 29,8 % | 41 % | rechazada |
| V3 filtro de funding | **1,67** | **1,15** | **2,31** | **1,06** | 23,8 % | 41 % | **adoptada** |
| V4 objetivo de volatilidad | 1,72 | 0,98 | 2,13 | 0,81 | 29,6 % | 40 % | rechazada |
| V5 piramidación | **1,65** | **1,20** | **2,77** | **1,17** | 30,8 % | 42 % | **adoptada** |
| **Combinada (V3 + V5)** | **1,73** | **1,22** | **3,03** | **1,18** | 29,3 % | **44 %** | supera a V0 en ambas |

Observaciones:
- **V1 (la idea central del artículo) no mejora aquí:** los periodos cortos (5–10 días) diluyen la ventaja con
  más ruido y más costes. En nuestros datos manda la tendencia larga, coherente con la literatura reciente
  ("las tendencias cortas se han debilitado").
- V2 y V4 ayudan en una mitad y empeoran en la otra → por la regla, rechazadas. Así se evita adoptar suerte.
- La piramidación sube el CAGR pero también el DD: añade riesgo justo cuando la tendencia está confirmada.
- El filtro de funding evita entrar cuando los largos están saturados: menos trades, mejor calidad.

**Congelada:** `l05_config_congelada.json` = filtro de funding + piramidación. Commit ANTES del examen.
