# Lección 1c — Riesgo por trade: el 3 %

Monte Carlo (20 000 simulaciones de 300 trades, interés compuesto) para dos estrategias
**buenas** netas de costes (`lecciones/leccion_01c_riesgo.py`):

| Perfil | Riesgo | DD máx. típico | DD en un mal escenario (p95) | P(DD > 30 %) | P(DD > 50 %) | Retorno mediano |
|---|---|---|---|---|---|---|
| Alto WR (58 %, PF 1,26) | 1 % | 11 % | 19 % | 0 % | 0 % | +37 % |
| Alto WR | 3 % | **30 %** | **48 %** | **48 %** | 4 % | +136 % |
| Tendencia (38 %, PF 1,49) | 1 % | 14 % | 24 % | 1 % | 0 % | +110 % |
| Tendencia | 3 % | **38 %** | **58 %** | **83 %** | 14 % | +619 % |

Rachas de pérdidas esperables (p95): 9 seguidas (alto WR), 16 seguidas (tendencia).
Con un 3 % de riesgo, 16 pérdidas seguidas son un −39 %.

## Matiz importante
Estas cifras **suponen que la ventaja es real**. En la práctica el rendimiento en real
suele ser peor que el del backtest. Si la ventaja resulta ser nula, un 3 % por trade
destruye la cuenta mucho más rápido que un 1 %.

## Decisión
- El riesgo es un parámetro: `RISK_MAX = 3 %`, elegido por el usuario.
- Por fases: validación en testnet (riesgo indiferente) → real con 1 % durante los
  primeros 50–100 trades → 3 % solo si el real se parece al backtest.
- **Corta-circuitos por drawdown**: con DD > 15 % el riesgo baja a la mitad; con DD > 30 %
  el bot se detiene y revisamos.
- Apalancamiento implícito = riesgo / stop. Con un 3 % y un stop del 1,5 % (típico en 4h)
  son 2x nocionales; la liquidación queda muy lejos si se usa margen aislado con apalancamiento ≤ 5x.
