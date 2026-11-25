# Lección 44 — Mejorar las entradas y salidas del bloque B (corto altcoins / largo BTC)

## 1. Pre-registro (antes de calcular resultados)
Base: reglas actuales de B (ratio altcoin/BTC en 4 h, ratio diario bajo su EMA50, ruptura del mínimo de 120 velas, stop dinámico 5 ATR;
1 % de riesgo, máximo 10 posiciones, 30 más líquidas point-in-time; costes 0,14 % por lado y funding real de las dos patas).
Cada variante cambia UNA cosa:
- **Q1 · Filtro de cortos saturados:** no abrir si el funding medio de 3 días de la altcoin < −0,03 % por 8 h (los cortos ya pagan mucho:
  riesgo de "short squeeze"). Es el espejo del filtro de euforia aprobado en D.
- **Q2 · Piramidación:** entrar con la mitad del riesgo y añadir un cuarto cuando el ratio cae 1 ATR y otro cuando cae 2 ATR (mismo stop).
  Mismo riesgo total. Es lo aprobado en D.
- **Q3 · Stop a cero:** cuando la operación gana 1R, el stop no puede quedar por encima de la entrada.
- **Q4 · Salida por tiempo:** si tras 30 velas (5 días) la operación no ha ido nunca 0,5R a favor, se cierra al cierre de esa vela.
**Mitades:** 2020-03 → 2022-12 y 2023-01 → 2026-10 (el criterio es la estabilidad en ambas).
**Criterio:** Sharpe mayor en las dos mitades y caída máxima no mayor que B actual. Pruebas nuevas: 4.
