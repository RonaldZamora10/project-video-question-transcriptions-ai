"""Generación de respuestas (Etapa 10 del Entregable 1) con Llama 3.2 vía la API HTTP de Ollama.

Dos configuraciones, según el Entregable 1 §6.2:
    "rag"      (A) el modelo recibe solo los fragmentos recuperados más parecidos a la pregunta.
    "completo" (B) el modelo recibe la transcripción completa, sin recuperación.

API de Ollama usada: POST /api/chat con "stream": false y "options" (temperature, seed, num_ctx).
Fuente: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion
"""

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from chromadb.api.models.Collection import Collection

from videoqa.config import load_config
from videoqa.index import retrieve
from videoqa.transcribe import format_timestamp

MODES = {"rag": "A — Con RAG (fragmentos relevantes)", "completo": "B — Transcripción completa (sin RAG)"}
_BRACKETS = re.compile(r"\[([^\]]*)\]")
_TIMESTAMP = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_NANOSECONDS = 1e9

SYSTEM_PROMPT = """Eres un asistente que responde preguntas sobre un video.
Usa ÚNICAMENTE la transcripción que se te entrega. Reglas:
1. Responde en español, de forma breve y directa.
2. Usa solo información que esté en la transcripción. No uses conocimiento propio aunque conozcas la respuesta.
3. Después de cada afirmación, cita entre corchetes el minuto de donde la tomaste, por ejemplo [03:15].
4. Si la transcripción no contiene la respuesta, responde exactamente: "{not_found}"
"""


@dataclass
class Answer:
    text: str
    mode: str
    citations: list[float]  # segundos citados en la respuesta, para saltar a ese punto del video
    latency_seconds: float
    prompt_tokens: int
    output_tokens: int
    sources: list[dict] = field(default_factory=list)  # fragmentos recuperados (solo configuración A)


def build_context(mode: str, transcript: dict, sources: list[dict]) -> str:
    """Texto que recibe el modelo: fragmentos recuperados (A) o la transcripción completa (B), siempre con minutos."""
    if mode == "rag":
        ordered = sorted(sources, key=lambda chunk: chunk["start"])  # en orden cronológico se lee mejor
        return "\n\n".join(
            f"[{format_timestamp(c['start'])} - {format_timestamp(c['end'])}] {c['text']}" for c in ordered
        )
    return "\n".join(f"[{format_timestamp(s['start'])}] {s['text']}" for s in transcript["segments"])


def extract_citations(text: str) -> list[float]:
    """Minutos citados entre corchetes, como [03:15] o [04:55 - 05:41], en segundos y sin repetir."""
    return sorted(
        {
            int(minutes) * 60 + int(seconds)
            for inside in _BRACKETS.findall(text)
            for minutes, seconds in _TIMESTAMP.findall(inside)
        }
    )


def chat(messages: list[dict]) -> dict:
    """Llama a Ollama y devuelve la respuesta completa (texto y estadísticas de tiempo/tokens)."""
    settings = load_config()["llm"]
    payload = {
        "model": settings["model"],
        "messages": messages,
        "stream": False,
        "options": {"temperature": settings["temperature"], "seed": settings["seed"], "num_ctx": settings["num_ctx"]},
    }
    request = urllib.request.Request(
        f"{settings['base_url']}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=settings["timeout_seconds"]) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise ConnectionError(
            f"No se pudo conectar con Ollama en {settings['base_url']}. Verifica que Ollama esté abierto. ({error})"
        ) from error


def answer_question(question: str, mode: str, transcript: dict, collection: Collection | None = None) -> Answer:
    if mode not in MODES:
        raise ValueError(f"Modo desconocido: {mode}. Usa uno de {list(MODES)}")
    settings = load_config()
    sources = retrieve(collection, question, settings["retrieval"]["top_k"]) if mode == "rag" else []
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(not_found=settings["llm"]["not_found_answer"])},
        {
            "role": "user",
            "content": f"Transcripción:\n{build_context(mode, transcript, sources)}\n\nPregunta: {question}",
        },
    ]
    response = chat(messages)
    text = response["message"]["content"].strip()
    return Answer(
        text=text,
        mode=mode,
        citations=extract_citations(text),
        latency_seconds=round(response["total_duration"] / _NANOSECONDS, 2),
        prompt_tokens=response.get("prompt_eval_count", 0),
        output_tokens=response.get("eval_count", 0),
        sources=sources,
    )
