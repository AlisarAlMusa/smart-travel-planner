"""Tests for the simple overlapping chunking strategy."""

from rag.chunk_documents import split_text_into_chunks


def test_chunking_creates_at_most_configured_chunks() -> None:
    """The chunker should cap the number of chunks at the configured maximum."""
    text = " ".join(f"word{i}" for i in range(3200))
    chunks = split_text_into_chunks(text=text, target_tokens=1000, overlap_tokens=150, max_chunks=4)

    assert 1 <= len(chunks) <= 4
    assert all(len(chunk.split()) <= 1000 for chunk in chunks)


def test_overlap_exists_between_chunks() -> None:
    """Later chunks should repeat some words from the end of the previous chunk."""
    text = " ".join(f"word{i}" for i in range(2200))
    chunks = split_text_into_chunks(text=text, target_tokens=1000, overlap_tokens=150, max_chunks=3)

    assert len(chunks) >= 2
    first_chunk_tail = chunks[0].split()[-150:]
    second_chunk_head = chunks[1].split()[:150]
    assert first_chunk_tail == second_chunk_head


def test_extra_tail_content_is_capped_after_max_chunks() -> None:
    """Very long documents should keep safe chunk sizes and drop remaining tail content."""
    text = " ".join(f"word{i}" for i in range(12000))
    chunks = split_text_into_chunks(text=text, target_tokens=2500, overlap_tokens=150, max_chunks=4)

    assert len(chunks) == 4
    assert all(len(chunk.split()) <= 2500 for chunk in chunks)
    assert "word11999" not in chunks[-1]


def test_empty_text_returns_safe_result() -> None:
    """Empty input should not produce invalid chunks."""
    chunks = split_text_into_chunks(text="", target_tokens=1000, overlap_tokens=150, max_chunks=3)

    assert chunks == []
