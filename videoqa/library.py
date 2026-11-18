"""Videos que agrega el usuario (archivo propio o enlace de YouTube), guardados en data/videos/subidos/.

Junto a cada archivo se guarda <id>.json con su título y, si viene de YouTube, su enlace. Así la lista "Mis videos"
sobrevive al reiniciar la aplicación y la transcripción no se repite.
"""

import json
import re
from pathlib import Path

from videoqa.config import load_config, project_path

# Solo enlaces de video de YouTube: es lo único que se descarga desde la interfaz.
_YOUTUBE = re.compile(
    r"^(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/)|youtu\.be/)([\w-]{11})"
)


class VideoError(Exception):
    """Error con un mensaje listo para mostrar al usuario."""


def youtube_id(url: str) -> str | None:
    match = _YOUTUBE.match(url.strip())
    return match.group(1) if match else None


def save_meta(video_id: str, title: str, url: str | None = None) -> None:
    folder = project_path("uploads")
    folder.mkdir(parents=True, exist_ok=True)
    data = {"id": video_id, "title": title, "url": url}
    (folder / f"{video_id}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def list_user_videos() -> list[dict]:
    """Videos agregados por el usuario, del más reciente al más antiguo."""
    folder = project_path("uploads")
    files = (
        sorted(folder.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True) if folder.exists() else []
    )
    return [json.loads(path.read_text(encoding="utf-8")) for path in files]


def download_youtube(url: str) -> dict:
    """Descarga solo el audio (Whisper no necesita la imagen; el reproductor usa el enlace de YouTube)."""
    import yt_dlp  # import tardío: solo se carga si el usuario usa esta opción

    video_key = youtube_id(url)
    if video_key is None:
        raise VideoError("El enlace no parece de un video de YouTube. Copia la dirección completa del video.")
    video_id = f"yt_{video_key}"
    clean_url = f"https://www.youtube.com/watch?v={video_key}"
    existing = next((video for video in list_user_videos() if video["id"] == video_id), None)
    if existing:
        return existing

    max_minutes = load_config()["youtube"]["max_minutes"]
    folder = project_path("uploads")
    options = {
        "format": "bestaudio[ext=m4a]/bestaudio",  # m4a lo lee Whisper sin instalar ffmpeg
        "outtmpl": str(folder / f"{video_id}.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(clean_url, download=False)
            if (info.get("duration") or 0) > max_minutes * 60:
                raise VideoError(f"El video dura más de {max_minutes} minutos. Elige uno más corto.")
            downloader.download([clean_url])
    except yt_dlp.utils.DownloadError as error:
        raise VideoError(
            "No se pudo descargar el video. Revisa que el enlace sea público y que tengas conexión a internet."
        ) from error
    save_meta(video_id, info.get("title") or video_id, clean_url)
    return {"id": video_id, "title": info.get("title") or video_id, "url": clean_url}


def save_upload(name: str, data: bytes) -> dict:
    """Guarda un archivo subido desde la interfaz y devuelve su ficha."""
    stem, _, extension = name.rpartition(".")
    video_id = "subido_" + (re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")[:40] or "video")
    folder = project_path("uploads")
    folder.mkdir(parents=True, exist_ok=True)
    path: Path = folder / f"{video_id}.{extension.lower()}"
    if not path.exists():
        path.write_bytes(data)
    save_meta(video_id, stem or name)
    return {"id": video_id, "title": stem or name, "url": None}
