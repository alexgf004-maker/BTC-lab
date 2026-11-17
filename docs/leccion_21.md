# Lección 21 — Robustez de las cuatro piezas aprobadas

## 1. Pre-registro (las rejillas NO sirven para elegir parámetros: los de la cartera no cambian)
Se mide si cada pieza funciona en una región amplia de parámetros (mecanismo) o solo en el valor elegido (espejismo).
- **A carry** (211 monedas con spot): umbral de entrada {0,010; 0,015; 0,020; 0,030} % por 8h × salida {0; 0,005; 0,010} %.
- **E carry inverso** (~700 criptos, reglas de realismo, interés 30 %): mismas 12 combinaciones.
- **B S1** (~700 criptos): ruptura N ∈ {60, 90, 120, 180, 240} velas de 4h × chandelier m ∈ {3, 4, 5, 6}.
- **D tendencia BTC/ETH:** las mismas 20 combinaciones.
Criterio de robustez: ≥ 75 % de las combinaciones con Sharpe > 0,5 y la combinación de la cartera no es la mejor por un margen > 50 %.
Además: **capacidad** (capital máximo si cada operación no supera el 1 % del volumen diario de la moneda) y **comportamiento en cada crisis**.

## 2. Sensibilidad de parámetros — `l21_rejillas.csv`, `l21_salida_resumen.txt`
| Pieza | Combinaciones | Sharpe > 0,5 | Sharpe mediano | Rango | El de la cartera | Lectura |
|---|---|---|---|---|---|---|
| A carry | 12 | 100 % | 4,62 | 3,74–5,05 | 4,69 | robusta |
| E carry inverso | 12 | 100 % | 4,53 | 4,35–4,69 | 4,47 | robusta (muy estable) |
| B S1 corto alt/BTC | 20 | 100 % | 1,30 | 0,98–1,45 | 1,13 | robusta; el elegido está **por debajo** de la mediana (estimación conservadora) |
| D tendencia BTC/ETH | 20 | 80 % | **0,68** | 0,25–1,06 | **1,06** | el elegido es **el mejor** de la rejilla: su Sharpe está sobrestimado; esperar ≈ 0,7 |

Nota sobre el criterio: "el de la cartera no supera al mejor en más de un 50 %" no detecta el caso en que el elegido ES el mejor.
D pasa formalmente, pero se recalcula la cartera con la expectativa mediana en la Lección 22.

## 3. Crisis — `l21_salida_crisis_capacidad.txt`
| Episodio | A carry | B S1 | D tendencia | E carry inverso | **Cartera** | BTC |
|---|---|---|---|---|---|---|
| Crash de mayo 2021 (China) | +0,7 % | +0,4 % | −2,8 % | −0,6 % | **−0,5 %** | −33,5 % |
| Colapso de LUNA | 0,0 % | +18,0 % | 0,0 % | +1,2 % | **+4,8 %** | −23,6 % |
| 3AC / Celsius | 0,0 % | +10,2 % | 0,0 % | +0,3 % | **+2,6 %** | −33,4 % |
| Quiebra de FTX | 0,0 % | +1,7 % | −3,3 % | +3,7 % | **+0,5 %** | −20,7 % |
| Deshacer del carry del yen (ago. 2024) | 0,0 % | +14,5 % | 0,0 % | −0,1 % | **+3,5 %** | −5,9 % |
| Desplome del 10-oct-2025 | −0,1 % | +8,0 % | −2,8 % | +0,5 % | **+1,6 %** | −5,1 % |
| Año 2022 completo | +0,2 % | +160,1 % | −16,5 % | +13,1 % | **+27,7 %** | −64,2 % |
| 2026 hasta octubre | 0,0 % | −27,3 % | −9,2 % | +73,8 % | **+4,9 %** | −11,5 % |

**En ninguna de las seis crisis agudas la cartera perdió más de un 0,5 %.** S1 actúa como seguro en los desplomes (las altcoins caen
más que BTC) y el carry inverso en los periodos de miedo prolongado. La tendencia es la única pieza que sufre en las crisis.

## 4. Capacidad (cada operación ≤ 1 % del volumen diario de la moneda)
| Pieza | Nocional por posición | Capital máximo: mediana | p25 | p10 |
|---|---|---|---|---|
| S1 (examen) | 11,3 % del capital | 2,8 M$ | 1,1 M$ | 0,36 M$ |
| Carry inverso (nuevas) | 16,7 % | 0,6 M$ | 0,37 M$ | 0,26 M$ |
| Carry inverso (antiguas) | 16,7 % | 3,6 M$ | 1,6 M$ | 0,76 M$ |
Para cuentas de hasta ~250 000 $ la capacidad no es una restricción; por encima, habría que limitar el carry inverso a monedas grandes.
