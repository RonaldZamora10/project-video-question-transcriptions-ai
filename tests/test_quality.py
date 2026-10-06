"""Pruebas del análisis de calidad de transcripciones."""

from videoqa.quality import normalize_for_wer, read_vtt, word_error_rate

VTT = """WEBVTT

1
00:00:01.373 --> 00:00:04.635
Si saltaran al azar
en cualquier punto del mar

00:00:04.635 --> 00:00:06.629
hoy, <i>seguramente</i>, verían algo así. (Aplausos)
"""


def test_read_vtt_keeps_only_spoken_text(tmp_path):
    path = tmp_path / "charla.es.vtt"
    path.write_text(VTT, encoding="utf-8")
    expected = "si saltaran al azar en cualquier punto del mar hoy seguramente verían algo así"
    assert normalize_for_wer(read_vtt(path)) == expected


def test_wer_ignores_case_and_punctuation():
    assert word_error_rate("Hoy, seguramente, verían algo así.", "hoy seguramente verían algo así") == 0


def test_wer_counts_one_wrong_word_out_of_four():
    assert word_error_rate("las matemáticas son eternas", "las matemáticas son externas") == 0.25
