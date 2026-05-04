"""Tests for embedding ingestion helpers."""

from rag.embed_and_store import embedding_chunk_index, split_for_embedding


def test_split_for_embedding_keeps_safe_text_whole() -> None:
    """Text under the max word count should stay as one embedding request."""
    text = " ".join(f"word{i}" for i in range(5))

    assert split_for_embedding(text, max_words=10) == [text]


def test_split_for_embedding_splits_oversized_text() -> None:
    """Oversized text should be split into safe embedding windows."""
    text = " ".join(f"word{i}" for i in range(12))

    chunks = split_for_embedding(text, max_words=5)

    assert [len(chunk.split()) for chunk in chunks] == [5, 5, 2]


def test_embedding_chunk_index_avoids_split_collisions() -> None:
    """Split chunk indexes should not collide with normal 0, 1, 2 chunk indexes."""
    assert embedding_chunk_index(1, 0, total_parts=1) == 1
    assert embedding_chunk_index(0, 0, total_parts=2) == 100_000
    assert embedding_chunk_index(0, 1, total_parts=2) == 100_001
    assert embedding_chunk_index(1, 0, total_parts=2) == 101_000
