#!/usr/bin/env bash
# Comprueba si el VPS sirve para el bot. No instala ni cambia nada. Uso: bash deploy/comprobar_vps.sh
ok=1
say() { printf "%-42s %s\n" "$1" "$2"; }
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1"; }
v=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "no")
say "Python 3.10 o superior" "$v"; python3 -c 'import sys; sys.exit(sys.version_info < (3,10))' 2>/dev/null || ok=0
say "Memoria libre (MB)" "$(free -m 2>/dev/null | awk '/Mem:/{print $7}')   (recomendado ≥ 700)"
say "Disco libre en / (GB)" "$(df -BG / | awk 'NR==2{print $4}')   (recomendado ≥ 2)"
say "Reloj sincronizado (NTP)" "$(timedatectl show -p NTPSynchronized --value 2>/dev/null || echo 'desconocido')"
for u in "https://fapi.binance.com/fapi/v1/ping|API de futuros de Binance" "https://api.binance.com/api/v3/ping|API spot/margen de Binance" \
         "https://testnet.binancefuture.com/fapi/v1/ping|Testnet de futuros" "https://api.telegram.org|Telegram (avisos)"; do
  c=$(code "${u%%|*}"); m="${u##*|}"
  case "$c" in
    200|302|404) say "$m" "OK ($c)";;
    451|403) say "$m" "BLOQUEADO ($c): Binance no permite operar desde la región de este VPS"; [[ "$m" == API* ]] && ok=0;;
    *) say "$m" "sin respuesta ($c)"; [[ "$m" == API* ]] && ok=0;;
  esac
done
echo; [ $ok = 1 ] && echo "✅ El VPS sirve para el bot." || echo "❌ Hay problemas: revisa las líneas marcadas antes de instalar."
