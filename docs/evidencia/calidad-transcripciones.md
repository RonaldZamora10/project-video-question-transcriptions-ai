# Calidad de las transcripciones (Whisper `small`, int8, CPU)

Fuente: `python -m videoqa.quality` → `data/analisis/calidad_small.csv`. Estado: **5 de 8 videos** transcritos
(faltan 06, 07 y 08: `python -m videoqa.transcribe --all` los completa sin repetir los existentes).

| Video | Min | Palabras | Estimadas (150 ppm) | Palabras/min | WER aprox. vs TED |
|---|---|---|---|---|---|
| 01 Matemáticas | 10,3 | 1.428 | 1.547 | 138 | — (sin subtítulos TED) |
| 02 Privacidad | 16,2 | 2.532 | 2.424 | 157 | — (sin subtítulos TED) |
| 03 Cocina | 13,3 | 1.872 | 1.989 | 141 | 15,0 % |
| 04 Música | 15,8 | 1.727 | 2.369 | 109 | 10,6 % |
| 05 Alta mar | 12,7 | 1.816 | 1.907 | 143 | 13,8 % |
| **Total** | **68,3** | **9.375** | **10.236** | | |

## Hallazgos
- **El corpus real es un 8,4 % menor que lo estimado** en el Entregable 1 (150 palabras/min). El video de música está
  muy por debajo (109 ppm) porque tiene fragmentos orquestales sin voz.
- **WER aproximado entre 10,6 % y 15,0 %.** Es una cota pesimista: los subtítulos de TED están editados (quitan
  repeticiones y muletillas), así que parte de la "diferencia" no es error de Whisper. Aun así es peor que el ~5 % que
  el Entregable cita para `large-v3`, lo cual es esperable con un modelo más pequeño.
- **Errores típicos:** nombres propios (*"tomás hails"* por Thomas Hales, *"weyrey felan"* por Weaire-Phelan,
  *"Maler"* por Mahler, *"vicí"* por Debussy) y palabras poco comunes (*"teorema del panel"* por panal).
- **Muletillas:** muy pocas (menos de 1 cada 100 palabras): son charlas ensayadas. La limpieza casi no quitó palabras.
- **Velocidad:** 01 = 2,6× tiempo real; 02 = 2,1×; 03 = 1,1× (con el procesador compartido con otras pruebas).
  **Los tiempos de 04 y 05 (~6.000 s) no son válidos:** el equipo probablemente se suspendió durante la transcripción y
  el cronómetro siguió contando. Para el informe, medir de nuevo con el equipo dedicado.

## Pendiente
Comparar con `medium` en un solo video (decisión abierta nº 1) si el tiempo lo permite.
