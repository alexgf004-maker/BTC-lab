# Lección 24 — Ampliar la reversión de los "mercados que duermen"

## 0. Datos descriptivos previos
- **El índice de los perpetuos de acciones NO se congela el fin de semana:** la prima media es ≈ 0,05 % tanto el martes como el sábado
  (TSLA, NVDA, QQQ, XAU…). La idea 3 de la lección anterior (prima frente a un índice congelado) queda descartada sin necesidad de prueba.
- El funding de fin de semana es pequeño (≈ 0,02 % por pago; máximo hasta 2 %).
- **Corrección de T1b:** la ventana de reacción (domingo 21:00 → lunes 03:00) incluye el pago de funding de las 00:00; no se había contado.

## 1. Pre-registro
Misma división de activos que la Lección 23 (semilla 2030). Precio = apertura de cada hora; se incluye el funding de la ventana de reacción.
Costes 0,14 % ida y vuelta. Criterio en todas: desarrollo y examen con resultado neto medio por periodo > 0 y t ≥ 2.
1. **T1b corregido** (con funding): corrección, no prueba nueva.
2. **Entrada más temprana en el fin de semana** (pruebas nuevas): W de viernes 21:00 hasta la entrada; R hasta el lunes 03:00.
   (a) entrada el sábado 21:00; (b) entrada el domingo 09:00. Umbral |W| ≥ 1 %.
3. **Noches entre semana, EE. UU.** (prueba nueva): W = 21:00 → 07:00 del día siguiente; R = 07:00 → 15:00 (preapertura y apertura).
   Noches de lunes a jueves. Umbral |W| ≥ 1 %. *Aviso:* entre semana los futuros del CME siguen cotizando y los creadores de mercado
   pueden cubrirse con ellos → se espera menos efecto que en el fin de semana.
4. **Materias primas, fin de semana** (prueba nueva): W = viernes 21:00 → domingo 21:00; R = domingo 21:00 → lunes 03:00. Umbral |W| ≥ 0,5 %.
5. **Asia, noches entre semana** (prueba nueva): W = 09:00 → 00:00 del día siguiente; R = 00:00 → 03:00. Umbral |W| ≥ 1 %.
6. **Festivos de EE. UU. entre semana:** solo descriptivo (muy pocos casos).
