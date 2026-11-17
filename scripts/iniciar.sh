#!/usr/bin/env bash
# Arranque del bot en Linux/macOS. Uso: ./scripts/iniciar.sh
set -e
cd "$(dirname "$0")/.."
[ -f bot/config.yaml ] || { cp bot/config.example.yaml bot/config.yaml; echo "Creado bot/config.yaml (modo paper). Revísalo y vuelve a ejecutar."; exit 0; }
python3 -m pip install -q -r requirements.txt
python3 -m pytest -q tests || { echo "Las pruebas fallan: no se arranca."; exit 1; }
exec python3 -m bot.main --config bot/config.yaml
