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

## 2. Resultados — `l20_salida_M1.txt`, `l20_salida_M2.txt`

### M1 — Desequilibrio del libro de órdenes (BTC, ETH, SOL, XRP, DOGE; 1397 días)
**11 de las 12 pruebas son significativas** en desarrollo (z de hasta +29) y **todas se replican con el mismo signo en el examen**
(z de hasta +21). El libro de órdenes predice el precio: cuando hay más compras que ventas cerca del precio, el precio tiende a subir
en los minutos siguientes. Es la señal más significativa de todo el proyecto.

Pero el efecto es minúsculo: la regla del decil extremo gana **≈ +0,01 % bruto** por operación, frente a un coste de 0,09–0,14 %.
Resultado neto en el examen: entre −0,10 % y −0,13 % por operación en todas las variantes (t de −5 a −211). **No operable.**

### M2 — Adelanto de BTC sobre las altcoins (1 min)
Correlación del minuto siguiente: −0,01 a +0,02 (simultánea: +0,60 a +0,80). Tras un minuto con BTC ±0,30 %, las altcoins siguen en el
mismo sentido solo +0,01 % a +0,05 % bruto. Neto, con 0,14 %: −0,09 % a −0,13 % por operación en todas las variantes. **No operable.**

## 3. Conclusión
La microestructura confirma la regla general del proyecto: **hay información real a escala de minutos, pero es entre 5 y 15 veces más
pequeña que los costes de un minorista.** Solo la capturan creadores de mercado con comisiones negativas y latencias de microsegundos.
Con esto quedan cerradas las vías de alta frecuencia: scalping (L10), funding al segundo (L12), libro de órdenes y adelanto de BTC (L20).
