"""Pruebas del resumen que alimenta la página de comparación de modelos."""

import pandas as pd

from videoqa.report import outcome, summarize


def _row(model, kind, refused_ok="", refused_wrong="", citation="", latency="10"):
    return {
        "modelo": model,
        "configuracion": "rag",
        "tipo": kind,
        "rechazo_correcto": refused_ok,
        "rechazo_indebido": refused_wrong,
        "cita_cercana": citation,
        "latencia_s": float(latency),
    }


def test_summarize_computes_percentages_per_model():
    results = pd.DataFrame(
        [
            _row("a", "trampa", refused_ok="True", latency="4"),
            _row("a", "trampa", refused_ok="False", latency="6"),
            _row("a", "normal", refused_wrong="False", citation="True", latency="8"),
            _row("a", "normal", refused_wrong="True", citation="False", latency="10"),
            _row("b", "normal", refused_wrong="no", citation="sí", latency="3"),  # calificado a mano en Excel
        ]
    )

    summary = summarize(results).set_index("modelo")

    assert summary.loc["a", "no_inventa"] == 50
    assert summary.loc["a", "responde_si_sabe"] == 50
    assert summary.loc["a", "cita_correcta"] == 50
    assert summary.loc["a", "confiabilidad"] == 50
    assert summary.loc["a", "latencia_mediana_s"] == 7.0
    assert pd.isna(summary.loc["b", "no_inventa"])  # sin trampas: no se inventa un valor
    assert summary.loc["b", "confiabilidad"] == 100


def test_outcome_in_plain_words():
    assert outcome(pd.Series(_row("a", "trampa", refused_ok="False"))) == "Inventó una respuesta"
    assert outcome(pd.Series(_row("a", "normal", refused_wrong="True"))) == "Dijo que no estaba"
    assert outcome(pd.Series(_row("a", "normal", refused_wrong="False", citation="True"))) == "Respondió y citó bien"
