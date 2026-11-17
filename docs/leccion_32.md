# Lección 32 — Desbloqueos de tokens: ¿cae el precio cuando los inversores pueden vender?

## 0. Mecanismo
Muchos tokens nacen con la mayor parte del suministro bloqueado: equipo, inversores privados y fondos del ecosistema lo reciben poco a poco
según un calendario público. Cuando llega un **desbloqueo grande ("cliff") de equipo o inversores**, que compraron muy por debajo del
precio, aparece oferta nueva. Hipótesis: el mercado lo anticipa mal, y los creadores de mercado y los propios inversores **se cubren
vendiendo perpetuos en los días previos**. Estudios del sector (p. ej. Keyrock, 2024, ≈16 000 desbloqueos) describen caídas que empiezan
antes del evento. Es el mismo mecanismo que explica el bloque B (emisión de tokens), pero con fecha conocida.

## 1. Datos
Calendarios de desbloqueo de DefiLlama (almacén público `defillama-datasets.llama.fi`, 373 tokens; 197 con perpetuo en Binance),
con la categoría de cada asignación (insiders = equipo y asesores, privateSale = inversores, ecosystem, farming, airdrop…).
Suministro en circulación en cada fecha: suma de lo desbloqueado según el propio calendario.
**Limitación declarada:** el calendario es el documentado hoy; si algún proyecto lo cambió, podría haber cierta información futura.
Se descartan emparejamientos de símbolo dudosos (precio actual de DefiLlama frente al último precio del perpetuo fuera de ×0,5–×2).

## 2. Pre-registro (antes de cruzar ningún evento con precios)
**Evento:** día T (UTC) con desbloqueo "cliff" de las categorías insiders + privateSale de tamaño s = cantidad / circulante el día anterior.
Grupos: **(i) grandes de equipo/inversores, s ≥ 1 %**; (ii) grandes de ecosistema/farming/airdrop/staking, s ≥ 1 %; (iii) pequeños de equipo/inversores, 0,1 % ≤ s < 1 %.
Liquidez: volumen medio del perpetuo de 30 días ≥ 5 M$. Rentabilidad anormal = rentabilidad del ratio altcoin/BTC (cierres diarios del perpetuo).
**U1 (medición):** rentabilidad anormal media en [T−30, T−8], [T−7, T−1], [T, T+6] y [T+7, T+30], por grupo, con placebo
(las mismas monedas en fechas al azar sin desbloqueos de equipo/inversores en ±30 días).
**U2 (estrategia):** corto en la altcoin y largo en BTC (mismo nocional) a las 00:00 UTC de T−7; salida a las 00:00 UTC de T+3. Solo grupo (i).
Una posición por moneda a la vez. Costes 0,28 % por operación (dos patas, entrada y salida) + funding real de las dos patas.
**Periodos:** desarrollo = eventos antes de 2024-01-01; **examen = 2024-01-01 → 2026-10-20** (una vez).
**Criterio U2:** rentabilidad neta media > 0 con t ≥ 3 agrupando por semana en el examen, positiva en desarrollo y mejor que el placebo.
**U3 (informativo):** solapamiento con el bloque B y correlación con su resultado. Pruebas nuevas: 1 (U2); U1 es medición.

## 2b. Pre-registro adicional (tras ver U1–U3, antes de calcular U4)
U1–U3 sugieren que la caída no está ligada al día del desbloqueo: las mismas monedas pierden frente a BTC también en fechas al azar
(placebo +1,8 % por operación de 10 días en el examen) y casi nunca coinciden con los cortos del bloque B (7 %).
**U4 — Factor de emisión (cesta neutral, reequilibrio mensual).** Cada inicio de mes, para los tokens con perpetuo líquido (volumen medio
de 30 días ≥ 5 M$): emisión programada E = circulante dentro de 90 días / circulante hoy − 1 (según el calendario, conocido de antemano).
**Corto en el tercio con más emisión y largo en BTC** (pesos iguales, mismo nocional total en cada lado). Control: el tercio con menos emisión.
Costes 0,14 % por unidad de nocional que rota en cada pata + funding real. **Desarrollo 2021-01 → 2023-12; examen 2024-01 → 2026-10.**
**Contaminación declarada:** el comportamiento medio de estas monedas en 2024–2026 ya se ha visto en el placebo; el examen no es limpio.
Si sale positiva, se considera **candidata a seguimiento en tiempo real** (simulado), no aprobada.
Criterio: Sharpe del tercio alto > 1 en los dos periodos **y** mayor que el del tercio bajo (la emisión debe explicar la diferencia).

## 3. Resultados — `l32_salida.txt`, `l32_salida_U3.txt`, `l32_salida_U4.txt`
**Datos:** 1 384 eventos con liquidez suficiente en 89 monedas (647 grandes de equipo/inversores, 240 de ecosistema, 497 pequeños);
22 emparejamientos de símbolo descartados por precio.

**U1 — Rentabilidad anormal frente a BTC (examen 2024–2026, grupo i frente a placebo):**
| Ventana | Desbloqueo grande de equipo/inversores | Placebo (mismas monedas, sin desbloqueo) | Diferencia |
|---|---|---|---|
| [T−30, T−8] | −5,9 % | −2,8 % | −3,1 % |
| [T−7, T−1] | −3,3 % (t −4,8) | −2,1 % | −1,2 % |
| [T, T+6] | −2,9 % | −1,9 % | −1,0 % |
| [T+7, T+30] | −8,2 % | −7,4 % | −0,8 % |
Hay un efecto propio del desbloqueo (−1 a −3 % adicional, sobre todo en el mes previo), pero **la mayor parte de la caída la sufren estas
monedas siempre**, haya desbloqueo o no. En el desarrollo (antes de 2024, menos eventos) el patrón es parecido pero no significativo.
Los desbloqueos de ecosistema y los pequeños se comportan igual que los grandes de equipo: no es tanto el tamaño del evento como el tipo de token.

**U2 — Corto altcoin / largo BTC de T−7 a T+3: NO APROBADA.**
| | Desarrollo | Examen |
|---|---|---|
| Desbloqueo grande equipo/inversores | +1,2 % por operación (t 0,5) | **+2,3 % (t 2,3; 66 % positivas)** |
| Placebo | −4,2 % | +1,8 % (t 1,4) |
No llega a t ≥ 3, y la ventaja sobre el placebo es de solo +0,45 % por operación. Por tamaño, los mayores (≥ 5 % del circulante) dan +3,6 %,
pero sin significación suficiente.

**U3 — Solapamiento con el bloque B:** solo el 7 % de estas operaciones coincide con un corto de B en la misma moneda (cuando coincide, +9,4 %).

**U4 — Factor de emisión (cesta corta del tercio con más emisión, largo BTC): NO APROBADA.**
| | Desarrollo 2021–2023 | Examen 2024–2026 (contaminado) |
|---|---|---|
| Tercio con más emisión (≈ 13,5 % en 90 días) | **−61 % anual, caída del 80 %** | +35 % anual, Sharpe 1,30 |
| Tercio con menos emisión (≈ 0,4 %) | −49 % anual | +11 % anual, Sharpe 0,62 |
En 2021 (temporada de altcoins) la cesta corta perdió un 93 %. En 2024–2026 el orden es el esperado (más emisión → peor), pero en
2021–2023 no. Estar corto de forma permanente en las altcoins es una apuesta de régimen, no una ventaja estable.

## 4. Conclusiones
1. **La emisión de tokens sí pesa**: las monedas con calendarios de desbloqueo pierden frente a BTC (−8 a −9 % al mes en 2024–2026), y el
   desbloqueo añade un −1 a −3 % adicional en las semanas previas. Es el mismo mecanismo que explica el bloque B.
2. **Pero no se puede operar mejor que lo que ya hace B.** El corto alrededor del desbloqueo no llega al criterio y gana poco más que
   un corto en cualquier fecha. El corto permanente se hunde en las temporadas de altcoins.
3. **B ya captura este efecto de la forma robusta**: corta solo cuando el ratio altcoin/BTC ya está en tendencia bajista, y eso le protege
   en las temporadas de altcoins (2021: −18 % frente a −93 % de la cesta permanente).
4. Pista para el futuro, sin aprobar: dar prioridad en B a las monedas con más emisión programada cuando hay más señales que huecos.
   Requiere un examen limpio (datos posteriores a hoy), así que solo se podría validar con seguimiento en tiempo real.
