"""Pruebas de la generación de respuestas, con Ollama simulado (no necesitan red ni modelos)."""

import pytest

from videoqa import answer
from videoqa.answer import build_context, extract_citations

TRANSCRIPT = {
    "segments": [
        {"start": 0.0, "end": 5.0, "text": "Las matemáticas son para siempre."},
        {"start": 75.0, "end": 80.0, "text": "Un teorema no caduca."},
    ]
}
FAKE_OLLAMA_RESPONSE = {
    "message": {"role": "assistant", "content": "Porque un teorema no caduca [01:15]."},
    "total_duration": 2_500_000_000,
    "prompt_eval_count": 120,
    "eval_count": 12,
}


def test_full_context_has_every_segment_with_its_minute():
    context = build_context("completo", TRANSCRIPT, [])
    assert context == "[00:00] Las matemáticas son para siempre.\n[01:15] Un teorema no caduca."


def test_rag_context_is_sorted_by_time():
    sources = [{"start": 75.0, "end": 80.0, "text": "B"}, {"start": 0.0, "end": 5.0, "text": "A"}]
    assert build_context("rag", TRANSCRIPT, sources) == "[00:00 - 00:05] A\n\n[01:15 - 01:20] B"


def test_extract_citations_returns_unique_seconds():
    assert extract_citations("Dice X [01:15] y también [00:07]. Repite [01:15].") == [7, 75]


def test_extract_citations_understands_ranges_and_ignores_times_outside_brackets():
    # Caso real: Llama 3.2 citó "[04:55 - 05:41]". Una hora suelta (10:30) no es una cita.
    assert extract_citations("Son eternos [04:55 - 05:41]. A las 10:30 llegó.") == [295, 341]


def test_answer_question_full_mode_uses_ollama_response(monkeypatch):
    sent = {}

    def fake_chat(messages):
        sent["messages"] = messages
        return FAKE_OLLAMA_RESPONSE

    monkeypatch.setattr(answer, "chat", fake_chat)
    result = answer.answer_question("¿Por qué son para siempre?", "completo", TRANSCRIPT)

    assert result.text == "Porque un teorema no caduca [01:15]."
    assert result.citations == [75]
    assert result.latency_seconds == 2.5
    assert "No encuentro esto en el video." in sent["messages"][0]["content"]
    assert "[01:15] Un teorema no caduca." in sent["messages"][1]["content"]


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        answer.answer_question("hola", "otro", TRANSCRIPT)


def test_connection_error_has_clear_message(monkeypatch):
    monkeypatch.setattr(answer.urllib.request, "urlopen", _raise_connection_refused)
    with pytest.raises(ConnectionError, match="Ollama"):
        answer.chat([{"role": "user", "content": "hola"}])


def _raise_connection_refused(*args, **kwargs):
    raise answer.urllib.error.URLError("conexión rechazada")
