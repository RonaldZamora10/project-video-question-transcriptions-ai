"""Indexación (Etapas 5 a 7 y 9 del Entregable 1): fragmentos con tiempos, embeddings e5 y búsqueda en ChromaDB."""

from functools import cache

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from videoqa.clean import count_words
from videoqa.config import load_config, project_path


def _merge(segments: list[dict]) -> dict:
    return {
        "start": segments[0]["start"],
        "end": segments[-1]["end"],
        "text": " ".join(segment["text"] for segment in segments),
    }


def _overlap_tail(segments: list[dict], overlap_words: int) -> list[dict]:
    """Últimos segmentos que suman al menos `overlap_words` palabras, sin repetir nunca el fragmento entero."""
    words = 0
    for position in range(len(segments) - 1, 0, -1):
        words += count_words(segments[position]["text"])
        if words >= overlap_words:
            return segments[position:]
    return segments[1:]


def build_chunks(segments: list[dict], words_per_chunk: int, overlap_words: int) -> list[dict]:
    """Agrupa los segmentos de Whisper en fragmentos de ~`words_per_chunk` palabras.

    Se corta siempre entre segmentos (nunca a mitad de frase), así cada fragmento conserva su minuto de inicio y fin.
    """
    chunks, window, new_segments = [], [], 0
    for segment in segments:
        window.append(segment)
        new_segments += 1
        if sum(count_words(item["text"]) for item in window) >= words_per_chunk:
            chunks.append(_merge(window))
            window, new_segments = _overlap_tail(window, overlap_words), 0
    if new_segments:
        chunks.append(_merge(window))
    return chunks


@cache
def load_embedder() -> SentenceTransformer:
    return SentenceTransformer(load_config()["embeddings"]["model"])


def embed(texts: list[str], kind: str) -> list[list[float]]:
    """Embeddings normalizados. El modelo e5 exige el prefijo "query: " en preguntas y "passage: " en fragmentos.

    Fuente: https://huggingface.co/intfloat/multilingual-e5-base (sección FAQ y ejemplo con sentence-transformers).
    """
    vectors = load_embedder().encode([f"{kind}: {text}" for text in texts], normalize_embeddings=True)
    return vectors.tolist()


@cache
def get_client() -> chromadb.ClientAPI:
    # Telemetría desactivada: el sistema debe funcionar 100 % local.
    return chromadb.PersistentClient(path=str(project_path("index")), settings=Settings(anonymized_telemetry=False))


def ensure_index(video_id: str, transcript: dict) -> Collection:
    """Devuelve el índice del video; si no existe, lo crea. Al reiniciar el programa no se reconstruye."""
    settings = load_config()
    # Una colección por video y modelo de Whisper: cambiar de modelo no mezcla transcripciones distintas.
    # Distancia coseno y embeddings propios (embedding_function=None), según
    # https://docs.trychroma.com/docs/collections/configure
    collection = get_client().get_or_create_collection(
        name=f"{video_id}-{transcript['whisper_model']}",
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )
    if collection.count() == 0:
        chunks = build_chunks(
            transcript["segments"], settings["chunking"]["words_per_chunk"], settings["chunking"]["overlap_words"]
        )
        texts = [chunk["text"] for chunk in chunks]
        collection.add(
            ids=[f"{position:04d}" for position in range(len(chunks))],
            embeddings=embed(texts, "passage"),
            documents=texts,
            metadatas=[{"start": chunk["start"], "end": chunk["end"]} for chunk in chunks],
        )
    return collection


def retrieve(collection: Collection, question: str, top_k: int) -> list[dict]:
    """Los `top_k` fragmentos más parecidos a la pregunta, de mayor a menor similitud."""
    result = collection.query(
        query_embeddings=embed([question], "query"),
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"text": text, "start": meta["start"], "end": meta["end"], "similarity": round(1 - distance, 3)}
        for text, meta, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0], strict=True
        )
    ]
