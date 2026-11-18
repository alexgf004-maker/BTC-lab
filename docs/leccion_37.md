# Lección 37 — Acciones tokenizadas en Binance

## 0. Qué hay
Binance tiene **acciones tokenizadas en spot** (AAPLB, AMZNB, COINB, CRCLB, GOOGLB, HOODB, METAB, MSFTB, MSTRB, NVDAB, QQQB, SPYB, TSLAB
frente a USDT; desde junio de 2026) y **perpetuos de las mismas acciones** (desde 2026), los dos cotizando 24/7.
Eso permite tres ideas que ya funcionaron con criptos o con los perpetuos de acciones:

## 1. Pre-registro (antes de calcular resultados)
**K1 — Carry con acciones** (como el bloque A): largo en el token spot y corto en el perpetuo cuando el funding medio de 3 días > 0,015 %
por 8 h; salida si < 0,005 %. Mismas reglas y costes que A (spot 0,10 % + 0,02 %; perpetuo 0,05 % + 0,02 % por lado).
Se mide primero el funding de los perpetuos de acciones en toda su historia (2026), que es lo que cobraría K1, y después la operación
completa con los tokens spot (junio–octubre de 2026).
**K2 — Reversión del fin de semana en los tokens spot** (como el bloque F, que opera los perpetuos): mismas reglas que F
(domingo 21:00 UTC, |W| ≥ 1 %, salida lunes 03:00), con costes de spot. Se compara con el mismo cálculo en los perpetuos.
**K3 — Diferencial spot–perpetuo:** si el token spot se separa más de 0,5 % del perpetuo, comprar el barato y vender el caro;
salida cuando el diferencial vuelve a < 0,1 % o tras 24 h. Costes de las dos patas.
**Periodo:** toda la historia disponible (sin división: muestra demasiado corta). **Exploratorio:** como mucho, candidato a seguimiento
en papel; criterio t ≥ 3 en lo disponible y resultado positivo en los dos meses de mitades (jun–ago / sep–oct).
Pruebas nuevas: 3.

## 2. Resultados — `l37_salida.txt`
**K1 — Carry con acciones: RECHAZADO.** El funding de los perpetuos de acciones es bajo (de −3,7 % a +14,9 % anual; mediana ≈ 2–5 %) y
casi nunca persiste: solo CRCL pasa la mitad del tiempo por encima del umbral. Con los tokens spot (jun–oct 2026), 38 episodios y
−4,8 % anual: los episodios duran pocos días y los costes de entrar y salir de dos patas se comen el funding.
**K2 — Fin de semana en los tokens spot:** +0,83 % neto por operación (45 operaciones, 18 fines de semana, t 2,2), positivo en las dos
mitades (jun–ago +0,96 %, sep–oct +0,65 %). **Es el mismo efecto del bloque F** (los perpetuos dan +0,80 % las mismas semanas), ahora
visto en un instrumento distinto. No llega a t ≥ 3 y no es independiente de F, así que **no añade una pieza nueva, pero confirma F.**
Al ser spot (sin funding ni liquidación), es una alternativa para operar F si los perpetuos de acciones dejaran de estar disponibles.
**K3 — Diferencial spot–perpetuo:** normalmente están a 5–7 pb (0,05 %) uno del otro; solo en momentos puntuales se separan más de 0,5 %.
34 operaciones, +0,34 % neto, t 2,9: **no aprobado** (no llega a 3 y la muestra es de 5 meses), pero es la pista más interesante:
**candidato a seguimiento en papel.** Limitación: el volumen spot diario de varios tokens es pequeño (140 k$–1,5 M$).

## 3. Conclusión
Las acciones tokenizadas son un mercado nuevo con las mismas propiedades que ya explotamos: el fin de semana sin cobertura (F) se repite
en los tokens. El carry no funciona (el funding de las acciones es bajo) y el arbitraje spot–perpetuo existe pero es raro y pequeño.
Con 5 meses de historia no se puede aprobar nada nuevo; vale la pena volver a medirlo dentro de 6–12 meses.
