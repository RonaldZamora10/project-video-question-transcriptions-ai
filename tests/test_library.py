"""Pruebas de los videos que agrega el usuario (sin internet)."""

import pytest

from videoqa import library


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=lmFUp4K8fFc",
        "https://youtube.com/watch?feature=share&v=lmFUp4K8fFc",
        "youtu.be/lmFUp4K8fFc?t=30",
        "https://m.youtube.com/shorts/lmFUp4K8fFc",
    ],
)
def test_youtube_id_accepts_video_links(url):
    assert library.youtube_id(url) == "lmFUp4K8fFc"


@pytest.mark.parametrize("url", ["https://vimeo.com/123", "https://www.youtube.com/@canal", "lmFUp4K8fFc", ""])
def test_youtube_id_rejects_other_links(url):
    assert library.youtube_id(url) is None


def test_download_rejects_non_youtube_without_network():
    with pytest.raises(library.VideoError):
        library.download_youtube("https://ejemplo.com/video.mp4")


def test_upload_is_listed_with_its_title(tmp_path, monkeypatch):
    monkeypatch.setattr(library, "project_path", lambda key: tmp_path)

    video = library.save_upload("Mi Charla Favorita.MP4", b"datos")

    assert video["id"] == "subido_mi_charla_favorita"
    assert (tmp_path / "subido_mi_charla_favorita.mp4").read_bytes() == b"datos"
    assert library.list_user_videos() == [{"id": video["id"], "title": "Mi Charla Favorita", "url": None}]
