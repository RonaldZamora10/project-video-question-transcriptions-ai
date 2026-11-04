"""Limpieza del texto transcrito (Etapa 4 de la metodología del Entregable 1).

La limpieza es conservadora: solo quita sonidos de duda ("eh", "mmm") y palabras repetidas por error de Whisper
("que que"). Las muletillas con significado ("pues", "bueno") se cuentan para el análisis, pero no se borran.
"""

import re
from collections import Counter

_REPEATED_WORD = re.compile(r"\b(\w+)(?:\s+\1\b)+", re.IGNORECASE)
_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([,.;:!?])")
_WORD = re.compile(r"\w+")


def _phrase_pattern(phrases: list[str]) -> re.Pattern:
    """Expresión que encuentra cualquiera de las frases como palabra completa (las más largas primero)."""
    alternatives = "|".join(re.escape(phrase) for phrase in sorted(phrases, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)


def clean_text(text: str, hesitations: list[str]) -> str:
    """Quita sonidos de duda y palabras repetidas, y normaliza los espacios."""
    without_hesitations = re.sub(_phrase_pattern(hesitations).pattern + r"[,.]?", "", text, flags=re.IGNORECASE)
    without_repeats = _REPEATED_WORD.sub(r"\1", without_hesitations)
    single_spaced = " ".join(without_repeats.split())
    return _SPACE_BEFORE_PUNCTUATION.sub(r"\1", single_spaced).strip(" ,")


def count_words(text: str) -> int:
    return len(_WORD.findall(text))


def count_fillers(text: str, fillers: list[str]) -> Counter:
    """Cuántas veces aparece cada muletilla en el texto."""
    return Counter(match.lower() for match in _phrase_pattern(fillers).findall(text))
