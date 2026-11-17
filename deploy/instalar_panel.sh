#!/usr/bin/env bash
# Panel web del bot con HTTPS (certificado gratuito y automático) y contraseña.
# Uso:  sudo bash /opt/btclab/deploy/instalar_panel.sh
set -euo pipefail
DIR=/opt/btclab
[ -d "$DIR/bot" ] || { echo "❌ Primero instala el bot (deploy/instalar_vps.sh)."; exit 1; }

# 1) dirección pública: IP del droplet → nombre <ip-con-guiones>.sslip.io (resuelve a esa IP; permite un certificado real)
IP=$(curl -s -m 3 http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address || true)
[ -n "$IP" ] || IP=$(curl -s -4 -m 10 https://api.ipify.org)
HOST="${IP//./-}.sslip.io"

# 2) Caddy (servidor web con HTTPS automático)
if ! command -v caddy >/dev/null; then
  apt-get update -q >/dev/null
  if ! DEBIAN_FRONTEND=noninteractive apt-get install -y -q caddy >/dev/null 2>&1; then   # repositorio oficial de Caddy
    DEBIAN_FRONTEND=noninteractive apt-get install -y -q debian-keyring debian-archive-keyring apt-transport-https gnupg >/dev/null
    curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -q >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y -q caddy >/dev/null
  fi
fi

# 3) contraseña (se genera una vez; se guarda solo para root)
PWFILE=/etc/btclab/panel_contrasena
if [ ! -f "$PWFILE" ]; then
  openssl rand -base64 24 | tr -d '/+=' | cut -c1-16 > "$PWFILE"
fi
chmod 600 "$PWFILE"; chown root:root "$PWFILE"
PW=$(cat "$PWFILE")
HASH=$(caddy hash-password --plaintext "$PW")

cat > /etc/caddy/Caddyfile <<CADDY
$HOST {
	basicauth {
		btclab $HASH
	}
	header {
		Strict-Transport-Security "max-age=31536000"
		-Server
	}
	reverse_proxy 127.0.0.1:8090
}
CADDY

# 4) cortafuegos (solo si ufw está activo): abrir 80 (para el certificado) y 443
if ufw status 2>/dev/null | grep -q "Status: active"; then ufw allow 80/tcp >/dev/null; ufw allow 443/tcp >/dev/null; fi

# 5) servicios
cp "$DIR/deploy/btclab-panel.service" /etc/systemd/system/btclab-panel.service
systemctl daemon-reload
systemctl enable --now btclab-panel >/dev/null 2>&1
systemctl restart btclab-panel
systemctl enable caddy >/dev/null 2>&1
systemctl restart caddy
sleep 8
echo
if curl -s -m 20 -o /dev/null -w "%{http_code}" -u "btclab:$PW" "https://$HOST/salud" | grep -q 200; then
  echo "✅ Panel listo"
else
  echo "⏳ El certificado puede tardar 1-2 minutos la primera vez. Si no carga, mira: sudo journalctl -u caddy -n 30"
fi
echo "   Dirección:  https://$HOST"
echo "   Usuario:    btclab"
echo "   Contraseña: $PW"
echo "   (para volver a verla: sudo cat $PWFILE)"
