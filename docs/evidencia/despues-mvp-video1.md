# Evidencia del "después": MVP con las mismas preguntas del código base

Fecha: 2026-10-06. Mismo equipo (CPU, sin GPU) y mismo video: `01_matematicas` (10:19).
Durante esta prueba se estaban transcribiendo otros videos en paralelo, así que **las latencias están infladas** y no son
las definitivas; las oficiales salen de `python -m videoqa.evaluate`.

Configuración: Whisper `small` (int8, `language="es"`), fragmentos de ~120 palabras con tiempos (16 en este video),
embeddings `multilingual-e5-base`, ChromaDB, Llama 3.2 3B con `temperature: 0` y `seed: 42`.

## Transcripción
- Whisper `small`: 238 s para 619 s de audio (2,6 veces más rápido que el video).
- Corrige errores del modelo `base` del código original: "tú en que trabajas", "le dices soy matemático".
- Sigue fallando en nombres propios: "tomás hails" (Thomas Hales), "weyrey felan" (Weaire-Phelan),
  "teorema del panel" (teorema del panal).

## Respuestas (comparación directa con `antes-codigo-base.md`)

| Pregunta | Código base | MVP — A (RAG) | MVP — B (transcripción completa) |
|---|---|---|---|
| ¿Por qué dice el autor que las matemáticas son para siempre? | ❌ "El autor **no dice** que son para siempre" | ✅ "sus resultados son eternos, como el teorema de Pitágoras… incluso después de la muerte de Pitágoras" [04:55 - 05:41] | ⚠️ Parcial: habla de "lógica propia" y "rigor"; cita [03:51] |
| ¿Qué es un teorema según el video? | Razonable, sin cita | ✅ "una verdad eterna… que se puede demostrar", **sin cita** | ✅ igual, con cita [06:15] |
| ¿Cuál es la capital de Francia? (trampa) | ❌ "¡París!" | ✅ "No encuentro esto en el video." | ✅ "No encuentro esto en el video." |

Tokens de entrada: A ≈ 800–950, B ≈ 2.730 (cabe holgado en `num_ctx: 8192`).

## Prueba desde la interfaz web
Pregunta: "¿Qué pasaría si se dobla 50 veces una hoja de papel?" (configuración A).
Respuesta: "el grosor del papel ocuparía la distancia de la tierra al sol" [04:19 - 05:06], 28,9 s.
El botón "04:19" llevó el reproductor al segundo 259, que es el punto citado.

## Lectura honesta
- Se corrigió el problema principal: el sistema ya no responde con conocimiento propio.
- En esta muestra pequeña, A fue más preciso que B en la pregunta central. Con 3 preguntas no se puede generalizar;
  la comparación formal se hace con el banco de preguntas completo.
- El modelo no siempre cita el minuto aunque el prompt lo pide (una de seis respuestas no citó).
