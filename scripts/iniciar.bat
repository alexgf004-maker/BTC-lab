@echo off
REM Arranque del bot en Windows. Uso: doble clic o "scripts\iniciar.bat" desde la carpeta BTC-lab
cd /d "%~dp0\.."
if not exist bot\config.yaml (copy bot\config.example.yaml bot\config.yaml & echo Creado bot\config.yaml (modo paper). Revisalo y vuelve a ejecutar. & pause & exit /b)
python -m pip install -q -r requirements.txt
python -m pytest -q tests || (echo Las pruebas fallan: no se arranca. & pause & exit /b 1)
python -m bot.main --config bot\config.yaml
pause
