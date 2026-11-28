# Lección 61 — ¿Le conviene un stop de emergencia al bloque I (prima de Coinbase)?

El bloque I (en seguimiento) no tiene stop: cada 4 h decide largo / corto / fuera según la prima de Coinbase (L47, CP4).
Pregunta del usuario: ¿no debería tener stop loss?

## 1. Pre-registro (subido antes de calcular)
Misma regla y datos que la L47 (CP4). Variantes con stop de emergencia revisado con velas de 1 h desde el precio de entrada:
**S2** −2 %, **S3** −3 %, **S5** −5 %. Tras saltar el stop, no se vuelve a entrar en la misma dirección hasta que la señal pase
por neutral o cambie de signo. Costes 0,07 % por lado + funding.
Criterio: Sharpe mayor que I sin stop en desarrollo (2020–2022) **y** examen (2023 → 2026-10), y caída máxima no mayor.
Pruebas nuevas: 3.

## 2. Resultados — `l61_salida.txt`
| Variante | Desarrollo: Sharpe / anual / caída | Examen: Sharpe / anual / caída |
|---|---|---|
| I sin stop (actual; reproduce la L47) | +0,51 / +23,0 % / 48,6 % | +0,83 / +24,6 % / 36,5 % |
| S2 stop −2 % | +0,31 / +11,5 % / 59,5 % | +0,30 / +7,9 % / 32,7 % |
| S3 stop −3 % | +0,15 / +6,0 % / 56,9 % | +0,49 / +13,8 % / 35,6 % |
| S5 stop −5 % | +0,19 / +8,0 % / 53,4 % | +0,80 / +23,8 % / 36,5 % |

**Rechazados los tres.** Un stop fijo saca a I de posiciones que la señal todavía sostiene y empeora el resultado (incluso la caída,
en 2020–22). La revisión cada 4 h ya funciona como salida. Lo que sí queda claro: I, sin stop y con todo el bloque invertido, tuvo
caídas de hasta el 49 % en la historia. Si algún día pasara a la cartera, el control debería ser el **tamaño** (menos capital), no
un stop.
