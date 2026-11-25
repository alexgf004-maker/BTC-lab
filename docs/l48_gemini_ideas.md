# Hipótesis de Estrategias Cuantitativas para Cartera Sistemática Cripto

## Contexto y Restricciones
- **Mercado y ejecución:** Binance (futuros perpetuos USDT-M, spot y margen). Coste estimado de ~0,05 % por lado en orden de mercado (~0,07 % con deslizamiento; 0,14 % ida y vuelta más *funding* en cortos). Revisión horaria o diaria (sin baja latencia).
- **Metodología:** Pre-registro de la regla antes de observar resultados, periodo de desarrollo (2020–2022) y de examen (2023–2026), universo de las 30 monedas más líquidas de cada mes (salvo indicación expresa), pruebas de placebo y $t$-estadístico con errores agrupados.
- **Objetivo:** Complementar la cartera existente (*carry*, tendencia en BTC/ETH, corto en *altcoins* débiles, *momentum* de ráfaga y reversión de fin de semana en perpetuos de acciones) con fuentes de **flujo forzado no basado en precio puro** y **convexidad bajista** o correlación cercana a cero con el *beta* de BTC.

---

### 1. Inversión de la estructura temporal de volatilidad en Deribit (Desapalancamiento de margen)

* **Mecanismo:** Las mesas institucionales y fondos de *carry* con margen de cartera en Deribit y CEX ven aumentar mecánicamente sus requisitos de colateral cuando la volatilidad implícita a corto plazo supera a la de 30 días (*backwardation*). Al no existir prestamista de última instancia ni pausas de mercado en cripto, ese endurecimiento dispara ventas forzadas de colateral en *spot* y perpetuos durante 24–72 horas. No es prima de volatilidad (no vendes opciones), sino continuación direccional por liquidación de balances institucionales.
* **Regla exacta:**
  * **Señal:** Cada hora, calcular el diferencial de volatilidad implícita *at-the-money* en Deribit: $S_t = \text{IV}_{7d,\text{ATM}} - \text{IV}_{30d,\text{ATM}}$ (interpolada linealmente en varianza entre los vencimientos más cercanos a 7 y 30 días).
  * **Entrada:** Abrir **corto** en BTCUSDT (50 %) y ETHUSDT (50 %) al cierre horario si $S_t \ge 5$ puntos de volatilidad (o $z$-score de 90 días superior a 2,0), la rentabilidad de BTC en las últimas 24 h es inferior a $-3\%$ (descarta *squeezes* alcistas de *calls*) y el *funding* previsto de Binance es superior a $-0,05\%$/8 h.
  * **Salida:** Cerrar cuando $S_t \le 0$ durante 3 horas consecutivas, o salida temporal a las 72 h.
  * **Stop:** Stop rígido en $+4\%$ sobre entrada o *trailing stop* de $2{,}5 \times \text{ATR}_{24h}$ (el más estrecho).
  * **Tamaño:** Escalado a volatilidad objetivo del 10 % anualizado, tope de apalancamiento bruto 1x.
  * **Frecuencia:** Revisión horaria (~6–12 eventos/año).
* **Datos necesarios y descarga:** Cadena histórica de opciones y *trades* de Deribit vía API pública (`public/get_last_trades_by_currency_and_time` / histórico de libros y DVOL desde 2021 como control cruzado) + velas 1 h y *funding* de Binance (`data.binance.vision`).
* **Signo esperado y magnitud frente a costes:** Positivo en caídas de mercado (alfa de crisis). Movimientos medios esperados de 3 %–7 % en 24–72 h frente a 0,14 % de ejecución y ~0,05 %–0,15 % de *funding* en contra.
* **Cómo se demostraría falsa:** Si su rendimiento neto no supera a un placebo que abre cortos tras la misma caída de $-3\%$ en 24 h *sin* inversión de curva ($S_t \le 0$), o si el efecto desaparece por completo en 2023–2026.
* **Riesgos:** Número reducido de eventos (bajo $N$, difícil superar el umbral de pruebas múltiples con errores agrupados); rebotes violentos en V por anuncios macro; menor liquidez en vencimientos de 7 días en 2020.

---

### 2. Ruptura del umbral de *carry* real frente a letras del Tesoro de EE. UU.

* **Mecanismo:** Los fondos de arbitraje *cash-and-carry* (largo *spot* + corto perpetuo) exigen una rentabilidad mínima superior al tipo libre de riesgo en dólares más una prima por riesgo de contraparte. Un *funding* anualizado del 4 % atraía capital en 2021 (tipos al 0 %), pero provoca salidas estructurales en 2023–2026 (letras al 4,5 %–5,5 %). Cuando el *funding* cae por debajo del tipo de las letras con el interés abierto todavía elevado, los arbitrajistas deshacen el *carry* vendiendo *spot* de forma persistente y retirando la demanda pasiva del mercado.
* **Regla exacta:**
  * **Señal:** Al cierre diario (00:00 UTC), calcular el *funding* anualizado medio de los últimos 14 días de BTC ($F_{14d}$) y restar el rendimiento anualizado de la letra del Tesoro a 3 meses de EE. UU. ($R_f$, serie `DTB3` con retardo de publicación de 1 día hábil): $E_t = F_{14d} - R_f$.
  * **Entrada:** Abrir **corto** en una cesta equiponderada por inversa de volatilidad de las 15 *altcoins* con mayor *beta* a 30 días dentro del Top 30 cuando $E_t$ cruce por debajo de $-2\%$ anualizado **y** el interés abierto de BTC (en unidades de BTC) esté por encima de su mediana de 90 días (indica *carry* aún congestionado por deshacer).
  * **Salida:** Cerrar si $E_t$ supera $+2\%$, si el interés abierto de BTC cae más de un 15 % desde la entrada (desapalancamiento completado) o a los 21 días naturales.
  * **Stop:** Stop de cesta en $+7\%$ sobre el precio medio de entrada o cierre individual si el *funding* de 7 días de una moneda cae por debajo de $-0,05\%$/8 h.
  * **Tamaño:** Volatilidad objetivo del 10 % anualizado, tope 1x bruto; actúa además como cobertura directa de la estrategia actual de *carry*.
  * **Frecuencia:** Revisión diaria (00:00 UTC).
* **Datos necesarios y descarga:** Serie `DTB3` (con fechas de publicación *vintage* vía ALFRED/FRED API) + *funding*, interés abierto y velas diarias/horarias de Binance.
* **Signo esperado y magnitud frente a costes:** Positivo en regímenes de drenaje de liquidez y mercados laterales/bajistas. Horizonte de 1–3 semanas con desplazamientos de 5 %–15 % frente a 0,14 % de costes de entrada/salida.
* **Cómo se demostraría falsa:** Si restar `DTB3` no añade $t$-estadístico incremental frente a usar un umbral fijo de *funding* bruto ($F_{14d}$ sin tipo libre de riesgo), o si su alfa desaparece al regresarla contra la estrategia actual de corto en *altcoins* débiles.
* **Riesgos:** Fases de pánico donde el *funding* negativo extremo precede a rebotes técnicos; cambio estructural si el acceso vía ETF *spot* reduce el peso del arbitraje de perpetuos en la formación de precios.

---

### 3. Rotación defensiva hacia BTC en episodios de estrés de paridad de *stablecoins*

* **Mecanismo:** A diferencia de la emisión neta de *stablecoins*, un desvío agudo de la paridad secundaria de USDT o USDC activa un cuello de botella físico en los raíles bancarios (horarios de oficina, redenciones T+1, límites KYC). El capital atrapado en cripto huye simultáneamente hacia BTC como único colateral percibido sin riesgo emisor mientras liquida *altcoins* y posiciones apalancadas en margen/DeFi para reducir riesgo. Los arbitrajistas no pueden inyectar dólares frescos al instante, generando una divergencia persistente durante horas o días.
* **Regla exacta:**
  * **Señal:** Cada hora, medir el desvío máximo de paridad $D_t = \max(|\text{USDT/USD} - 1|,\; |\text{USDC/USD} - 1|)$ usando el tipo implícito de Coinbase (`USDT-USD`) y DefiLlama (evitando así el hueco histórico de `USDCUSDT` en Binance durante la autoconversión a BUSD de 2022–2023).
  * **Entrada:** Cuando $D_t \ge 0{,}25\%$ durante 2 horas consecutivas, abrir una posición **neutral en dólar** (o neutral en *beta*): 100 % largo BTCUSDT frente a 100 % corto en cesta equiponderada por inversa de volatilidad de las 10 *altcoins* con mayor *beta* a 30 días del Top 30.
  * **Salida:** Cerrar cuando $D_t \le 0{,}10\%$ durante 6 horas consecutivas o tras un máximo de 7 días.
  * **Stop:** Stop del diferencial (*spread*) en $-5\%$.
  * **Tamaño:** Exposición bruta de 1x por pata (o escalada a volatilidad del *spread*).
  * **Frecuencia:** Revisión horaria (eventos poco frecuentes, ~4–10 por año).
* **Datos necesarios y descarga:** Histórico de precios de *stablecoins* de DefiLlama (`stablecoins.llama.fi`), velas horarias de `USDT-USD` en Coinbase y velas 1 h de perpetuos Top 30 en Binance.
* **Signo esperado y magnitud frente a costes:** Positivo durante crisis de liquidez y pánicos sistémicos. Diferenciales históricos de BTC frente a *altcoins* de 4 %–12 % en días de estrés frente a 0,28 % de costes totales de ambas patas.
* **Cómo se demostraría falsa:** Placebo condicionando a horas con la misma volatilidad realizada de BTC pero con $D_t$ inferior a $0{,}05\%$; si el *spread* BTC menos *altcoins* no supera al placebo, el mecanismo de estrés de colateral es falso.
* **Riesgos:** Muestra pequeña de crisis reales (riesgo de sobreajuste a episodios concretos como UST 2022 o SVB 2023); rebote abrupto de *altcoins* si el emisor publica una garantía o rescate imprevisto.

---

### 4. Agotamiento de bombas minoristas en Upbit por dominancia de volumen

* **Mecanismo:** No es la prima de precio *kimchi* sobre BTC, sino un fallo de arbitraje microeconómico por controles de capital en Corea del Sur que impiden a arbitrajistas extranjeros mover wones libremente. Periódicamente, el flujo minorista coreano concentra más del 35 %–50 % del volumen global *spot* de una *altcoin* concreta del Top 30 en Upbit, arrastrando su perpetuo en Binance por especulación anticipatoria. En cuanto decae el volumen local en Upbit, no existe demanda institucional fuera de Corea y el perpetuo de Binance revierte violentamente a la baja.
* **Regla exacta:**
  * **Señal:** Para cada moneda $i$ del Top 30 listada en pares KRW de Upbit, calcular cada hora la cuota de volumen en dólares de Upbit sobre el total (Upbit + Binance *spot*):
    $$U_{i,t} = \frac{V_{24h,\text{Upbit}}}{V_{24h,\text{Upbit}} + V_{24h,\text{BinSpot}}}$$
    (convirtiendo KRW a USD con el tipo implícito $\text{BTC}_{\text{Upbit}}/\text{BTCUSDT}_{\text{Binance}}$).
  * **Pre-activación (Fase 1):** $U_{i,t} \ge 0{,}35$, $U_{i,t} \ge 3 \times \text{Mediana}_{90d}(U_i)$ y subida de 24 h en Binance superior a $+15\%$.
  * **Entrada (Fase 2, agotamiento):** Abrir **corto** en el perpetuo USDT-M de Binance al primer cierre horario (dentro de las 24 h posteriores a Fase 1) en que el volumen móvil de 4 h en Upbit caiga al menos un 40 % desde el máximo de la bomba **y** el precio horario cierre por debajo de su VWAP de 6 h.
  * **Salida:** Cerrar a las 72 h, o si $U_{i,t}$ cae por debajo de $1{,}5 \times \text{Mediana}_{90d}(U_i)$, o toma de beneficios en $-15\%$.
  * **Stop:** Stop rígido en $+10\%$ sobre entrada (o máximo de 24 h $+1\%$), y salida de emergencia inmediata si el *funding* de Binance cae por debajo de $-0,10\%$/8 h.
  * **Tamaño:** 2 %–3 % de riesgo de cartera por nombre, máximo 4 posiciones simultáneas.
  * **Frecuencia:** Revisión horaria.
* **Datos necesarios y descarga:** API pública de velas horarias de Upbit (`minutes/60` para `KRW-*` y `KRW-BTC`) + velas horarias *spot*, perpetuos y *funding* de Binance.
* **Signo esperado y magnitud frente a costes:** Positivo en el lado corto e independiente de la dirección de BTC. Caídas medias tras agotamiento de 5 %–15 % frente a 0,14 % de ejecución más 0,2 %–0,6 % de posible coste de *funding* negativo.
* **Cómo se demostraría falsa:** Placebo sobre subidas de $+15\%$ en 24 h en Binance donde $U_{i,t}$ sea inferior a $0{,}10$; si la caída posterior es igual sin dominancia coreana, el mecanismo de controles de capital queda refutado.
* **Riesgos:** Bombas en doble oleada que barren stops antes de caer; sangrado severo por *funding* negativo si la multitud entra en corto demasiado pronto; cambios regulatorios en Corea que alteren el flujo minorista.

---

### 5. Liberación de Gamma tras vencimientos mensuales en Deribit

* **Mecanismo:** En las 24–48 horas previas a los vencimientos mensuales y trimestrales de Deribit (último viernes de mes, 08:00 UTC), los creadores de mercado suelen estar largos en *gamma* cerca de los *strikes* con mayor interés abierto (por la oferta estructural de opciones cubiertas y productos de rendimiento). Su cobertura delta (vender subidas, comprar caídas) ancla artificialmente el precio y comprime la volatilidad realizada; a las 08:00 UTC en punto esas coberturas desaparecen de golpe y el flujo direccional reprimido rompe el rango sin amortiguación.
* **Regla exacta:**
  * **Señal:** A las 07:00 UTC de cada viernes de vencimiento (mensual o semanal que represente al menos el 15 % del interés abierto total de Deribit en BTC o ETH), verificar dos condiciones: (1) al menos el 25 % del interés abierto que vence se concentra dentro de $\pm 2{,}5\%$ del precio *spot*, y (2) la volatilidad realizada de las últimas 24 h es inferior a $0{,}75 \times$ la volatilidad realizada de 30 días (confirma anclaje activo).
  * **Entrada:** Entre las 09:00 y las 14:00 UTC de ese mismo viernes, entrar en la dirección de la primera vela horaria que cierre fuera del rango [Máximo, Mínimo] de las 24 h previas al vencimiento (largo si rompe al alza, corto si rompe a la baja).
  * **Salida:** Cierre temporal a las 48 h desde la entrada o *trailing stop* de $2 \times \text{ATR}_{24h}$.
  * **Stop:** Lado opuesto del rango previo de 24 h, acotado a un máximo del 3,5 %.
  * **Tamaño:** Escalado por volatilidad (riesgo fijo del 1 % por evento).
  * **Frecuencia:** Revisión horaria en ventana de evento (~12–25 oportunidades/año entre BTC y ETH).
* **Datos necesarios y descarga:** Interés abierto por *strike* y vencimiento en Deribit + velas 1 h de BTCUSDT y ETHUSDT en Binance.
* **Signo esperado y magnitud frente a costes:** Positivo en expansiones bidireccionales (captura caídas bruscas cuando se rompe el suelo del rango). Desplazamientos post-anclaje de 2,5 %–5 % frente a 0,14 % de costes.
* **Cómo se demostraría falsa:** Placebo aplicando exactamente la misma regla de ruptura de rango a las 08:00 UTC en viernes con bajo interés abierto próximo al *spot* (inferior al 10 %) o en miércoles aleatorios; si no hay diferencia significativa, es mero ruido de ruptura.
* **Riesgos:** Cambio de signo del posicionamiento neto de *dealers* (si los creadores están cortos en *gamma* en lugar de largos, el efecto se invierte); baja frecuencia anual; falsas rupturas por noticias macro de EE. UU. (NFP/PCE suelen coincidir con viernes).

---

### 6. Fragilidad de liquidez bajista mediante Lambda de Kyle asimétrica (`aggTrades`)

* **Mecanismo:** El desequilibrio estático del libro de órdenes falla por *spoofing* y órdenes cancelables en milisegundos. Un fenómeno mucho más lento es la aversión al inventario de los creadores de mercado ante flujo tóxico: cuando detectan ventas informadas, retiran liquidez pasiva del lado comprador (*bid*) mucho más rápido que del vendedor (*ask*). Esto crea "bolsas de aire" bajistas donde cada dólar vendido mueve el precio sustancialmente más que un dólar comprado, amplificando cualquier venta posterior durante 12–48 horas.
* **Regla exacta:**
  * **Señal:** Para cada moneda del Top 30, agrupar `aggTrades` en intervalos de 1 minuto durante una ventana móvil de 24 h. Separar los minutos con flujo neto vendedor ($\text{SignedVol}_m \lt 0$) y comprador ($\text{SignedVol}_m \gt 0$) y estimar el impacto medio por dólar en cada lado:
    $$\lambda^- = \text{Mediana}\left(\frac{|\Delta p_m|}{|\text{SignedVol}_m|}\right)_{\text{venta}}, \quad \lambda^+ = \text{Mediana}\left(\frac{|\Delta p_m|}{|\text{SignedVol}_m|}\right)_{\text{compra}}$$
    Definir la asimetría de iliquidez $A_{i,t} = \ln(\lambda^- / \lambda^+)$ y estandarizarla en ventana móvil de 30 días ($z$-score $Z_{A,i,t}$).
  * **Entrada:** Abrir **corto** en el perpetuo USDT-M al cierre horario cuando $Z_{A,i,t} \ge 2{,}0$ (impacto bajista anormalmente alto respecto al alcista) **y** el retorno de las últimas 6 h esté entre $-3\%$ y $+1\%$ (aún no se ha producido el desplome completo).
  * **Salida:** Cerrar tras 36 h o cuando $Z_{A,i,t} \le 0{,}5$.
  * **Stop:** Stop rígido de $2{,}5 \times \text{ATR}_{24h}$ (techo 6 %).
  * **Tamaño:** Cesta equiponderada por volatilidad, máximo 5 nombres simultáneos, 10 % volatilidad objetivo anualizada.
  * **Frecuencia:** Revisión horaria.
* **Datos necesarios y descarga:** `aggTrades` históricos de Binance (`data.binance.vision`, disponibles desde 2020) + velas 1 h y *funding*.
* **Signo esperado y magnitud frente a costes:** Positivo en el lado corto (convexidad bajista). Horizonte de 1–2 días con recorridos esperados de 2 %–5 % frente a 0,14 % de ejecución.
* **Cómo se demostraría falsa:** Si el efecto desaparece al controlar por volatilidad realizada total y rentabilidad reciente de 24 h, o si el caso simétrico alcista ($Z_{A,i,t} \le -2{,}0$ para largos) produce el signo opuesto al teórico.
* **Riesgos:** Alto coste computacional de procesar `aggTrades` históricos de 6 años para todo el universo; posible contaminación por órdenes *wash* o cambios en los programas de *rebates* de creadores de mercado de Binance entre 2020–2022 y 2023–2026.

---

### 7. Distribución silenciosa por estratificación de tamaño en `aggTrades`

* **Mecanismo:** Las variables clásicas de volumen comprador/vendedor mezclan todos los participantes. En fases de distribución institucional, tenedores grandes venden agresivamente mediante ejecuciones en el percentil superior de tamaño mientras el público minorista absorbe las caídas con órdenes pequeñas, manteniendo el precio plano o ligeramente alcista. Cuando la liquidez minorista se agota al cabo de 1–3 días, el precio quiebra a la baja sin soporte institucional debajo.
* **Regla exacta:**
  * **Señal:** Para cada activo del Top 30, calibrar en ventana móvil de 30 días dos umbrales dinámicos sobre el nocional en USD de cada `aggTrade`: operaciones grandes $G$ (percentil $\ge 99$) y pequeñas $P$ (percentil $\le 50$). Calcular el desequilibrio neto agresivo (*taker buy* menos *taker sell*, dividido por suma) en las últimas 24 h por separado: $\text{OFI}_{G,t}$ y $\text{OFI}_{P,t}$.
  * **Entrada:** Abrir **corto** al cierre horario cuando $\text{OFI}_{G,t} \le -0{,}25$ (venta agresiva sostenida de órdenes grandes), $\text{OFI}_{P,t} \ge +0{,}15$ (compra agresiva minorista) **y** el retorno de 24 h sea superior a $0\%$ (el precio todavía resiste gracias al flujo minorista).
  * **Salida:** Cerrar a las 48 h o cuando $\text{OFI}_{G,t} \ge 0$ durante 6 horas seguidas.
  * **Stop:** Stop en $+4\%$ para BTC/ETH y $+7\%$ para *altcoins* (o $2{,}5 \times \text{ATR}_{24h}$).
  * **Tamaño:** Máximo 5 activos simultáneos, ponderados por inversa de volatilidad (volatilidad objetivo 10 %).
  * **Frecuencia:** Revisión horaria.
* **Datos necesarios y descarga:** `aggTrades` de Binance (`data.binance.vision`, perpetuos y opcionalmente *spot* para validación cruzada) + velas 1 h.
* **Signo esperado y magnitud frente a costes:** Positivo en techos locales y mercados laterales/bajistas; baja correlación con ruptura de tendencia porque vende cuando el precio aún está en verde. Recorrido objetivo 2 %–6 % frente a 0,14 % de costes.
* **Cómo se demostraría falsa:** Placebo usando el $\text{OFI}$ total sin estratificar por tamaño; si la divergencia entre grandes y pequeños no supera significativamente al $\text{OFI}$ agregado, la hipótesis de distribución informada es falsa.
* **Riesgos:** Decaimiento estructural en 2024–2026 debido a algoritmos institucionales TWAP/VWAP que trocean órdenes grandes en ejecuciones pequeñas, contaminando el cubo minorista $P$.

---

### 8. Transmisión retardada de estrés de crédito y tipos reales de EE. UU. (FRED)

* **Mecanismo:** Los operadores nativos de cripto reaccionan al instante a titulares de IPC o FOMC, pero infrarreaccionan ante el deterioro silencioso de las condiciones financieras institucionales (ampliación de diferenciales de crédito *high-yield* y repunte simultáneo de tipos reales TIPS). Los fondos multiactivo tradicionales reequilibran presupuestos de riesgo con cadencia semanal o quincenal, generando salidas diferidas de activos de alta *beta* —especialmente *altcoins*— durante los 5–15 días posteriores al shock macro.
* **Regla exacta:**
  * **Señal:** Con datos diarios de FRED estrictamente alineados a su fecha real de publicación (vía ALFRED + 1 día de margen de seguridad), construir un índice de endurecimiento:
    $$M_t = z_{252}(\Delta_{5d}\text{HY\_OAS}) + z_{252}(\Delta_{5d}\text{DFII10})$$
    donde `BAMLH0A0HYM2` es el diferencial *high-yield* y `DFII10` el tipo real a 10 años.
  * **Entrada:** Al cierre diario (00:00 UTC) cuando $M_t \ge 2{,}0$, abrir **corto** en una cesta equiponderada por inversa de volatilidad de las 15 *altcoins* de mayor *beta* a 30 días del Top 30.
  * **Salida:** Cerrar cuando $M_t \le 0{,}5$ o al cumplirse 10 días hábiles desde la entrada.
  * **Stop:** Stop de cesta en $+6\%$ (o cierre si BTC rompe máximo de 20 días al alza).
  * **Tamaño:** Volatilidad objetivo del 10 % anualizado, tope 1x bruto.
  * **Frecuencia:** Revisión diaria (00:00 UTC).
* **Datos necesarios y descarga:** Series `BAMLH0A0HYM2` y `DFII10` desde FRED/ALFRED (gratuito, con marcas de publicación para evitar sesgo de anticipación) + velas diarias de Binance.
* **Signo esperado y magnitud frente a costes:** Positivo en mercados bajistas impulsados por condiciones financieras (2022, repuntes de rendimientos en 2023–2025). Horizonte de 1–2 semanas con movimientos esperados de 4 %–10 % frente a 0,14 % de costes.
* **Cómo se demostraría falsa:** Desplazar la serie macro $\pm 15$ días como placebo o regresar sus retornos contra la estrategia actual de tendencia en BTC/ETH y corto en *altcoins* débiles; si el alfa residual $\alpha$ no es positivo y significativo, no aporta información nueva.
* **Riesgos:** Sesgo de revisión si no se usan fechas *vintage* de ALFRED; desacoplamiento de régimen si los repuntes de tipos se asocian a riesgo fiscal soberano y el capital usa cripto como cobertura.

---

### 9. Espiral de atrición de liquidez y riesgo de deslistado (Cola larga fuera del Top 30)

* **Mecanismo:** Cuando un perpetuo fuera del Top 50 sufre un colapso prolongado de volumen y precio, Binance recorta los tramos de apalancamiento, eleva márgenes o coloca etiquetas de monitoreo antes del deslistado, forzando la salida de largos y creadores de mercado. Los fondos institucionales no pueden arbitrar esta decadencia porque la capacidad es minúscula para sus patrimonios; un operador minorista con diversificación y frenos contra *short squeezes* sí puede capturarla. *(Nota: exige salir deliberadamente del universo Top 30 y aprovechar la base de ~700 perpetuos incluidos los deslistados).*
* **Regla exacta:**
  * **Señal:** Cribado semanal (lunes 00:00 UTC) sobre todos los perpetuos USDT-M activos fuera del Top 50 por volumen, exigiendo volumen medio de 7 días superior a 3 M USD (ejecución minorista viable). Seleccionar activos que cumplan simultáneamente: (1) volumen medio de 90 días ha caído al menos un 70 % desde su pico de 365 días, (2) precio está al menos un 60 % por debajo de su máximo de 365 días y por debajo de su media móvil de 50 días, y (3) *funding* medio de 7 días es superior a $-0,01\%$/8 h (filtra cortos congestionados).
  * **Entrada:** Abrir **corto** equiponderado en hasta 15 candidatos (los de mayor caída relativa de volumen).
  * **Salida:** Rebalanceo semanal; cierre inmediato en revisión horaria si el *funding* medio de 3 días cae por debajo de $-0,05\%$/8 h (riesgo de *squeeze*) o si el volumen de 4 h supera $5 \times$ la mediana de 30 días (entrada de manipulación/*pump*).
  * **Stop:** Stop rígido individual en $+25\%$ sobre precio de entrada (imprescindible ante bombas ilíquidas).
  * **Tamaño:** Exposición bruta máxima total 0,5x del capital; máximo 4 % nocional por moneda.
  * **Frecuencia:** Selección semanal con disyuntores horarios.
* **Datos necesarios y descarga:** Histórico completo de ~700 perpetuos USDT-M de Binance incluidos los deslistados (sin sesgo de supervivencia), velas 1 h y *funding*.
* **Signo esperado y magnitud frente a costes:** Positivo en mercados laterales y bajistas. Horizonte de varias semanas con decaimientos medios de 8 %–20 % frente a costes estimados superiores (~0,25 %–0,35 % ida y vuelta por mayor deslizamiento en cola larga).
* **Cómo se demostraría falsa:** Si los costes reales de deslizamiento (simulados con `bookTicker`/profundidad) más los eventos de cola (+25 % *stops* y *funding* negativo) anulan la deriva bajista, o si el rendimiento cae a cero en mercados alcistas de *altcoins* sin compensación en el ciclo completo.
* **Riesgos:** Riesgo de cola extremo por manipulaciones coordinadas ("*short squeezes*" de +100 % en horas en monedas moribundas); anuncios repentinos de deslistado con liquidación forzosa a precio índice desfavorable; mayor deslizamiento real que el 0,07 % del Top 30.

---

### 10. Prima de lotería pura (Efecto MAX normalizado por volatilidad)

* **Mecanismo:** La literatura empírica (Bali, Cakici y Whitelaw) documenta que los inversores minoristas sobrepagan por activos con pagos tipo lotería (saltos horarios extremos positivos), generando rendimientos futuros sistemáticamente negativos cuando el entusiasmo se disipa. Es distinto de la reversión diaria y de la volatilidad total: a igual retorno semanal y a igual volatilidad, los activos cuyo movimiento proviene de un único pico explosivo (asimetría positiva extrema) sobrevaloran la cola alcista frente a los que suben de forma gradual. Es además ortogonal a la estrategia actual de corto en *altcoins* débiles, pues suele vender activos recientes fuertes o neutrales.
* **Regla exacta:**
  * **Señal:** Cada día a las 00:00 UTC, para las 30 monedas más líquidas del mes, calcular la media de las 3 mayores rentabilidades horarias positivas en los últimos 14 días ($\text{MAX3}_{14d}$) dividida por la desviación estándar horaria de esos mismos 14 días ($\sigma_{14d}$):
    $$L_{i,t} = \frac{\text{MAX3}_{14d,i}}{\sigma_{14d,i}}$$
    Para aislar pureza de lotería, ortogonalizar transversalmente $L_{i,t}$ frente al retorno total de 14 días y a $\sigma_{14d}$ (residuo de regresión transversal diaria).
  * **Entrada:** Mantener una cartera **neutral en mercado** con rebalanceo cada 72 h (o por bandas de rotación para reducir costes): **corto** en el quintil superior (6 monedas con mayor residuo de lotería) y **largo** en el quintil inferior (6 monedas con menor residuo, movimientos más suaves), excluyendo monedas con *funding* de 24 h inferior a $-0,05\%$/8 h en la pata corta.
  * **Salida:** Al salir del quintil extremo (con histéresis: mantener mientras siga en los 10 primeros/últimos para recortar rotación) o tras 7 días.
  * **Stop:** Stop individual en la pata corta de $+12\%$ sobre precio de entrada.
  * **Tamaño:** Dólar-neutral, ponderado por inversa de volatilidad de 30 días, volatilidad objetivo del 10 % anualizado.
  * **Frecuencia:** Rebalanceo cada 3 días (revisión horaria solo para stops y filtro de *funding*).
* **Datos necesarios y descarga:** Velas 1 h y *funding* del universo Top 30 de Binance (`data.binance.vision`).
* **Signo esperado y magnitud frente a costes:** Positivo y de baja correlación con BTC y con tendencia relativa. Con histéresis de 3–7 días la rotación semanal queda en ~30 %–50 % por lado (coste ~0,10 %–0,15 %/semana) frente a un diferencial esperado de 0,4 %–0,8 %/semana.
* **Cómo se demostraría falsa:** Si el residuo ortogonalizado frente al retorno de 14 días y a la volatilidad total da un $t$-estadístico nulo (lo que probaría que era solo reversión o baja volatilidad disfrazadas), o si la pata corta pierde dinero de forma sistemática por continuación de *momentum*.
* **Riesgos:** Choque directo contra burbujas parabólicas de *memecoins* en el Top 30 donde un salto horario precede a varios días más de euforia; sensibilidad a la rotación si no se aplica banda de histéresis.

---

## Priorización sugerida para la cola de pre-registro

| # | Hipótesis | Perfil frente a caídas de BTC | Correlación esperada con tu cartera | Complejidad de datos (2020–2026) |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Curva IV Deribit (Backwardation) | Muy alta (alfa de crisis) | Muy baja / negativa | Media (cadena Deribit) |
| **2** | *Carry* real vs. FRED `DTB3` | Alta (cubre tu *carry*) | Negativa con *carry* | Baja |
| **4** | Agotamiento volumen Upbit | Alta (corto idiosincrático) | Muy baja | Baja–Media (API Upbit) |
| **7** | Estratificación `aggTrades` | Media–Alta (techos) | Baja | Alta (ETL `aggTrades`) |
| **6** | Lambda de Kyle asimétrica | Alta (fragilidad bajista) | Baja | Alta (ETL `aggTrades`) |
| **8** | Estrés crédito/tipos FRED | Alta (macro bajista) | Baja–Media (revisar vs. cortos) | Baja (usar ALFRED) |
| **10** | Prima de lotería ($\text{MAX}/\sigma$) | Neutral (corta euforia) | Negativa con cortos en débiles | Baja |
| **5** | Liberación Gamma Deribit | Bidireccional | Muy baja | Media (OI por *strike*) |
| **3** | Estrés de paridad *stablecoins* | Alta (crisis sistémica) | Muy baja | Baja–Media (bajo $N$) |
| **9** | Cola larga / deslistados | Alta (deriva bajista) | Baja–Media (fuera Top 30) | Baja (ya descargado) |

**Recomendación operativa:** Para maximizar potencia estadística sin quemar presupuesto de pruebas múltiples, pre-registra primero las de menor fricción de datos y mayor distancia económica respecto a OHLCV puro (**#2**, **#4**, **#10** y **#1**), dejando el ETL pesado de `aggTrades` (**#6** y **#7**) para una segunda tanda.