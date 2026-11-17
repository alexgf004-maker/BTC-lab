# Guía del bot de BTC-lab

## 1. Qué hace
Ejecuta en vivo las piezas validadas en la investigación (ver `docs/INFORME_FINAL.md`):

| Bloque | Capital | Qué hace | Frecuencia |
|---|---|---|---|
| A Carry | 23,75 % | largo spot + corto perpetuo cuando el funding es alto | cada 8 h (00, 08, 16 UTC) |
| E Carry inverso | 23,75 % | largo perpetuo + corto spot prestado cuando el funding es muy negativo | cada 8 h |
| B Corto de altcoins débiles | 23,75 % | corto altcoin + largo BTC al romper a la baja su ratio | velas de 4 h; salidas vigiladas cada hora |
| D Tendencia BTC/ETH | 23,75 % | largo en rupturas de 20 días con stop dinámico (stop real en el exchange) | velas de 4 h |
| F Fin de semana (candidata) | 5 % | contra el movimiento del fin de semana en perpetuos de acciones de EE. UU. | domingo 21:00 → lunes 03:00 UTC |

## 2. Verificación (paridad con el backtest)
El bot se ejecutó hora a hora sobre los datos históricos, sin ver el futuro, y se comparó con el backtest:
- Tendencia BTC/ETH, 2020–2026: **120 de 120 operaciones idénticas** (entrada, salida, precios y stop).
- Corto de altcoins (muestra de 26 monedas, 2023): **101 de 101** (más 2 por el arranque en vacío).
- Carry inverso (53 monedas, 2020–2026): **251 de 251 episodios**; rentabilidad por episodio con correlación 0,99.
- Carry (53 monedas): 59 de 62 episodios; diferencia mediana de rentabilidad +0,09 %.
Scripts: `bot/paridad/`. Pruebas automáticas: `python -m pytest -q tests` (11 pruebas).
Durante la verificación se encontraron y corrigieron tres errores del bot: funding contado dos veces, pata spot al precio del perpetuo
y dos bloques con el mismo identificador.

## 3. Instalación (en tu ordenador o en un VPS)
Requisitos: Python 3.11+, conexión a Binance desde un país permitido (la API de Binance bloquea algunas regiones; cumple la normativa de tu país).
```bash
git clone https://github.com/alexgf004-maker/BTC-lab.git && cd BTC-lab
pip install -r requirements.txt pyyaml requests
cp bot/config.example.yaml bot/config.yaml      # y edítalo
```
Datos históricos: no son necesarios para operar; el bot descarga lo que necesita de la API.

## 4. Claves de la API (nunca en ficheros ni en el chat)
1. Crea las claves en Binance (o en testnet.binancefuture.com para pruebas).
2. Permisos: **lectura y trading de futuros** (y spot y margen si usas A y E). **NUNCA permiso de retirada.**
3. Restringe la clave a la IP de tu ordenador o VPS.
4. Pásalas como variables de entorno antes de arrancar:
```bash
export BINANCE_API_KEY="..."        # Windows PowerShell:  $env:BINANCE_API_KEY="..."
export BINANCE_API_SECRET="..."
```

## 5. Fases recomendadas
| Fase | `modo` | Duración | Qué se comprueba |
|---|---|---|---|
| 1. Simulación con datos reales | `paper` | 2–4 semanas | que las señales y el diario coinciden con lo esperado; sin dinero ni claves |
| 2. Testnet de futuros | `testnet` | 1–2 semanas | envío de órdenes, stops en el exchange, redondeos (A y E se desactivan: el testnet no tiene spot ni margen) |
| 3. Real pequeño | `live` | 1–3 meses | ejecución real, préstamo para el carry inverso, deslizamiento; capital que puedas permitirte perder |
| 4. Escalar | `live` | — | solo si el real se parece a lo esperado (≈ 15–20 % anual, caídas ≈ 10 %) |

## 6. Ejecución
```bash
python -m bot.main --config bot/config.yaml            # bucle continuo: un ciclo cada hora en punto + 2 min
python -m bot.main --config bot/config.yaml --once     # un solo ciclo (para cron o el programador de tareas)
python -m bot.main --config bot/config.yaml --status   # estado sin operar
```
En un VPS Linux, para que siga tras reiniciar: un servicio de systemd o `cron` con `--once` a los 2 minutos de cada hora.
Ficheros generados (en `datos_bot/`): `estado.json` (posiciones; sobrevive a reinicios sin duplicar), `diario.csv` (cada decisión y ejecución)
y `bot.log`.

## 7. Seguridad y límites conocidos
- **Freno de riesgo:** aviso con una caída del 15 % desde el máximo; **parada total con un 25 %** (solo una persona la reactiva,
  editando `halted` en `estado.json` tras revisar).
- Tendencia: el stop vive en el exchange (STOP_MARKET de solo reducción) → protegido aunque el bot se caiga.
- Corto de altcoins: el stop es sobre un ratio y no se puede dejar en el exchange; el bot lo vigila cada hora.
  Si el bot está caído, esas posiciones quedan sin vigilancia: usa un VPS estable.
- Carry: cuando el precio sube un 20 % el bot **avisa** en el diario para reponer margen en la pata corta (todavía manual).
- Carry inverso: antes de entrar comprueba en vivo cuánto se puede pedir prestado y el interés real; si no hay préstamo, no entra.
- Pendiente: notificaciones al móvil (Telegram), traspasos automáticos de margen entre cuentas, y reconciliación completa
  de posiciones con el exchange al arrancar.
