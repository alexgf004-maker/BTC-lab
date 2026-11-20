# Guía del bot de BTC-lab

## 1. Qué hace
Ejecuta en vivo las piezas validadas en la investigación (ver `docs/INFORME_FINAL.md`):

| Bloque | Capital | Qué hace | Frecuencia |
|---|---|---|---|
| A Carry | 23,75 % | largo spot + corto perpetuo cuando el funding es alto (3 huecos + 25 % de reserva de margen) | cada 8 h (00, 08, 16 UTC) |
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

## 2b. Corrección importante descubierta al construir el bot
El backtest del carry normal suponía margen ilimitado para reponer la pata corta. Con el capital real del bloque, en las grandes
subidas (2020–21) no hay margen suficiente y hay que reducir posiciones. Rentabilidad ejecutable (211 monedas, 2020–2026):
**+3,6 % anual** frente al +15,9 % del backtest. El carry inverso sí se mantiene (+2,6 % frente a +2,8 % por episodio).
Cartera recalculada: 10 000 $ de 2020 → **56 734 $** (x5,7, +29,7 % anual, caída máxima 9,5 %); con descuento: **23 387 $** (+13,6 % anual).

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
2. Permisos: **lectura, trading de futuros**, y si usas A y E: **spot y margen** y **transferencia universal** (solo mueve dinero
   entre TUS cuentas de Binance: spot, margen y futuros). **NUNCA permiso de retirada.**
3. Restringe la clave a la IP de tu ordenador o VPS.
4. Pásalas como variables de entorno antes de arrancar:
```bash
export BINANCE_API_KEY="..."        # Windows PowerShell:  $env:BINANCE_API_KEY="..."
export BINANCE_API_SECRET="..."
```

## 4b. Avisos por Telegram (opcional, recomendado)
1. En Telegram, habla con **@BotFather** → `/newbot` → te da un *token*.
2. Escribe cualquier mensaje a tu bot nuevo y abre `https://api.telegram.org/bot<TOKEN>/getUpdates` en el navegador: el número
   `"chat":{"id": ...}` es tu *chat id*.
3. Variables de entorno: `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
Recibirás: arranque, cada entrada y salida, errores, reajustes de margen, descuadres, avisos de caída y un resumen diario a las 08:00 UTC.

## 5. Fases recomendadas
| Fase | `modo` | Duración | Qué se comprueba |
|---|---|---|---|
| 1. Simulación con datos reales | `paper` | 2–4 semanas | que las señales y el diario coinciden con lo esperado; sin dinero ni claves |
| 2. Testnet de futuros | `testnet` | 1–2 semanas | envío de órdenes, stops en el exchange, redondeos (A y E se desactivan: el testnet no tiene spot ni margen) |
| 3. Real pequeño | `live` | 1–3 meses | ejecución real, préstamo para el carry inverso, deslizamiento; capital que puedas permitirte perder |
| 4. Escalar | `live` | — | solo si el real se parece a lo esperado (≈ 15–20 % anual, caídas ≈ 10 %) |

## 5b. Instalación en un VPS (junto a otros servicios)
El bot se instala en `/opt/btclab` con su propio usuario (`btclab`), su propio entorno de Python y su propio servicio (`btclab-bot`):
no toca ningún otro proyecto del VPS ni usa puertos.
```bash
git clone https://github.com/alexgf004-maker/BTC-lab.git /tmp/btclab && cd /tmp/btclab
bash deploy/comprobar_vps.sh          # 1) ¿Binance permite operar desde aquí? ¿Python, memoria, reloj?
sudo bash deploy/instalar_vps.sh      # 2) instala (sin arrancar)
sudo -u btclab nano /opt/btclab/bot/config.yaml      # 3) modo: paper para empezar
sudo nano /etc/btclab/entorno                        # 4) Telegram (y más adelante las claves); permisos 600
sudo systemctl enable --now btclab-bot               # 5) arrancar y que arranque solo al reiniciar el VPS
sudo journalctl -u btclab-bot -f                     # ver lo que hace en directo
sudo -u btclab /opt/btclab/.venv/bin/python -m bot.main --config /opt/btclab/bot/config.yaml --status
```
Actualizar: `sudo bash /opt/btclab/deploy/instalar_vps.sh && sudo systemctl restart btclab-bot` (conserva `config.yaml`, el estado y el entorno).
Parar: `sudo systemctl stop btclab-bot`. El servicio limita la memoria a 1,5 GB y solo puede escribir en `/opt/btclab`.
Si `comprobar_vps.sh` muestra **BLOQUEADO (451)**, Binance no permite operar desde la región del VPS: hace falta otro VPS en una
región permitida (y cumplir la normativa de tu país).

## 5c. Paso a modo real (dinero real)

1. **Clave de la API en Binance** (Perfil → Gestión de API → Crear API → generada por el sistema). Permisos:
   lectura, trading spot y margen, margen (préstamo/devolución), futuros y transferencia universal.
   **Nunca el permiso de retirada.** Restringe la clave a la IP del VPS.
2. **Futuros → Preferencias → Modo de posición: Unidireccional (One-way).** Activa también las cuentas de futuros y de margen.
3. **Reparte los USDT** entre las cuentas: ~55 % en futuros USDⓈ-M, ~25 % en spot y ~20 % en margen cruzado.
4. En el VPS: `sudo nano /etc/btclab/entorno` (las claves) y `sudo -u btclab nano /opt/btclab/bot/config.yaml`
   (`modo: live` y `capital:` igual o algo inferior al USDT total).
5. Actualiza: `sudo bash /opt/btclab/deploy/instalar_vps.sh`.
6. Comprobación previa (solo lee): `sudo bash /opt/btclab/deploy/comprobar_live.sh`. Si hay ❌, no arranques.
7. Arranca: `sudo systemctl enable --now btclab-bot` y vigila con `sudo journalctl -u btclab-bot -f` y Telegram.

El bot se niega a arrancar si encuentra un estado de otro modo (por ejemplo, de una prueba en paper).
Si una pata de una cobertura falla, deshace la otra. Si una orden no llega al mínimo de Binance, la omite y lo anota.

## 5d. Panel web de monitoreo
`sudo bash /opt/btclab/deploy/instalar_panel.sh` instala una página de **solo lectura** con capital, curva, bloques, posiciones y
últimos eventos. HTTPS con certificado gratuito y automático (dirección `https://<ip-con-guiones>.sslip.io`) y contraseña generada
por el instalador (`sudo cat /etc/btclab/panel_contrasena`). El panel escucha solo en 127.0.0.1; Caddy pone el HTTPS y la contraseña delante.
Vigilancia: si el bot se detiene por un fallo, systemd avisa por Telegram (`deploy/alerta_caida.sh`, máx. un aviso cada 30 min);
y si el servicio no está activo o lleva más de 2 h 15 min sin completar un ciclo, el panel avisa (y vuelve a avisar al recuperarse).

## 5e. Bloque G en prueba (Lección 40)
Motor A del BTC-Strategy-Monitor (ráfaga de momentum en BTC, ETH y SOL), el único de esa suite que funciona fuera de BTC.
**Siempre simulado**, aunque el bot esté en modo real (usa el bróker simulado), y **no cuenta en el capital** ni en la caída de la cartera:
el panel y los avisos lo marcan "EN PRUEBA". Paridad comprobada con el monitor (281 operaciones idénticas) y entre la versión hora a hora
y la réplica histórica (54 de 54 en 2024). Se activa solo; para desactivarlo: `G_rafaga: {activo: false}` en config.yaml.

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
- **Margen del carry (automático):** si el precio se mueve un 20 %, la pata que pierde recibe USDT de la reserva del bloque mediante una
  transferencia interna; si no hay reserva, el bot reduce las dos patas y traspasa lo liberado. En el carry inverso se protegen las dos
  direcciones (la pata prestada sufre con las subidas). Además, si el margen de mantenimiento de futuros supera el 35 % del saldo,
  el bot trae USDT de spot hasta dejarlo en el 20 %.
- **Comparación con el exchange (cada hora en testnet y real):** compara las posiciones del estado con las reales (perpetuos, spot y
  préstamos). Si algo no cuadra, avisa y **bloquea nuevas entradas en ese símbolo** hasta que lo revises y lo borres de `bloqueados` en
  `estado.json`. También vuelve a colocar los stops de la tendencia que falten.
- Carry inverso: antes de entrar comprueba en vivo cuánto se puede pedir prestado y el interés real; si no hay préstamo, no entra.
- Arranque rápido: `./scripts/iniciar.sh` (Linux/macOS) o `scripts\iniciar.bat` (Windows): crea la configuración la primera vez,
  pasa las pruebas y arranca. Por defecto en modo `paper` (sin dinero).
