# Preguntas y respuestas sobre videos con IA local

Proyecto de la asignatura **Sistemas Inteligentes** — Universidad ECCI.

El sistema transcribe una charla en español, la indexa y responde preguntas en lenguaje natural **usando solo lo que se
dijo en el video**, indicando el minuto de donde sale cada respuesta. Si la respuesta no está en el video, lo dice.
Todo se ejecuta en el computador del usuario, sin servicios de pago.

Pregunta problema: *¿es posible construir un sistema basado en LLM que, a partir de la transcripción automática de un
video, responda con precisión y fidelidad las preguntas en lenguaje natural de un usuario?*

## Equipo

| Integrante | Rol |
|---|---|
| _Por definir_ | |
| _Por definir_ | |
| _Por definir_ | |
| _Por definir_ | |

## Cómo funciona

```
video ─► Whisper (texto con minutos) ─► limpieza ─► fragmentos ─► embeddings e5 ─► ChromaDB
                                                                                     │
pregunta ─► embedding ─► fragmentos más parecidos ─► Llama 3.2 3B (Ollama) ─► respuesta con [mm:ss]
```

Se comparan dos configuraciones:

- **A — Con recuperación (RAG):** el modelo solo recibe los fragmentos más relacionados con la pregunta.
- **B — Sin recuperación:** el modelo recibe la transcripción completa.

## Estructura

```
app.py              Interfaz web (Streamlit)
config.yaml         Toda la configuración: modelos, rutas y parámetros
videoqa/            Código del sistema
tests/              Pruebas automáticas (no necesitan internet ni modelos)
data/videos.yaml    Catálogo de los 8 videos del dataset
data/transcripts/   Transcripciones generadas (forman parte del dataset)
docs/               Entregables, decisiones técnicas y evidencias
```

## Instalación (Windows)

Requisitos: Python 3.11, [Ollama](https://ollama.com) y unos 6 GB libres en disco.

```bash
py -3.11 -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt
ollama pull llama3.2:3b
```

Los videos no se suben al repositorio por su tamaño: se guardan en `data/videos/` con el nombre del `id` del catálogo
(por ejemplo `data/videos/01_matematicas.mp4`).

## Pruebas

```bash
python -m pytest
python -m ruff check .
```

## Créditos y licencias

- Este proyecto parte del código de [vaibhav07772/multi-agent-rag-local-ai](https://github.com/vaibhav07772/multi-agent-rag-local-ai)
  (licencia MIT, se conserva en `LICENSE`). Del original se reescribió todo el flujo: transcripción en español con
  minutos, limpieza, fragmentación por segmentos, índice persistente, prompt restrictivo con citas, configuración B y
  evaluación. La evidencia del comportamiento original está en `docs/evidencia/antes-codigo-base.md`.
- Modelo de lenguaje: **Llama 3.2** de Meta, bajo la *Llama 3.2 Community License*. Built with Llama.
- Transcripción: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) con modelos Whisper de OpenAI (MIT).
- Embeddings: [intfloat/multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base) (MIT).
- Videos: charlas TED y TEDx, licencia CC BY-NC-ND 4.0; se usan con fines académicos y no se redistribuyen.
