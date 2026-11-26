# Hipótesis Tanda 3: Continuación, Flujos Forzados y Mercados Cerrados

## Lecciones incorporadas de las pruebas previas (Tandas 1 y 2)
- **Lo que muestra soporte empírico:** Tendencia, *momentum* de ráfaga, *carry*, corto en *altcoins* débiles frente a BTC y reversión de fin de semana en mercados con subyacente cerrado. En cripto abierto, apostar a la **continuación** supera sistemáticamente a la reversión (incluyendo que los activos sobrecargados de interés abierto caen más, no menos).
- **Lo que se descarta:** Reversiones de corto plazo (resacas, agotamientos, rupturas falsas), señales macro, microestructura por debajo de costes (0,14 % ida y vuelta) y supuestos liderazgos de otros exchanges frente a Binance.
- **Restricciones:** Reglas pre-registradas antes de ver resultados, desarrollo 2020–2022 y examen 2023–2026, costes 0,07 % por lado más *funding* real, pruebas de placebo y datos gratuitos desde 2020.

---

### 1. Reversión de fin de semana en oro tokenizado (`PAXG`) por cierre de COMEX/LBMA

* **Mecanismo:** Entre el cierre de los mercados institucionales de oro (viernes) y su reapertura el domingo por la noche, la liquidez real de COMEX/LBMA y los raíles de emisión/redención de Paxos permanecen cerrados mientras `PAXG` cotiza 24/7 en Binance. Durante fines de semana con pánico o euforia en cripto, los operadores liquidan `PAXG` para cubrir márgenes en USDT o huyen hacia él como refugio, separándolo del precio del oro físico; al reabrir Londres y Nueva York, los arbitrajistas devuelven el precio a la paridad del subyacente. Es el mismo cuello de botella que funciona en perpetuos de acciones, pero en una materia prima con historia desde 2020.
* **Regla exacta:**
  * **Señal:** Medir el retorno de fin de semana de `PAXGUSDT` entre el cierre horario del **viernes 20:00 UTC** (referencia segura antes del cierre de Nueva York todo el año, sin depender de cambios de horario de verano) y el **domingo 20:00 UTC**:
    $$R_{\text{fd}} = \frac{P_{\text{dom 20h}}}{P_{\text{vie 20h}}} - 1$$
    Calcular también la desviación estándar $\sigma_{20w}$ de los últimos 20 retornos de fin de semana.
  * **Entrada:** El domingo a las **20:00 UTC**, si $|R_{\text{fd}}| \ge \max(0{,}8\%,\; 1{,}5 \times \sigma_{20w})$, entrar en sentido contrario al movimiento del fin de semana (largo si cayó, corto si subió).
  * **Salida:** Cierre fijo el **lunes a las 14:00 UTC** (tras la apertura de Londres y la sesión matutina de COMEX), o al regresar al precio del viernes 20:00 UTC.
  * **Stop:** Rígido en $1{,}5 \times |R_{\text{fd}}|$ en contra desde la entrada (techo absoluto de $2{,}5\%$).
  * **Tamaño:** Escalado por volatilidad objetivo de cartera (exposición bruta máxima 1x).
  * **Frecuencia:** 1 evaluación semanal (domingo 20:00 UTC), con control horario de stop.
* **Datos necesarios y descarga:** Velas 1 h de `PAXGUSDT` en Binance Spot/Margen (disponibles desde agosto de 2020 en `data.binance.vision`; el perpetuo USDT-M arrancó en mayo de 2024, por lo que 2020–2024 debe simularse en spot/margen incluyendo la tasa de préstamo horaria de margen en la pata corta, o separar prueba solo-largo vs. largo-corto).
* **Signo esperado:** Positivo y con correlación cercana a cero frente a tendencia en BTC, *carry* y cortos en *altcoins*; tiende a activarse justo en pánicos cripto de fin de semana. La fricción de 0,14 % ida y vuelta exige filtrar por el umbral mínimo de $0{,}8\%$ para no operar ruido.
* **Cómo se demostraría falsa:** Placebo aplicando exactamente la misma regla de reversión de 48 horas entre el **martes 20:00 UTC y el jueves 20:00 UTC** (con COMEX y LBMA abiertos). Si la reversión entre semana es similar a la del fin de semana, el mecanismo de mercado cerrado es falso.
* **Riesgos:** Eventos geopolíticos reales durante el fin de semana donde es el oro de COMEX el que abre con brecha a favor del movimiento de `PAXG` (y no al revés); menor liquidez y mayor deslizamiento real en `PAXG` durante 2020–2021; baja frecuencia anual de disparos.

---

### 2. Continuación bajista por fuga de capital real on-chain (TVL deflactado en DefiLlama)

* **Mecanismo:** Cuando el capital abandona un ecosistema L1 o protocolo DeFi (retiradas de colateral, fin de incentivos, *unstaking* con bloqueos de 7 a 28 días), el TVL medido en dólares cae **más rápido que el precio del token nativo**. A diferencia de una oscilación de precio, la fuga de capital real es un proceso lento y forzado que reduce la liquidez y demanda estructural del protocolo durante semanas, generando continuación bajista mientras los compradores técnicos intentan atrapar el rebote.
* **Regla exacta:**
  * **Universo:** Subconjunto del Top 30 mensual formado por tokens L1 y DeFi con serie histórica mapeada en DefiLlama (cadenas como ETH, SOL, BNB, AVAX, TRX, MATIC/POL, ADA, ATOM, NEAR, FTM y protocolos como UNI, AAVE, CRV, MKR, LDO, COMP, SNX, CAKE).
  * **Señal:** Con retardo de 1 día natural sobre el dato diario de DefiLlama (para eliminar sesgo de anticipación), calcular el cambio logarítmico de 14 días del TVL deflactado por el precio del propio token:
    $$\Delta \text{RealTVL}_{i,14d} = \ln\left(\frac{\text{TVL}_{i,t-1}}{P_{i,t-1}}\right) - \ln\left(\frac{\text{TVL}_{i,t-15}}{P_{i,t-15}}\right)$$
  * **Entrada:** En revisión diaria (00:00 UTC), abrir **corto** en perpetuo USDT-M en los activos que cumplan simultáneamente: (1) $\Delta \text{RealTVL}_{i,14d} \le -10\%$, (2) precio por debajo de su media móvil simple de 30 días (confirmación de continuación bajista), y (3) *funding* medio de 7 días superior a $-0{,}05\%$/8 h.
  * **Salida:** Cerrar si $\Delta \text{RealTVL}_{i,14d} \ge 0\%$, si el precio cierra por encima de la SMA de 30 días, o tras 21 días naturales.
  * **Stop:** *Trailing stop* de $3 \times \text{ATR}_{24h}$ (techo rígido en $+12\%$ por activo) y salida de emergencia si el *funding* previsto cae por debajo de $-0{,}08\%$/8 h.
  * **Tamaño:** Ponderado por inversa de volatilidad de 30 días, máximo 6 activos simultáneos, tope bruto 1x.
  * **Frecuencia:** Revisión diaria (00:00 UTC), con vigilancia horaria de stops.
* **Datos necesarios y descarga:** API pública gratuita de DefiLlama (`api.llama.fi/v2/historicalChainTvl/{chain}` y `api.llama.fi/protocol/{slug}`, historia desde 2020) + velas diarias/horarias y *funding* de Binance.
* **Signo esperado:** Positivo en mercados bajistas y desarmes prolongados de ecosistemas; horizonte de semanas que amortiza con holgura el coste de 0,14 % ida y vuelta.
* **Cómo se demostraría falsa:** Dos pruebas obligatorias: (1) placebo aplicando la misma regla de precio ($P < \text{SMA}_{30d}$) a los tokens L1/DeFi con $\Delta \text{RealTVL}_{i,14d} \ge 0\%$ (si caen igual, el TVL real no añade valor); y (2) regresión de retornos contra la estrategia actual de corto en *altcoins* débiles frente a BTC (si el alfa residual $\alpha$ no es positivo y significativo, es redundante).
* **Riesgos:** Sesgo de mapeo o cambios metodológicos de DefiLlama (por ejemplo, cómo clasifica *staking* líquido o préstamos recursivos); cambios bruscos de TVL causados por migraciones de contratos v2$\to$v3 que simulan una salida falsa; universo reducido en 2020 frente a 2023–2026.

---

### 3. Continuación bajista por cobertura forzada de *dealers* en *Skew* extremo de Deribit

* **Mecanismo:** Cuando mesas institucionales compran agresivamente opciones *put* fuera de dinero en Deribit para cubrir carteras, el *skew* (diferencial de volatilidad implícita entre *calls* y *puts* de 25 delta) se hunde en terreno negativo extremo y los creadores de mercado quedan cortos en *puts* (*gamma* negativa y exposición a *vanna*). Si el precio rompe a la baja en ese estado, los *dealers* están obligados matemáticamente a vender futuros perpetuos a medida que cae el precio y sube la volatilidad implícita para mantenerse delta-neutrales, retroalimentando la caída en la misma dirección durante 24–72 horas.
* **Regla exacta:**
  * **Señal:** Cada hora, a partir de los vencimientos más cercanos a 14–30 días en Deribit (BTC y ETH por separado), calcular el *Risk Reversal* de 25 delta:
    $$RR_{25,t} = \text{IV}_{25\Delta\text{Call}} - \text{IV}_{25\Delta\text{Put}}$$
    y su $z$-score móvil de 90 días ($Z_{RR,t}$).
  * **Entrada:** Abrir **corto** en BTCUSDT o ETHUSDT al cierre horario cuando: (1) $Z_{RR,t} \le -2{,}0$ (demanda extrema de protección bajista), (2) el precio cierre por debajo de su mínimo de las últimas 24 h (confirma que el precio entra en la pendiente de cobertura forzada), y (3) el *funding* de Binance sea superior a $-0{,}05\%$/8 h.
  * **Salida:** Cerrar cuando $Z_{RR,t} \ge -0{,}5$ durante 3 horas consecutivas, o al cumplirse 72 horas desde la entrada.
  * **Stop:** *Trailing stop* de $2{,}5 \times \text{ATR}_{24h}$ (con tope rígido inicial de $+4{,}5\%$).
  * **Tamaño:** Escalado por volatilidad objetivo de cartera (50 % presupuesto de riesgo BTC, 50 % ETH; tope bruto 1x).
  * **Frecuencia:** Revisión horaria (baja rotación, concentrada en episodios de tensión).
* **Datos necesarios y descarga:** Histórico público de operaciones y libros de opciones de Deribit (`history.deribit.com`, desde 2020 para BTC y ETH) para interpolar $\text{IV}_{25\Delta}$ sobre el futuro subyacente + velas 1 h y *funding* de Binance.
* **Signo esperado:** Positivo en fases de aceleración bajista (alfa de crisis directo sobre BTC/ETH), con correlación baja o negativa frente a la cartera de *carry* y al *momentum* de ráfaga alcista.
* **Cómo se demostraría falsa:** Placebo disparando exactamente la misma ruptura de mínimo de 24 h en BTC/ETH cuando $Z_{RR,t} \ge 0$ (sesgo neutral o alcista en opciones). Si no existe diferencia significativa entre ambos regímenes de *skew*, el mecanismo de cobertura de *dealers* queda refutado.
* **Riesgos:** Reconstrucción histórica exigente de la superficie de volatilidad en 2020 (donde las *puts* OTM de ETH tenían menor liquidez); si los *dealers* llegan a la caída largos en *puts* (por venta masiva de productos estructurados) el flujo de cobertura puede amortiguar la caída en lugar de amplificarla; bajo número de eventos para errores agrupados.

---

### 4. Desarme forzado de líderes congestionados (*Crowded Winners Breakdown*)

* **Mecanismo:** La estrategia actual de debilidad relativa vende las monedas *más débiles*, y la prueba de Tanda 2 confirmó que las monedas sobrecargadas de apalancamiento son las que más caen. En el extremo opuesto del universo aparecen los "líderes congestionados": *altcoins* que subieron con fuerza acumulando interés abierto (en unidades de moneda) y *funding* alto positivo, concentrando largos tardíos con un coste medio muy agrupado. Cuando ese precio pierde el coste medio reciente de los largos, el desarme secuencial de stops y llamadas de margen provoca una continuación bajista violenta en monedas que la estrategia de debilidad relativa nunca toca.
* **Regla exacta:**
  * **Preselección diaria (00:00 UTC) en el Top 30:** Una moneda entra en lista de vigilancia si cumple las 3 condiciones de congestión alcista: (1) retorno de 14 días en el tercil superior del Top 30 y superior a $+10\%$, (2) variación de 14 días del interés abierto **en unidades de moneda** ($\text{OI}_{\text{USD}} / P$) superior a $+25\%$ (evita confundir subida de precio con entrada de apalancamiento), y (3) *funding* medio de 7 días superior a $+0{,}015\%$/8 h.
  * **Entrada (continuación, nunca contra la subida):** En revisión horaria, abrir **corto** solo cuando una moneda en vigilancia cierre por debajo de su $\text{VWAP}_{7d}$ **y** por debajo de su mínimo de 48 horas (confirma que los largos acumulados están bajo el agua).
  * **Salida:** Cerrar si el interés abierto en monedas cae al menos un 20 % desde el momento de entrada (apalancamiento purgado), o tras 7 días máximo.
  * **Stop:** *Trailing stop* de $2{,}5 \times \text{ATR}_{24h}$ (stop inicial rígido en $3 \times \text{ATR}_{24h}$).
  * **Tamaño:** Ponderado por inversa de volatilidad, máximo 5 nombres simultáneos, tope bruto 1x.
  * **Frecuencia:** Preselección diaria y ejecución/gestión horaria.
* **Datos necesarios y descarga:** Velas 1 h, *funding* e interés abierto del Top 30 de perpetuos USDT-M de Binance (2020–2026).
* **Signo esperado:** Positivo en giros de burbujas de *altcoins* y correcciones del mercado; por construcción selecciona activos del extremo opuesto a "corto en *altcoins* débiles", aportando diversificación real en el libro corto.
* **Cómo se demostraría falsa:** Placebo aplicando exactamente la misma ruptura ($\text{cierre} < \text{VWAP}_{7d}$ y mínimo de 48 h) a monedas del tercil superior de retorno de 14 días cuyo interés abierto en monedas haya caído o quedado plano ($\le 0\%$) y con *funding* $\le 0{,}01\%$. Si ambas cestas rinden igual, la congestión de largos no explica la caída.
* **Riesgos:** Falsa ruptura seguida de continuación parabólica en *memecoins* del Top 30; la condición de retorno $> +10\%$ y OI $> +25\%$ puede quedar inactiva durante mercados bajistas prolongados (concentra sus disparos en transiciones de techo y correcciones tras euforia).

---

### 5. Continuación de rupturas lideradas por flujo *Spot* (*Spot-Led Liquidation*)

* **Mecanismo:** Una ruptura bajista impulsada solo por volumen en perpetuos suele venir de especuladores poniéndose cortos, lo que crea combustible para rebotes violentos cuando cierran posiciones. En cambio, cuando tenedores no apalancados (fondos con reembolsos, tesorerías, inversores de largo plazo) liquidan inventario real, deben vender en el mercado **spot**; esas ventas no tienen que recomprarse nunca y suelen ejecutarse en bloques durante varios días, produciendo continuación bajista limpia sin gasolina de *short squeeze*.
* **Regla exacta:**
  * **Señal:** Para cada activo del Top 30 con par activo en Binance Spot y Perpetuo USDT-M, calcular cada hora la cuota móvil de 24 h del volumen en dólares ejecutado en *spot*:
    $$S_{i,t} = \frac{V_{24h,\text{Spot}}}{V_{24h,\text{Spot}} + V_{24h,\text{Perp}}}$$
    y su $z$-score móvil de 60 días ($Z_{S,i,t}$).
  * **Entrada:** Abrir **corto** en el perpetuo USDT-M al cierre horario cuando: (1) el precio cierre por debajo de su mínimo de 7 días (ruptura bajista activa), (2) $Z_{S,i,t} \ge +1{,}5$ (repunte anormal de participación *spot* durante la caída), y (3) *funding* medio de 24 h superior a $-0{,}05\%$/8 h.
  * **Salida:** Cerrar si $Z_{S,i,t} \le 0$ durante 12 horas seguidas (desaparece la presión relativa de *spot*), o a los 5 días máximo.
  * **Stop:** *Trailing stop* de $2{,}5 \times \text{ATR}_{24h}$ (techo inicial de $3 \times \text{ATR}_{24h}$).
  * **Tamaño:** Cesta ponderada por inversa de volatilidad, máximo 5 posiciones simultáneas, tope bruto 1x.
  * **Frecuencia:** Revisión horaria.
* **Datos necesarios y descarga:** Velas 1 h de Binance Spot (`data.binance.vision/data/spot/`) y de Binance Perpetuos USDT-M + *funding* (2020–2026). **Nota crítica de higiene de datos:** entre julio de 2022 y marzo de 2023 Binance eliminó las comisiones en `BTCUSDT` *spot*, distorsionando artificialmente su volumen *spot*; conviene excluir `BTCUSDT` de esa ventana o limitar el universo de esta señal a las 29 *altcoins* (incluyendo ETH) para evitar contaminación del $z$-score.
* **Signo esperado:** Positivo en fases de distribución real y caídas sostenidas; baja rotación relativa al horizonte de varios días y menor exposición a *short squeezes* que los cortos basados solo en precio.
* **Cómo se demostraría falsa:** Placebo disparando exactamente la misma ruptura de mínimo de 7 días cuando $Z_{S,i,t} \le -1{,}0$ (caídas lideradas por perpetuos, no por *spot*). Si las rupturas lideradas por *spot* no superan significativamente a las lideradas por perpetuos tras costes, el mecanismo queda descartado.
* **Riesgos:** Promociones puntuales de cero comisiones en pares *spot* concretos de Binance (por ejemplo, pares FDUSD/TUSD o campañas promocionales) que alteren $S_{i,t}$ sin que exista flujo vendedor real; posible solapamiento parcial con tendencia bajista en caídas generalizadas (requiere medir correlación con las estrategias activas).

---

### 6. Aceleración bajista por convexidad de colateral inverso (*Coin-M Margin Squeeze*)

* **Mecanismo:** A diferencia de los perpetuos lineales USDT-M (donde el colateral en USDT conserva su valor cuando el mercado cae), en los contratos inversos **Coin-M** el colateral es la propia criptomoneda. Cuando el precio baja, un largo apalancado en Coin-M sufre un doble golpe simultáneo —pérdida de PnL y caída del valor en dólares de su garantía—, acelerando de forma no lineal las liquidaciones forzosas a medida que cae el precio. No es *carry* entre familias de futuros: es usar la acumulación de apalancamiento en contratos inversos como detector de fragilidad estructural para operar la continuación bajista en el perpetuo lineal USDT-M.
* **Regla exacta:**
  * **Universo:** Activos del Top 30 mensual que cuenten con perpetuo Coin-M activo en Binance (BTC, ETH, BNB, XRP, ADA, SOL, DOT, LINK, LTC, BCH, DOGE, etc., según disponibilidad histórica).
  * **Señal:** Cada hora, calcular la cuota de interés abierto en contratos inversos sobre el total:
    $$C_{i,t} = \frac{\text{OI}_{i,t,\text{CoinM}}}{\text{OI}_{i,t,\text{CoinM}} + \text{OI}_{i,t,\text{USDTM}}}$$
    (expresando ambos en la misma unidad, USD o monedas) y la variación de 14 días de $\text{OI}_{\text{CoinM}}$ en monedas.
  * **Entrada:** Abrir **corto en el perpetuo USDT-M** al cierre horario cuando: (1) $C_{i,t}$ esté por encima de su percentil 75 de los últimos 90 días **o** el OI de Coin-M en monedas haya crecido al menos $+15\%$ en 14 días con *funding* Coin-M positivo, (2) el precio rompa a la baja su mínimo de 72 h con una caída en las últimas 6 h de al menos $1{,}5 \times \text{ATR}_{24h}$ (entra en la zona de compresión no lineal del margen), y (3) *funding* de USDT-M superior a $-0{,}05\%$/8 h.
  * **Salida:** Cerrar si el OI de Coin-M en monedas cae al menos un 15 % desde la entrada (liquidación de colateral completada), o a las 72 horas máximo.
  * **Stop:** *Trailing stop* de $2{,}5 \times \text{ATR}_{24h}$ (stop rígido inicial de $+6\%$).
  * **Tamaño:** Ponderado por inversa de volatilidad, máximo 5 activos simultáneos, tope bruto 1x.
  * **Frecuencia:** Revisión horaria.
* **Datos necesarios y descarga:** Velas 1 h, *funding* e interés abierto de Binance Coin-M (`data.binance.vision/data/futures/cm/`, lanzados entre agosto y septiembre de 2020) y USDT-M (`um`). Para BTC y ETH, el OI de los perpetuos inversos de Deribit sirve como validación cruzada desde 2020.
* **Signo esperado:** Positivo durante desplomes con desapalancamiento violento (alfa de crisis convexo); operar en USDT-M evita el riesgo de colateral inverso en la cuenta propia mientras captura el flujo forzado de quienes sí están atrapados en Coin-M.
* **Cómo se demostraría falsa:** Placebo ejecutando exactamente la misma ruptura de mínimo de 72 h y caída de $1{,}5 \times \text{ATR}_{24h}$ cuando $C_{i,t}$ está en el cuartil inferior ($< \text{percentil } 25$) y el OI de Coin-M no creció en 14 días. Si la continuación bajista es idéntica con poco o mucho colateral inverso, la hipótesis de convexidad muere.
* **Riesgos:** La cuota global de Coin-M frente a USDT-M ha descendido estructuralmente entre 2020 y 2026 (por eso la regla usa percentil móvil de 90 días y no un umbral fijo); en 2020 el periodo de desarrollo solo empieza en el cuarto trimestre; menor tamaño del universo elegible frente al Top 30 completo.

---

## Orden sugerido de pre-registro (menor fricción de datos a mayor)

| Prioridad | Hipótesis | Mecanismo central | Papel en la cartera | Riesgo principal de datos |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **#4 Líderes congestionados** | Liquidación de largos atrapados | Corto en activos opuestos a los débiles | Ya tienes todos los datos |
| **2** | **#5 Ruptura liderada por *Spot*** | Ventas de efectivo sin *short squeeze* | Filtra caídas reales vs. ruido de perps | Excluir ventana 0-fee de BTC (2022–23) |
| **3** | **#1 Fin de semana en `PAXG`** | Mercado subyacente cerrado (COMEX) | Descorrelación total con beta cripto | Modelar coste de margen 2020–24 |
| **4** | **#6 Convexidad Coin-M** | Compresión no lineal de colateral | Alfa de crisis en liquidaciones | Arranca en Q4 2020; tendencia secular de cuota |
| **5** | **#2 TVL real DefiLlama** | Fuga lenta de capital on-chain | Deriva bajista en *altcoins* L1/DeFi | Mapeo limpio sin sesgo de supervivencia |
| **6** | **#3 *Skew* 25$\Delta$ Deribit** | Cobertura *short-gamma/vanna* | Alfa de crisis directo en BTC/ETH | Interpolación IV en 2020 |