#!/usr/bin/env bash
# Quita BTC-Strategy-Monitor del VPS: servicio, archivos, usuario, runner de GitHub Actions y tareas cron que lo lanzaban.
# Uso (como root):  bash deploy/quitar_monitor.sh
# No toca nada de BTC-lab. Antes de borrar, muestra lo que encontró y pide confirmación.
set -uo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Ejecútalo como root."; exit 1; }

echo "== Buscando restos del monitor =="
svc=$(systemctl list-unit-files --type=service --no-legend 2>/dev/null | awk '{print $1}' | grep -x "btc-strategy-monitor.service" || true)
runners=$(systemctl list-unit-files --type=service --no-legend 2>/dev/null | awk '{print $1}' | grep -i "actions.runner" | grep -i "strategy-monitor" || true)
dirs=""; for d in /opt/btc-strategy-monitor /var/lib/btc-strategy-monitor; do [ -e "$d" ] && dirs="$dirs $d"; done
envf=""; [ -e /etc/btc-strategy-monitor.env ] && envf=/etc/btc-strategy-monitor.env
usr=""; id btcmonitor &>/dev/null && usr=btcmonitor
runner_dirs=""
for r in $runners; do
  exe=$(systemctl show -p ExecStart --value "$r" 2>/dev/null | grep -o 'path=[^ ;]*' | head -1 | cut -d= -f2)
  [ -n "$exe" ] && runner_dirs="$runner_dirs $(dirname "$exe")"
done
crons=""
for u in root $(cut -d: -f1 /etc/passwd); do
  l=$(crontab -l -u "$u" 2>/dev/null | grep -n -i -E "strategy-monitor|paper-monitor|workflow_dispatch|monitor\.runner" || true)
  [ -n "$l" ] && crons="$crons\n  [$u] $l"
done
cronfiles=$(grep -l -i -E "strategy-monitor|paper-monitor|workflow_dispatch" /etc/cron.d/* 2>/dev/null || true)

echo "  servicio del monitor:        ${svc:-(no encontrado)}"
echo "  runner(s) de GitHub Actions: ${runners:-(no encontrado)}"
echo "  carpetas del runner:         ${runner_dirs:-(—)}"
echo "  carpetas del monitor:        ${dirs:-(no encontradas)}"
echo "  fichero de entorno:          ${envf:-(no encontrado)}"
echo "  usuario:                     ${usr:-(no encontrado)}"
echo -e "  tareas cron:                 ${crons:-(ninguna)}"
echo "  ficheros en /etc/cron.d:     ${cronfiles:-(ninguno)}"
echo
if [ -z "$svc$runners$dirs$envf$usr$crons$cronfiles" ]; then echo "No queda nada del monitor. ✅"; exit 0; fi
read -r -p "¿Borrar todo lo anterior? Escribe SI en mayúsculas para continuar: " ok
[ "$ok" = "SI" ] || { echo "Cancelado. No se ha tocado nada."; exit 0; }

[ -n "$svc" ] && { systemctl disable --now btc-strategy-monitor.service; rm -f /etc/systemd/system/btc-strategy-monitor.service; echo "✔ servicio del monitor parado y eliminado"; }
for r in $runners; do systemctl disable --now "$r"; rm -f "/etc/systemd/system/$r"; echo "✔ runner $r parado y eliminado"; done
for d in $runner_dirs; do [ -d "$d" ] && [ -f "$d/config.sh" ] && rm -rf "$d" && echo "✔ carpeta del runner $d eliminada"; done
for d in $dirs; do rm -rf "$d"; echo "✔ $d eliminado"; done
[ -n "$envf" ] && rm -f "$envf" && echo "✔ $envf eliminado"
for u in root $(cut -d: -f1 /etc/passwd); do
  if crontab -l -u "$u" 2>/dev/null | grep -q -i -E "strategy-monitor|paper-monitor|workflow_dispatch|monitor\.runner"; then
    crontab -l -u "$u" | grep -v -i -E "strategy-monitor|paper-monitor|workflow_dispatch|monitor\.runner" | crontab -u "$u" - && echo "✔ tareas cron del monitor quitadas ($u)"
  fi
done
for f in $cronfiles; do rm -f "$f"; echo "✔ $f eliminado"; done
[ -n "$usr" ] && userdel btcmonitor 2>/dev/null && echo "✔ usuario btcmonitor eliminado"
systemctl daemon-reload
echo
echo "✅ Monitor eliminado del VPS. Falta un paso en GitHub (en el navegador):"
echo "   BTC-Strategy-Monitor → Settings → Actions → Runners → borra el runner que aparezca como 'Offline'"
echo "   BTC-Strategy-Monitor → Actions → 'BTC paper monitor' → botón '…' → Disable workflow"
