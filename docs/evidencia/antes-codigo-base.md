# Evidencia del "antes": código base sin modificar

Fecha: 2026-10-06. Equipo: 16 GB RAM, Intel i5-1135G7, sin GPU (todo en CPU).

## Cómo se corrió
- Código de `vaibhav07772/multi-agent-rag-local-ai` **sin modificar** (`rag_pipeline.py`, `agents.py`).
- Única diferencia: la descarga de YouTube (bloqueada en la red de prueba) se reemplazó por el archivo local
  `data/videos/01_matematicas.mp4` (Sáenz de Cabezón, 10:19), transcrito con el mismo `whisper_model` del código base.
- Modelo: `llama3.2:3b` con el alias `llama3`, que es el nombre fijo que usa el código base.

## Problemas encontrados antes de poder correrlo
- `requirements.txt` no incluye `langchain-text-splitters`: el código base no arranca tal como viene.
- La versión estable de `yt-dlp` (2026.08.19) no lee ted.com; la versión preliminar 2026.09.27 sí.

## Resultados
Transcripción (Whisper `base`, sin idioma fijo): **173 s**, **1.408 palabras**. Hay errores visibles, por ejemplo
"sale en la conversación y **tuven que trabajas**" y "**le hice** soy matemático".

| Pregunta | Respuesta del sistema (resumida) | Latencia | Diagnóstico |
|---|---|---|---|
| ¿Por qué dice el autor que las matemáticas son para siempre? | "El autor **no dice** que las matemáticas son para siempre… son una herramienta…" | 67 s | **Incorrecta**: contradice el título y la tesis de la charla |
| ¿Qué es un teorema según el video? | "Una verdad eterna… sigue siendo válida aunque el que la propuso ya no esté vivo" | 32 s | Razonable, pero **sin minuto citado** |
| ¿Cuál es la capital de Francia? (pregunta trampa) | "¡Hola! Me alegra ayudarte… La capital de Francia es… ¡París!" | 18 s | **Responde fuera del video**: usa conocimiento propio en vez de decir que no está en el video |

## Defectos técnicos observados
- Errores `UnicodeDecodeError` (cp1252) al leer la salida de `ollama run` por `subprocess` en Windows.
- Texto con caracteres dañados ("matemÃ¡ticas") y códigos de control de la terminal mezclados en la respuesta.
- No cita minutos, el prompt está en inglés y el índice se reconstruye en cada pregunta.

## Conclusión
El código base contesta, pero **no es fiel al video**: falla la pregunta central de la charla y responde la pregunta trampa con
conocimiento propio. Esto motiva los cambios del proyecto: prompt restrictivo en español, citas `mm:ss`, Whisper con
`language="es"` y evaluación de alucinaciones.
