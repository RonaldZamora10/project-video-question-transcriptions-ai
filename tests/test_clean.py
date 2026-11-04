"""Pruebas de la limpieza de texto."""

from videoqa.clean import clean_text, count_fillers, count_words

HESITATIONS = ["eh", "em", "mmm"]
FILLERS = ["pues", "o sea", "bueno"]


def test_removes_hesitations_and_keeps_meaning():
    assert clean_text("Eh, las matemáticas mmm son para siempre", HESITATIONS) == "las matemáticas son para siempre"


def test_collapses_words_repeated_by_whisper():
    assert clean_text("y que que pasa con con el teorema", HESITATIONS) == "y que pasa con el teorema"


def test_does_not_touch_words_that_contain_a_hesitation():
    # "tema" contiene "em" y "ehecatl" empieza por "eh": no deben modificarse.
    assert clean_text("el tema de Ehecatl", HESITATIONS) == "el tema de Ehecatl"


def test_normalizes_spaces_before_punctuation():
    assert clean_text("hola   ,  mundo .", HESITATIONS) == "hola, mundo."


def test_counts_multiword_fillers_without_double_counting():
    counts = count_fillers("Pues, o sea, bueno... o sea que pues sí", FILLERS)
    assert counts == {"pues": 2, "o sea": 2, "bueno": 1}


def test_count_words_ignores_punctuation():
    assert count_words("¿Qué es un teorema? Una verdad, eterna.") == 7
