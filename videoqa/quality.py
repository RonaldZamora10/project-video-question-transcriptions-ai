"""Análisis de calidad de las transcripciones (objetivo específico 1 del Entregable 1).

Uso:
    python -m videoqa.quality --fetch-references   # una sola vez: baja los subtítulos humanos de TED (requiere yt-dlp)
    python -m videoqa.quality                      # genera data/analisis/calidad_<modelo>.csv y muestra el resumen

Para cada video calcula: palabras reales, palabras por minuto, muletillas cada 100 palabras, palabras quitadas por la
limpieza y, si hay subtítulos de TED, el error de palabras (WER) de Whisper. Ese WER es APROXIMADO: los subtítulos de
TED están editados (quitan repeticiones y muletillas), así que no son una transcripción literal.
"""

import argparse
import csv
import re
from pathlib import Path

import jiwer

from videoqa.clean import count_fillers, count_words
from videoqa.config import load_catalog, load_config, project_path
from videoqa.transcribe import load_transcript

_VTT_NOISE = re.compile(r"^(WEBVTT|NOTE|\d+$)|-->")
_TAGS_AND_SOUNDS = re.compile(r"<[^>]+>|\([^)]*\)|\[[^\]]*\]")  # etiquetas y anotaciones como "(Aplausos)"
_NON_WORD = re.compile(r"[^\w\s]")


def read_vtt(path: Path) -> str:
    """Extrae solo el texto hablado de un archivo de subtítulos .vtt."""
    lines = path.read_text(encoding="utf-8").splitlines()
    spoken = [line for line in lines if line.strip() and not _VTT_NOISE.search(line.strip())]
    return _TAGS_AND_SOUNDS.sub(" ", " ".join(spoken))


def normalize_for_wer(text: str) -> str:
    """Minúsculas y sin puntuación: el WER debe medir palabras, no signos."""
    return " ".join(_NON_WORD.sub(" ", text.lower()).split())


def word_error_rate(reference: str, hypothesis: str) -> float:
    return jiwer.wer(normalize_for_wer(reference), normalize_for_wer(hypothesis))


def reference_path(video_id: str) -> Path:
    return project_path("references") / f"{video_id}.es.vtt"


def fetch_references() -> None:
    """Descarga los subtítulos en español publicados por TED (solo para las charlas alojadas en ted.com)."""
    import yt_dlp  # dependencia de desarrollo: solo se necesita para esta descarga única

    folder = project_path("references")
    folder.mkdir(parents=True, exist_ok=True)
    for video in load_catalog():
        if "ted.com" not in video["url"]:
            continue
        options = {
            "writesubtitles": True,
            "subtitleslangs": ["es"],
            "subtitlesformat": "vtt",
            "skip_download": True,
            "quiet": True,
            "noprogress": True,
            "outtmpl": {"default": str(folder / video["id"])},
        }
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([video["url"]])
        except yt_dlp.utils.DownloadError as error:
            print(f"{video['id']}: no se pudieron bajar los subtítulos ({error})")
            continue
        print(f"{video['id']}: {'subtítulos guardados' if reference_path(video['id']).exists() else 'sin subtítulos'}")


def analyze(model_size: str) -> list[dict]:
    settings = load_config()
    rows = []
    for video in load_catalog():
        transcript = load_transcript(video["id"], model_size)
        if transcript is None:
            continue
        clean = " ".join(segment["text"] for segment in transcript["segments"])
        raw = " ".join(segment["raw"] for segment in transcript["segments"])
        words = count_words(clean)
        minutes = transcript["duration_seconds"] / 60
        fillers = count_fillers(raw, settings["cleaning"]["fillers"])
        reference = reference_path(video["id"])
        rows.append(
            {
                "id": video["id"],
                "minutos": round(minutes, 1),
                "palabras": words,
                "palabras_estimadas_150ppm": round(minutes * settings["analysis"]["estimated_words_per_minute"]),
                "palabras_por_minuto": round(words / minutes),
                "muletillas_cada_100": round(100 * sum(fillers.values()) / words, 1),
                "muletillas_frecuentes": ", ".join(f"{name} ({n})" for name, n in fillers.most_common(3)),
                "palabras_quitadas_limpieza": count_words(raw) - words,
                "wer_aprox_vs_ted": round(word_error_rate(read_vtt(reference), raw), 3) if reference.exists() else "",
                "segundos_transcripcion": transcript["transcription_seconds"],
                "veces_tiempo_real": round(transcript["duration_seconds"] / transcript["transcription_seconds"], 1),
            }
        )
    return rows


def save_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Análisis de calidad de las transcripciones.")
    parser.add_argument("--model", help="tamaño de Whisper a analizar (por defecto, el de config.yaml)")
    parser.add_argument("--fetch-references", action="store_true", help="bajar los subtítulos de TED y terminar")
    args = parser.parse_args()

    if args.fetch_references:
        fetch_references()
        return

    model_size = args.model or load_config()["whisper"]["model"]
    rows = analyze(model_size)
    if not rows:
        print(f"No hay transcripciones con '{model_size}'. Ejecuta antes: python -m videoqa.transcribe --all")
        return
    output = project_path("reports") / f"calidad_{model_size}.csv"
    save_csv(rows, output)

    for row in rows:
        print(row)
    total = sum(row["palabras"] for row in rows)
    estimate = load_config()["analysis"]["corpus_estimate_words"]
    print(f"\nPalabras reales del corpus: {total} | estimadas en el Entregable 1: {estimate}")
    print(f"Diferencia: {total - estimate:+} palabras")
    print(f"Tabla guardada en {output}")


if __name__ == "__main__":
    main()
