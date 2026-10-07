"""Pruebas de las métricas automáticas de evaluación."""

from videoqa.evaluate import citation_hit, is_refusal, retrieval_hit, summarize, to_seconds

NOT_FOUND = "No encuentro esto en el video."


def test_refusal_ignores_case_and_punctuation():
    assert is_refusal("no encuentro esto en el video", NOT_FOUND)
    assert is_refusal("Lo siento. No encuentro esto en el video.", NOT_FOUND)
    assert not is_refusal("La capital de Francia es París.", NOT_FOUND)


def test_retrieval_hit_uses_chunk_range_with_tolerance():
    sources = [{"start": 60.0, "end": 100.0}]
    assert retrieval_hit(sources, to_seconds("01:30"), tolerance=15)
    assert retrieval_hit(sources, to_seconds("01:50"), tolerance=15)
    assert not retrieval_hit(sources, to_seconds("03:00"), tolerance=15)


def test_citation_hit_with_tolerance():
    assert citation_hit([75.0], to_seconds("02:00"), tolerance=60)
    assert not citation_hit([75.0], to_seconds("03:00"), tolerance=60)
    assert not citation_hit([], to_seconds("03:00"), tolerance=60)


def test_summary_reads_values_from_script_and_from_excel():
    rows = [
        {"configuracion": "rag", "latencia_s": "10", "rechazo_correcto": "True", "rechazo_indebido": "",
         "recuperacion_acierta": "", "cita_cercana": "", "correctitud_0a2": "", "fidelidad_0a2": "",
         "alucinacion_si_no": ""},
        {"configuracion": "rag", "latencia_s": "20", "rechazo_correcto": "", "rechazo_indebido": False,
         "recuperacion_acierta": True, "cita_cercana": False, "correctitud_0a2": "2", "fidelidad_0a2": "1",
         "alucinacion_si_no": "sí"},
    ]  # fmt: skip
    [summary] = summarize(rows)
    assert summary["latencia_media_s"] == 15.0
    assert summary["rechazo_correcto_trampas"] == "100% (n=1)"
    assert summary["recuperacion_acierta"] == "100% (n=1)"
    assert summary["cita_cercana"] == "0% (n=1)"
    assert summary["correctitud_media_0a2"] == "2.00 (n=1)"
    assert summary["alucinaciones"] == "100% (n=1)"
