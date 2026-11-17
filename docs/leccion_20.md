# Lección 20 — Microestructura: desequilibrio del libro de órdenes y adelanto de BTC sobre las altcoins

## 1. Pre-registro
**M1 — Desequilibrio del libro (bookDepth, instantáneas cada ~30 s, 2023-01 → 2026-10).** Monedas: BTC, ETH, SOL, XRP, DOGE.
Variables cada 5 min (última instantánea): `obi1` = (compras − ventas) / (compras + ventas) dentro del ±1 %; `obi5` igual dentro del ±5 %;
`dobi1` = cambio de obi1 en 15 min. Objetivos: rentabilidad futura a 5, 15, 60 y 240 min.
División temporal: desarrollo 2023-01 → 2024-12; examen 2025-01 → 2026-10.
Estadístico: correlación de rangos (IC) por moneda en observaciones no solapadas, combinada entre monedas; corrección de
Benjamini-Hochberg al 5 % sobre las 3 × 4 = 12 pruebas.
Operable solo si: significativa en desarrollo, mismo signo y p < 0,05 en el examen, **y** la regla "posición = signo de la variable cuando
está en su decil extremo, mantener h minutos" gana en el examen tras costes (BTC/ETH 0,09 %, resto 0,14 % ida y vuelta).

**M2 — Adelanto de BTC sobre las altcoins (velas de 1 min, 2024-01 → 2026-10, 10 altcoins grandes).**
Regla: si BTC se mueve ≥ 0,30 % en un minuto, entrar en cada altcoin en el mismo sentido al cierre de ese minuto y salir N minutos después
(N = 1, 3, 5). Costes 0,14 % ida y vuelta. Desarrollo 2024; examen 2025-01 → 2026-10.
Criterio: rentabilidad neta media > 0 con t ≥ 3 en el examen.
