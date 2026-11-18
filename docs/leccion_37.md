# Lección 37 — Acciones tokenizadas en Binance

## 0. Qué hay
Binance tiene **acciones tokenizadas en spot** (AAPLB, AMZNB, COINB, CRCLB, GOOGLB, HOODB, METAB, MSFTB, MSTRB, NVDAB, QQQB, SPYB, TSLAB
frente a USDT; desde junio de 2026) y **perpetuos de las mismas acciones** (desde 2025), los dos cotizando 24/7.
Eso permite tres ideas que ya funcionaron con criptos o con los perpetuos de acciones:

## 1. Pre-registro (antes de calcular resultados)
**K1 — Carry con acciones** (como el bloque A): largo en el token spot y corto en el perpetuo cuando el funding medio de 3 días > 0,015 %
por 8 h; salida si < 0,005 %. Mismas reglas y costes que A (spot 0,10 % + 0,02 %; perpetuo 0,05 % + 0,02 % por lado).
Se mide primero el funding de los perpetuos de acciones en toda su historia (2025–2026), que es lo que cobraría K1, y después la operación
completa con los tokens spot (junio–octubre de 2026).
**K2 — Reversión del fin de semana en los tokens spot** (como el bloque F, que opera los perpetuos): mismas reglas que F
(domingo 21:00 UTC, |W| ≥ 1 %, salida lunes 03:00), con costes de spot. Se compara con el mismo cálculo en los perpetuos.
**K3 — Diferencial spot–perpetuo:** si el token spot se separa más de 0,5 % del perpetuo, comprar el barato y vender el caro;
salida cuando el diferencial vuelve a < 0,1 % o tras 24 h. Costes de las dos patas.
**Periodo:** toda la historia disponible (sin división: muestra demasiado corta). **Exploratorio:** como mucho, candidato a seguimiento
en papel; criterio t ≥ 3 en lo disponible y resultado positivo en los dos meses de mitades (jun–ago / sep–oct).
Pruebas nuevas: 3.
