#!/usr/bin/env bash
# Comprobación previa al modo real (solo lee, no envía órdenes).  Uso:  sudo bash /opt/btclab/deploy/comprobar_live.sh
set -euo pipefail
cd /opt/btclab
set -a; . /etc/btclab/entorno; set +a
sudo --preserve-env=BINANCE_API_KEY,BINANCE_API_SECRET -u btclab .venv/bin/python -m bot.preflight --config bot/config.yaml
