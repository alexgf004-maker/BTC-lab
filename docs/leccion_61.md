# Lección 61 — ¿Le conviene un stop de emergencia al bloque I (prima de Coinbase)?

El bloque I (en seguimiento) no tiene stop: cada 4 h decide largo / corto / fuera según la prima de Coinbase (L47, CP4).
Pregunta del usuario: ¿no debería tener stop loss?

## 1. Pre-registro (subido antes de calcular)
Misma regla y datos que la L47 (CP4). Variantes con stop de emergencia revisado con velas de 1 h desde el precio de entrada:
**S2** −2 %, **S3** −3 %, **S5** −5 %. Tras saltar el stop, no se vuelve a entrar en la misma dirección hasta que la señal pase
por neutral o cambie de signo. Costes 0,07 % por lado + funding.
Criterio: Sharpe mayor que I sin stop en desarrollo (2020–2022) **y** examen (2023 → 2026-10), y caída máxima no mayor.
Pruebas nuevas: 3.
