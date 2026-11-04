"""Pruebas de la configuración y del catálogo del dataset."""

import re

from videoqa.config import load_catalog, load_config, project_path


def test_config_has_required_sections():
    config = load_config()
    for section in ("paths", "whisper", "embeddings", "chunking", "retrieval", "llm"):
        assert section in config


def test_catalog_matches_dataset_rules():
    catalog = load_catalog()
    ids = [video["id"] for video in catalog]

    assert len(catalog) == 8
    assert len(set(ids)) == len(ids), "hay ids repetidos"
    for video in catalog:
        assert re.fullmatch(r"\d{2}_[a-z_]+", video["id"])
        minutes, seconds = map(int, video["duration"].split(":"))
        assert minutes * 60 + seconds <= 25 * 60, f"{video['id']} dura más de 25 minutos"


def test_project_path_is_inside_project():
    assert project_path("transcripts").name == "transcripts"
