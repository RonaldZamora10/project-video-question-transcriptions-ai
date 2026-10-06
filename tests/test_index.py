"""Pruebas de la fragmentación por segmentos (no cargan modelos)."""

from videoqa.index import build_chunks


def make_segments(count: int, words_each: int = 10) -> list[dict]:
    return [
        {"start": float(i * 5), "end": float(i * 5 + 5), "text": " ".join(f"p{i}_{w}" for w in range(words_each))}
        for i in range(count)
    ]


def test_chunks_keep_start_and_end_of_their_segments():
    chunks = build_chunks(make_segments(10), words_per_chunk=30, overlap_words=10)
    assert chunks[0]["start"] == 0.0 and chunks[0]["end"] == 15.0
    assert chunks[-1]["end"] == 50.0


def test_consecutive_chunks_overlap():
    chunks = build_chunks(make_segments(10), words_per_chunk=30, overlap_words=10)
    assert chunks[1]["start"] < chunks[0]["end"]
    assert chunks[0]["text"].split()[-10:] == chunks[1]["text"].split()[:10]


def test_every_segment_appears_in_some_chunk():
    segments = make_segments(13)
    text = " ".join(chunk["text"] for chunk in build_chunks(segments, words_per_chunk=30, overlap_words=10))
    assert all(segment["text"] in text for segment in segments)


def test_no_duplicate_chunk_made_only_of_overlap():
    # 5 segmentos de 10 palabras con fragmentos de 30: tras el 2.º fragmento solo queda el solapamiento (segmento 4),
    # que ya está indexado; no debe crearse un 3.er fragmento repetido.
    chunks = build_chunks(make_segments(5), words_per_chunk=30, overlap_words=10)
    assert len(chunks) == 2


def test_long_single_segment_does_not_loop_forever():
    chunks = build_chunks(make_segments(3, words_each=100), words_per_chunk=30, overlap_words=10)
    assert len(chunks) == 3
