# Lección 57 — ¿Qué tienen en común las operaciones perdedoras del bloque J?

Pregunta del usuario: J acierta el ~70 % pero pierde ~18 % cuando falla frente a ~7,5 % que gana cuando acierta. ¿Hay algo, al
entrar, que avise de que una operación será perdedora?

## 1. Pre-registro (subido antes de calcular)
Operaciones: regla J actual (stop 2 ATR). **Búsqueda solo en el top 30** (6.455 operaciones, L54). **Validación en los puestos
31–100** (13.657 operaciones, L55), que no se miran hasta haber elegido el filtro.

Variables candidatas (medidas al cierre del día de la ruptura, sin mirar al futuro):
1. Tamaño de la ruptura: distancia del cierre al nivel, en % (p. ej. BTW cerró un 18 % por encima de 1,00 $).
2. Tamaño de la ruptura en ATR.
3. Volatilidad: ATR(14) diario / precio.
4. Volumen del día de la ruptura frente a la media de 20 días.
5. Tendencia: cierre frente a la media de 50 días, en la dirección de la ruptura.
6. Rentabilidad de los 30 días previos, en la dirección de la ruptura.
7. Mercado: rentabilidad de BTC en 7 días, en la dirección de la ruptura.
8. Antigüedad de la moneda (días desde su primer dato).
9. Funding medio de 3 días, en la dirección de la ruptura (largos pagando → ruptura alcista "cargada").
10. Dirección de la ruptura (alcista → corto; bajista → largo).

Procedimiento: en el top 30, terciles de cada variable; para cada una, acierto, pérdida media y resultado medio por tercil. Se elige
**como mucho un filtro** (quitar un tercil extremo de una sola variable), el de mayor mejora del resultado medio en el top 30,
siempre que el patrón sea monótono (los tres terciles en orden).
**Criterio de validación** (puestos 31–100): el filtro mejora el resultado medio de J en desarrollo (2020–2022) **y** examen
(2023 → 2026-10), y deja J con media positiva en los dos. Si no, no se aplica.
