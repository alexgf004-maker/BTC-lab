# scalping-lab

Investigación rigurosa (y didáctica) de estrategias de scalping en Binance USDⓈ-M Futures,
con el objetivo final de ejecutarlas de forma automática.

## Método (no se salta ninguna fase)
1. Mercado y costes reales  ← **Lección 1 (hecha)**
2. Hipótesis de ventaja (por qué debería funcionar)
3. Reglas 100 % mecánicas
4. Backtest con costes realistas
5. Robustez: fuera de muestra, walk-forward, Monte Carlo, sensibilidad
6. Paper trading en testnet
7. Real con capital mínimo, límites de riesgo y kill switch

## Criterios de aprobación (fijados ANTES de ver resultados)
- PF neto ≥ 1,3 fuera de muestra
- ≥ 300 trades fuera de muestra
- Mayoría de ventanas walk-forward positivas
- Sin dependencia de un valor exacto de parámetro

## Uso
```bash
pip install -r requirements.txt
python lecciones/leccion_01_costes.py   # descarga previa: ver sclab/data.py
```

## Estructura
- `sclab/data.py` descarga y carga de velas (data.binance.vision)
- `sclab/costs.py` comisiones VIP0 y fórmulas de coste en R
- `sclab/backtest.py` motor conservador (entrada en la vela siguiente, SL primero si hay ambigüedad)
- `lecciones/` un script por lección; `docs/` conclusiones y resultados
