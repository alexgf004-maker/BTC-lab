# Reglas de Ejecución y Nuevas Ideas de Alfa para Cartera Sistemática Cripto

## Enfoque general
En una cartera sistemática con ~500 pruebas previas y un coste operativo de **0,07 % por lado** en Binance Futures (revisión horaria), la mejora más directa en rentabilidad neta proviene de dos frentes:
1. **Recortar fugas de ejecución y arrastre de *funding*** en las estrategias que ya funcionan.
2. **Explotar fuentes de datos gratuitas aún infrautilizadas** (Hyperliquid, consenso de interés abierto entre Binance/Bybit/OKX, Polymarket como sensor de shocks y acciones *proxy* entre semana).

---

## Bloque 1: 3 reglas de ejecución y gestión para exprimir tus estrategias actuales

Estas reglas no añaden indicadores subjetivos ni control de caídas clásico; atacan directamente las fricciones que erosionan la rentabilidad neta de la operativa horaria.

### 1. Ejecución "Maker-Chaser" en 3 minutos (recorta tu coste de 0,07 % a ~0,02 %)
* **La idea:** En estrategias horarias o diarias, entrar a orden de mercado suele ser urgencia innecesaria. Pasar de *taker* con deslizamiento (0,07 %) a tarifa *maker* en Binance Futures (0,02 %) transforma el umbral de supervivencia de cualquier señal.
* **Regla exacta:**
  1. Al cierre de la hora (salvo en el *momentum* de ráfaga de 3 h, donde prima la urgencia), enviar orden `LIMIT` con flag `POST_ONLY` al mejor precio del libro (`best_bid` para largo, `best_ask` para corto).
  2. **Minuto 1 y Minuto 2:** Si no se ejecutó, cancelar y recolocar en el nuevo `best_bid` / `best_ask`.
  3. **Minuto 3 (límite anti-persecución):** Si el precio se alejó **menos de 0,15 %** a favor de la señal, cruzar a mercado; si se alejó **más de 0,15 %**, cancelar la entrada y no perseguir.
  4. **Stops:** Los stops de protección siempre se ejecutan a mercado (nunca `POST_ONLY`).
* **Impacto esperado:** En una estrategia con 100 rotaciones ida y vuelta al año, reducir el coste de 0,14 % a ~0,04 % por vuelta recupera **+10 % neto anualizado** sin alterar el alfa subyacente.

### 2. Stop por presupuesto de sangrado (*Funding Bleed Stop*)
* **La idea:** En estrategias cortas de *altcoins* débiles, muchas posiciones no tocan el stop de precio, pero pierden rentabilidad lentamente pagando *funding* negativo mientras el activo lateraliza.
* **Regla exacta:**
  1. Desde la entrada del corto, llevar un contador del *funding* acumulado pagado en contra ($F_{\text{acum}}$) como porcentaje del nocional.
  2. **Salida por sangrado:** Cerrar en la revisión horaria si $F_{\text{acum}} \ge 0{,}60\%$ **y** la ganancia latente por precio es inferior a $+2{,}5\%$.
  3. **Disyuntor de *squeeze*:** Cerrar de inmediato si el *funding* previsto del siguiente corte cae por debajo de $-0{,}08\%$/8 h.
* **Impacto esperado:** Corta el drenaje silencioso de cortos congestionados y evita servir de liquidez de salida en *short squeezes*.

### 3. Penalización de tamaño por riesgo de aplastamiento (Ratio OI / Volumen)
* **La idea:** Dos *altcoins* con idéntica volatilidad realizada no presentan el mismo riesgo bajista. Aquella con un interés abierto desproporcionado frente a su volumen diario acumula combustible para un *squeeze* violento.
* **Regla exacta:** Antes de abrir cualquier corto en el Top 30, calcular $R_{i,t} = \text{OI}_{i,t} / \text{Volumen}_{24h,i,t}$ y ubicarlo en su percentil móvil de los últimos 90 días:
  * **Inferior al percentil 75:** tamaño normal (100 %).
  * **Entre percentil 75 y 90:** reducir tamaño a la mitad (50 %).
  * **Superior al percentil 90:** no entrar (0 %).
* **Impacto esperado:** Mitiga los 3 o 4 latigazos extremos anuales que suelen borrar meses de ganancia en cestas cortas, manteniendo intactos los descensos ordenados.

---

## Bloque 2: 5 ideas creativas de alfa con fuentes infrautilizadas

Todas están diseñadas para revisión horaria, con reglas pre-registrables y mecanismos distintos a las ~500 pruebas ya descartadas.

### 4. Consenso de interés abierto entre exchanges (Binance vs. Bybit y OKX)
* **Mecanismo:** Muchas rupturas falsas en Binance nacen de barridos locales o apalancamiento aislado en una sola plaza mientras otros mercados descargan posiciones. Las tendencias sostenibles atraen capital nuevo de forma simultánea en múltiples exchanges.
* **Regla exacta:**
  * **Condición (como filtro sobre tendencia BTC/ETH o como ruptura propia de 48 h en el Top 30):** Al producirse una ruptura horaria, calcular la variación porcentual del OI en las últimas 6 h por separado en **Binance, Bybit y OKX**.
  * **Entrada:** Abrir solo si **al menos 2 de los 3 exchanges** registran una expansión de OI superior a $+1{,}5\%$ en las últimas 6 h.
  * **Salida y stop:** Salida por ruptura inversa de 24 h o *trailing stop* de $2{,}5 \times \text{ATR}_{24h}$.
* **Prueba de falsación:** Comparar las rupturas con consenso ($\ge 2$ exchanges) frente a aquellas donde el OI solo crece en Binance; si el rendimiento medio por operación no mejora de forma significativa, se descarta.

### 5. Choque de posicionamiento Hyperliquid vs. Binance (Efecto "ballenas on-chain")
* **Mecanismo:** No es *carry* entre exchanges (no se abren patas opuestas). Hyperliquid concentra operadores activos y mesas nativas con alto apalancamiento que suelen reaccionar antes que el flujo minorista de Binance. Cuando el *funding* de Hyperliquid diverge bruscamente del de Binance, revela un choque de posicionamiento especializado que tiende a arrastrar al perpetuo de Binance en las horas siguientes.
* **Regla exacta:**
  * **Señal:** Cada hora, para las monedas del Top 30 listadas en ambos exchanges, calcular el diferencial de *funding* normalizado a 8 h:
    $$\Delta F_{i,t} = F_{\text{HL},8h} - F_{\text{Bin},8h}$$
  * **Entrada en Binance:**
    * **Largo** si $\Delta F_{i,t} \ge +0{,}04\%$ durante 3 horas seguidas **y** el retorno de las últimas 6 h en Binance es inferior a $+4\%$ (el movimiento no está agotado).
    * **Corto** si $\Delta F_{i,t} \le -0{,}04\%$ durante 3 horas seguidas **y** el retorno de las últimas 6 h en Binance es superior a $-4\%$.
  * **Salida:** Cuando $|\Delta F_{i,t}| \le 0{,}01\%$ o a las 24 h máximo.
  * **Stop:** $2{,}5 \times \text{ATR}_{24h}$ (techo rígido en 5 %).
* **Prueba de falsación:** Comprobar si usar únicamente $F_{\text{Bin}}$ replica el resultado; el alfa incremental debe proceder del diferencial frente a Hyperliquid.

### 6. Desacople intrasemana de acciones *proxy* (MSTR / COIN) frente a BTC
* **Mecanismo:** Complementario a la reversión de fin de semana en perpetuos de acciones. Entre semana ocurre el flujo contrario: durante la primera hora de Wall Street, fondos de renta variable y mesas de bonos convertibles mueven con fuerza MSTR y COIN, dejando a BTC rezagado varias horas hasta que los flujos de ETF y arbitraje cierran la brecha.
* **Regla exacta:**
  * **Señal:** Una hora después de la apertura de Wall Street (14:30 UTC en horario de verano / 15:30 UTC en invierno; evaluable en el cierre horario de las 15:00 o 16:00 UTC), calcular el retorno en exceso de COIN y MSTR frente a BTC en las últimas 2 horas:
    $$E_t = R_{\text{proxy},2h} - \beta_{30d} \cdot R_{\text{BTC},2h}$$
  * **Entrada:** Si tanto COIN como MSTR muestran el mismo signo de exceso y su media cumple $|E_t| \ge 3{,}0\%$, entrar en **BTCUSDT** en la dirección del exceso.
  * **Salida:** Al cierre de Wall Street (21:00 UTC) o tras un máximo de 6 horas.
  * **Stop:** 2 % rígido en BTCUSDT.
* **Prueba de falsación:** Ejecutar el mismo cálculo a las 04:00 UTC (bolsa estadounidense cerrada); si el rendimiento es equivalente, no responde al flujo bursátil.

### 7. Resaca mecánica post-*funding* extremo (Ventana T+1 h, no pre-cobro)
* **Mecanismo:** Cuando el *funding* alcanza extremos ($\ge +0{,}06\%$ o $\le -0{,}06\%$ por corte de 8 h), entra capital oportunista 1–2 horas antes del cobro solo para capturar el pago y desmontar inmediatamente después. El cierre masivo de estos operadores empuja el precio en sentido contrario durante 1–4 horas si el libro está tenso.
* **Regla exacta:**
  * **Señal:** Evaluar exactamente 1 hora después de cada liquidación (01:00, 09:00 y 17:00 UTC) en el universo Top 30.
  * **Entrada en corto:** Si el *funding* liquidado fue $\le -0{,}06\%$, el interés abierto cayó **al menos un 2 %** en esa primera hora (confirma desarme de cazadores largos) **y** la vela de esa hora cerró en negativo.
  * **Entrada en largo:** Simétrica si el *funding* fue $\ge +0{,}06\%$, el OI cayó al menos un 2 % y la vela post-cobro cerró en positivo.
  * **Salida:** Cierre fijo a las 4 horas o si el precio rompe el extremo opuesto de la vela de la hora del cobro.
  * **Stop:** 2,5 % rígido.
* **Prueba de falsación:** Ejecutar la regla sin el filtro de caída de OI ($\ge 2\%$); sin desarme físico de posiciones no debería manifestarse la resaca mecánica.

### 8. Sensor de choques narrativos en Polymarket hacia perpetuos de Binance
* **Mecanismo:** No consiste en explotar la calibración de Polymarket, sino en utilizarlo como un *feed* cuantificado de eventos con dinero real. Ante catalizadores regulatorios, macroeconómicos (tipos Fed) o judiciales, las probabilidades implícitas en Polymarket suelen ajustarse minutos u horas antes de que los perpetuos de Binance descuenten el movimiento completo.
* **Regla exacta:**
  * **Universo de eventos:** Lista predefinida de mercados de Polymarket con volumen acumulado superior a 5 M USD y signo económico inequívoco sobre BTC, ETH o un token concreto.
  * **Entrada:** En revisión horaria, si la probabilidad implícita salta **al menos 8 puntos porcentuales en 1 hora** (o 12 puntos en 3 h) **y** el perpetuo vinculado en Binance se ha movido **menos de** $0{,}5 \times \text{ATR}_{24h}$ en esa dirección, abrir posición a favor del shock.
  * **Salida:** A las 12 h o si la probabilidad en Polymarket revierte más de la mitad del salto inicial.
  * **Stop:** $1{,}5 \times \text{ATR}_{24h}$.
* **Advertencia de muestra:** La liquidez institucional de Polymarket despega en 2024, impidiendo validar en el bloque 2020–2022; requiere validación prospectiva en vivo con tamaño mínimo antes de asignar peso relevante.

---

## Referencia numérica: impacto de las fricciones (Bloque 1)

Ejemplo ilustrativo para una estrategia horaria con **35 bps** (0,35 %) de ventaja bruta media por operación, **120 operaciones ida y vuelta al año** y una duración media de **2 días** (6 cortes de *funding* a 1,5 bps/8 h = 9 bps de arrastre medio):

| Esquema de ejecución | Coste ejecución (bps) | Arrastre *funding* (bps) | Ventaja neta / op (bps) | Rentabilidad anual estimada |
| :--- | :---: | :---: | :---: | :---: |
| **Bruto (sin fricciones)** | 0,0 | 0,0 | 35,0 | 42,0 % |
| **Taker actual (0,07 %/lado)** | 14,0 | 9,0 | 12,0 | 14,4 % |
| **Maker-Chaser (0,02 %/lado)** | 4,0 | 9,0 | 22,0 | 26,4 % |
| **Maker-Chaser + Stop sangrado (-50 %)** | 4,0 | 4,5 | 26,5 | 31,8 % |

> **Conclusión operativa:** En este perfil de rotación, pasar de ejecución *taker* sin control de *funding* a **Maker-Chaser + Stop de sangrado** recupera **+17,4 puntos porcentuales anuales** sobre el mismo alfa bruto.

---

## Orden práctico de implementación

1. **Inmediato (sobre cartera activa):** Implementar **#1 (Maker-Chaser)**, **#2 (Stop de sangrado)** y **#3 (Ratio OI/Volumen)**; no requieren fuentes externas nuevas y su efecto es auditable directamente en el simulador actual.
2. **Prueba rápida de filtrado:** Evaluar **#4 (Consenso OI Binance/Bybit/OKX)** como filtro adicional sobre la estrategia de tendencia BTC/ETH y el *momentum* de ráfaga de 3 h.
3. **Nuevos motores independientes:** Pre-registrar **#5 (Hyperliquid vs. Binance)**, **#6 (MSTR/COIN intrasemana)** y **#7 (Resaca post-*funding*)** respetando los bloques 2020–2022 y 2023–2026 (y desde el histórico disponible de Hyperliquid a partir de 2023–2024).