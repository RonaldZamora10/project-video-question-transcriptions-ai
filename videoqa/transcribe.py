"""Transcripción de videos con faster-whisper, guardando el minuto de cada frase.

Uso desde la terminal:
    python -m videoqa.transcribe --all                 # los 8 videos del catálogo
    python -m videoqa.transcribe 01_matematicas        # uno o varios por id
    python -m videoqa.transcribe --all --model medium  # otro tamaño de Whisper (para comparar)

Cada video produce data/transcripts/<modelo>/<id>.json (segmentos con tiempos) y <id>.txt (lectura humana).
Si la transcripción ya existe no se repite, salvo con --force.
"""

import argparse
import json
import time
from pathlib import Path

from faster_whisper import WhisperModel

from videoqa.clean import clean_text
from videoqa.config import find_video_file, load_catalog, load_config, project_path


def format_timestamp(seconds: float) -> str:
    """Convierte segundos en el formato mm:ss que se usa en las citas."""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def transcript_path(video_id: str, model_size: str | None = None) -> Path:
    model_size = model_size or load_config()["whisper"]["model"]
    return project_path("transcripts") / model_size / f"{video_id}.json"


def load_whisper(model_size: str | None = None) -> WhisperModel:
    # Uso en CPU con int8 tomado del README oficial: https://github.com/SYSTRAN/faster-whisper#faster-whisper
    settings = load_config()["whisper"]
    return WhisperModel(
        model_size or settings["model"], device=settings["device"], compute_type=settings["compute_type"]
    )


def transcribe_file(model: WhisperModel, media_path: Path) -> dict:
    """Transcribe un archivo de audio o video y devuelve los segmentos limpios con sus tiempos."""
    settings = load_config()
    started = time.perf_counter()
    segments, info = model.transcribe(
        str(media_path),
        language=settings["whisper"]["language"],
        beam_size=settings["whisper"]["beam_size"],
        vad_filter=settings["whisper"]["vad_filter"],
    )
    # `segments` es un generador: la transcripción ocurre al recorrerlo (advertencia del README de faster-whisper).
    items = []
    for segment in segments:
        raw = segment.text.strip()
        text = clean_text(raw, settings["cleaning"]["hesitations"])
        if text:
            items.append({"start": round(segment.start, 2), "end": round(segment.end, 2), "text": text, "raw": raw})
    return {
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration_seconds": round(info.duration, 2),
        "transcription_seconds": round(time.perf_counter() - started, 1),
        "segments": items,
    }


def save_transcript(video_id: str, model_size: str, transcript: dict) -> Path:
    path = transcript_path(video_id, model_size)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"video_id": video_id, "whisper_model": model_size, **transcript}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"[{format_timestamp(s['start'])}] {s['text']}" for s in transcript["segments"]]
    path.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_transcript(video_id: str, model_size: str | None = None) -> dict | None:
    path = transcript_path(video_id, model_size)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def ensure_transcript(video_id: str, media_path: Path, model: WhisperModel | None = None) -> dict:
    """Devuelve la transcripción guardada o la genera si no existe (caché en disco)."""
    model_size = load_config()["whisper"]["model"]
    cached = load_transcript(video_id, model_size)
    if cached:
        return cached
    save_transcript(video_id, model_size, transcribe_file(model or load_whisper(model_size), media_path))
    return load_transcript(video_id, model_size)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe los videos del catálogo con Whisper.")
    parser.add_argument("ids", nargs="*", help="ids de video (ver data/videos.yaml)")
    parser.add_argument("--all", action="store_true", help="transcribir todos los videos del catálogo")
    parser.add_argument("--model", help="tamaño de Whisper (por defecto, el de config.yaml)")
    parser.add_argument("--force", action="store_true", help="repetir aunque ya exista la transcripción")
    args = parser.parse_args()

    model_size = args.model or load_config()["whisper"]["model"]
    video_ids = [video["id"] for video in load_catalog()] if args.all else args.ids
    if not video_ids:
        parser.error("indica uno o más ids, o usa --all")

    model = None
    for video_id in video_ids:
        media_path = find_video_file(video_id)
        if media_path is None:
            print(f"{video_id}: falta el archivo en data/videos/, se omite")
            continue
        if transcript_path(video_id, model_size).exists() and not args.force:
            print(f"{video_id}: ya transcrito con '{model_size}', se omite (usa --force para repetir)")
            continue
        model = model or load_whisper(model_size)
        transcript = transcribe_file(model, media_path)
        save_transcript(video_id, model_size, transcript)
        speed = transcript["duration_seconds"] / transcript["transcription_seconds"]
        print(
            f"{video_id}: {len(transcript['segments'])} segmentos en {transcript['transcription_seconds']} s "
            f"({speed:.1f}x tiempo real)"
        )


if __name__ == "__main__":
    main()
