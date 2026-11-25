# Lección 44 — Mejorar las entradas y salidas del bloque B (corto altcoins / largo BTC)

## 1. Pre-registro (antes de calcular resultados)
Base: reglas actuales de B (ratio altcoin/BTC en 4 h, ratio diario bajo su EMA50, ruptura del mínimo de 120 velas, stop dinámico 5 ATR;
1 % de riesgo, máximo 10 posiciones, 30 más líquidas point-in-time; costes 0,14 % por lado y funding real de las dos patas).
Cada variante cambia UNA cosa:
- **Q1 · Filtro de cortos saturados:** no abrir si el funding medio de 3 días de la altcoin < −0,03 % por 8 h (los cortos ya pagan mucho:
  riesgo de "short squeeze"). Es el espejo del filtro de euforia aprobado en D.
- **Q2 · Piramidación:** entrar con la mitad del riesgo y añadir un cuarto cuando el ratio cae 1 ATR y otro cuando cae 2 ATR (mismo stop).
  Mismo riesgo total. Es lo aprobado en D.
- **Q3 · Stop a cero:** cuando la operación gana 1R, el stop no puede quedar por encima de la entrada.
- **Q4 · Salida por tiempo:** si tras 30 velas (5 días) la operación no ha ido nunca 0,5R a favor, se cierra al cierre de esa vela.
**Mitades:** 2020-03 → 2022-12 y 2023-01 → 2026-10 (el criterio es la estabilidad en ambas).
**Criterio:** Sharpe mayor en las dos mitades y caída máxima no mayor que B actual. Pruebas nuevas: 4.

## 2. Resultados — `l44_salida.txt` (la reconstrucción de B reproduce exactamente la serie de la Lección 31: Sharpe 1,56 / 0,82)
| Variante | 2020–2022: Sharpe / anual / caída | 2023–2026: Sharpe / anual / caída | Veredicto |
|---|---|---|---|
| B actual | 1,56 / +71,0 % / 30,4 % | 0,82 / +28,4 % / 33,8 % | |
| Q1 filtro de cortos saturados | 1,41 / +60,8 % / 33,3 % | 0,88 / +31,7 % / 26,0 % | ❌ empeora 2020–22 |
| **Q2 piramidación** | **1,60 / +74,7 % / 26,8 %** | **0,92 / +34,0 % / 24,7 %** | ✅ |
| Q3 stop a cero tras +1R | 1,55 / +70,2 % / 30,3 % | 0,81 / +27,8 % / 34,0 % | ❌ sin efecto |
| Q4 salida por tiempo | 1,42 / +63,2 % / 30,2 % | 0,88 / +32,1 % / 31,7 % | ❌ empeora 2020–22 |
**La piramidación se aprueba también en B** (como en D): mejora el Sharpe en las dos mitades y reduce la caída máxima de 30–34 % a 25–27 %.
Las entradas que fallan enseguida solo arriesgan la mitad; las que funcionan terminan con el riesgo completo.
Mover el stop a cero no aporta (el stop dinámico de 5 ATR ya hace ese trabajo) y cerrar por tiempo corta algunas ganadoras lentas.
~~Activado en el bot~~ → **retirado; ver la corrección del apartado 3.**

## 3. Corrección: con ejecución realista, la piramidación NO mejora B — `l44_salida_realista.txt`
La simulación anterior ejecutaba cada añadido **exactamente en su precio de activación**. El bot revisa B cada 4 h y añade **al cierre de
la vela**, a menudo bastante más lejos. La comprobación con el código del bot (25 monedas, 2022–2024) dio menos saldo final con
piramidación (6 108 $ frente a 7 557 $), y la simulación repetida con añadidos al cierre de la vela confirma el problema:
| | 2020–2022: Sharpe / anual / caída | 2023–2026: Sharpe / anual / caída |
|---|---|---|
| B actual | 1,56 / +71,0 % / 30,4 % | 0,82 / +28,4 % / 33,8 % |
| Piramidación con añadidos al cierre de la vela | 1,40 / +61,9 % / 27,8 % | 0,67 / +21,1 % / 32,5 % |
**Q2 queda RECHAZADA.** El ratio altcoin/BTC se mueve a saltos: al añadir tarde se compra peor y se pierde la ventaja.
En D sí se mantiene, porque allí la mejora se confirmó directamente con el código del bot (que ya añade al precio real).
**Lección de método:** las suposiciones de ejecución "en el precio exacto" pueden fabricar mejoras que no existen.
