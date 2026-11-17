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
