# Lección 46 — Ruptura de números redondos (idea de un foro: "BTC perdió 60K con cierre diario")

Idea original (The 3AM Trader, Binance Square, 25-nov-2026): BTC defendió 60.000 tres días, cerró el día por debajo; vender los
rebotes hacia 60.000 y cerrar si el cierre diario vuelve a superarlo. ¿Los números redondos tienen algo especial, o es una ruptura
cualquiera?

## 1. Pre-registro (escrito y subido antes de ver ningún resultado)
**Datos:** velas diarias UTC de los perpetuos USDT de Binance (desde las de 1 h), 2020-01 → 2026-10. Universo: las 30 monedas más
líquidas de cada mes (sin sesgo de supervivencia, incluye deslistadas), BTC incluido. BTC+ETH se informan aparte, solo como dato.
Desarrollo 2020–2022, examen 2023–2026.

**Números redondos:** múltiplos de `paso = 5 × 10^(⌊log10 P⌋ − 1)`, con P el cierre del día anterior (BTC a 60.000 → cada 5.000;
ETH a 1.650 → cada 500; una moneda a 0,42 → cada 0,05).

**Señal corta (día t, al cierre):** los 3 cierres anteriores ≥ L, en esos 3 días el mínimo tocó L + 1 % o menos (el nivel fue
"defendido"), y el cierre de t < L. Si hay varios L, el más alto. **Señal larga:** el espejo (3 cierres ≤ L, máximo ≥ L − 1 %,
cierre de t > L).

**Entradas (2 variantes):**
- V1 "al cierre": apertura del día siguiente.
- V2 "vender el rebote" (lo que dice el trader): orden límite en L durante los 3 días siguientes; se llena solo si el precio
  atraviesa L un 0,1 %; si no se llena, no hay operación.

**Salidas:** cierre diario de vuelta al otro lado de L (lo que dice el trader); objetivo en el siguiente nivel redondo (L − paso en
cortos, L + paso en largos) tocado dentro del día; máximo 20 días. Si el mismo día se toca el objetivo y el cierre invalida, se
supone lo peor (salida al cierre). Una operación por moneda a la vez.

**Costes:** 0,07 % por lado (comisión + deslizamiento) y el funding real cobrado o pagado.

**Placebo:** las mismas reglas con niveles "no redondos": desplazados 0,37 × paso (p. ej. 61.850 en vez de 60.000).

**Medida:** rendimiento neto medio por operación; t-estadístico con errores agrupados por semana.

**Criterio de aprobación** (por lado × entrada, 4 pruebas): media neta > 0 en desarrollo y en examen, t ≥ 2,5 en todo el periodo,
y media mejor que la del placebo en los dos periodos. Si pasa, doble comprobación antes de llevarlo al bot.
