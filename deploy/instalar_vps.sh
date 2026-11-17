#!/usr/bin/env bash
# Instalación en un VPS Linux (Debian/Ubuntu) junto a otros servicios, sin tocarlos.
# Uso (como root o con sudo):  sudo bash deploy/instalar_vps.sh
set -euo pipefail
REPO="https://github.com/alexgf004-maker/BTC-lab.git"
DIR=/opt/btclab
id btclab &>/dev/null || useradd --system --create-home --home-dir /var/lib/btclab --shell /usr/sbin/nologin btclab
apt-get update -q >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y -q python3-venv git curl >/dev/null
if [ -d "$DIR/.git" ]; then sudo -u btclab git -C "$DIR" pull -q; else git clone -q "$REPO" "$DIR" && chown -R btclab:btclab "$DIR"; fi
sudo -u btclab python3 -m venv "$DIR/.venv"
sudo -u btclab "$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt" pytest
[ -f "$DIR/bot/config.yaml" ] || sudo -u btclab cp "$DIR/bot/config.example.yaml" "$DIR/bot/config.yaml"
mkdir -p /etc/btclab
if [ ! -f /etc/btclab/entorno ]; then
  cat > /etc/btclab/entorno <<'ENV'
# Claves y avisos del bot. Este fichero solo lo puede leer root (permisos 600).
# En modo paper no hacen falta las claves de Binance.
BINANCE_API_KEY=
BINANCE_API_SECRET=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
ENV
fi
chmod 600 /etc/btclab/entorno; chown root:root /etc/btclab/entorno
(cd "$DIR" && sudo -u btclab .venv/bin/python -m pytest -q tests) || { echo "❌ Las pruebas fallan: no se instala el servicio."; exit 1; }
cp "$DIR/deploy/btclab-bot.service" /etc/systemd/system/btclab-bot.service
systemctl daemon-reload
echo
echo "✅ Instalado en $DIR (usuario btclab, servicio btclab-bot). Aún NO está arrancado."
echo "   1) Revisa la configuración:      sudo -u btclab nano $DIR/bot/config.yaml   (modo: paper)"
echo "   2) Claves / Telegram (opcional): sudo nano /etc/btclab/entorno"
echo "   3) Arrancar y activar al inicio: sudo systemctl enable --now btclab-bot"
echo "   4) Ver lo que hace:              sudo journalctl -u btclab-bot -f"
