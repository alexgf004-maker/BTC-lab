#!/usr/bin/env bash
# Lo ejecuta systemd cada vez que el bot se detiene (ExecStopPost). Si no fue una parada normal, avisa por Telegram
# (como mucho un aviso cada 30 minutos, para no inundar el chat si el bot se reinicia en bucle).
[ "${SERVICE_RESULT:-success}" = "success" ] && exit 0
[ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ] || exit 0
marca=/opt/btclab/datos_bot/.ultima_alerta_caida
ahora=$(date +%s)
if [ -f "$marca" ] && [ $((ahora - $(cat "$marca"))) -lt 1800 ]; then exit 0; fi
echo "$ahora" > "$marca" 2>/dev/null || true
curl -s -m 10 "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=[BTC-lab] ⚠️ El bot se ha detenido por un fallo (${SERVICE_RESULT}, código ${EXIT_STATUS:-?}). systemd lo reinicia en 1 minuto. Detalle: sudo journalctl -u btclab-bot -n 50" >/dev/null || true
exit 0
