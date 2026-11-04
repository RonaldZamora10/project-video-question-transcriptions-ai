"""Lectura de la configuración (config.yaml) y del catálogo de videos (data/videos.yaml)."""

from functools import cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEO_EXTENSIONS = (".mp4", ".webm", ".mkv", ".m4a", ".mp3", ".wav")


@cache
def load_config() -> dict:
    """Lee config.yaml una sola vez por ejecución."""
    with open(PROJECT_ROOT / "config.yaml", encoding="utf-8") as file:
        return yaml.safe_load(file)


def project_path(key: str) -> Path:
    """Devuelve la ruta absoluta de una carpeta declarada en la sección `paths` de config.yaml."""
    return PROJECT_ROOT / load_config()["paths"][key]


def load_catalog() -> list[dict]:
    """Lista de videos del dataset, en el orden de data/videos.yaml."""
    with open(project_path("catalog"), encoding="utf-8") as file:
        return yaml.safe_load(file)


def find_video_file(video_id: str) -> Path | None:
    """Busca el archivo de un video por su id, sin importar la extensión. Devuelve None si no está descargado."""
    for folder in (project_path("videos"), project_path("uploads")):
        for extension in VIDEO_EXTENSIONS:
            candidate = folder / f"{video_id}{extension}"
            if candidate.exists():
                return candidate
    return None
