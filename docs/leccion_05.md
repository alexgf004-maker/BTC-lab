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
