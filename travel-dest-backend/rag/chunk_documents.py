"""Split cleaned destination text into a small number of overlapping chunks."""

from datetime import datetime, timezone
from math import ceil
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.rag import ChunkedDestinationDocument, DestinationChunk, ProcessedDestinationDocument


logger = get_logger(__name__)


def approximate_token_count(text: str) -> int:
    """Approximate tokens with a simple word count so the code stays easy to understand."""
    return len(text.split())


def split_text_into_chunks(
    text: str,
    target_tokens: int,
    overlap_tokens: int,
    max_chunks: int,
) -> list[str]:
    """Split text into one to three overlapping chunks using word boundaries."""
    words = text.split()
    if not words:
        return []

    total_words = len(words)
    if total_words <= target_tokens:
        return [" ".join(words)]

    estimated_chunk_count = ceil(total_words / target_tokens)
    chunk_count = max(1, min(max_chunks, estimated_chunk_count))
    base_chunk_size = ceil(total_words / chunk_count)

    chunks: list[str] = []
    start_index = 0

    for chunk_number in range(chunk_count):
        end_index = total_words if chunk_number == chunk_count - 1 else min(total_words, start_index + base_chunk_size)
        chunk_words = words[start_index:end_index]
        if chunk_words:
            chunks.append(" ".join(chunk_words))

        if end_index >= total_words:
            break

        next_start = max(0, end_index - overlap_tokens)
        if next_start <= start_index:
            next_start = end_index
        start_index = next_start

    return chunks


def output_file_path(destination_name: str) -> Path:
    """Build the chunk output file path for one destination."""
    settings = get_settings()
    safe_name = destination_name.lower().replace(" ", "_")
    return settings.chunks_data_path / f"{safe_name}_chunks.json"


def process_file(file_path: Path) -> None:
    """Read one processed document, chunk it, and save the result."""
    settings = get_settings()
    processed_document = ProcessedDestinationDocument.model_validate_json(file_path.read_text(encoding="utf-8"))
    chunk_texts = split_text_into_chunks(
        text=processed_document.clean_text,
        target_tokens=settings.CHUNK_TARGET_TOKENS,
        overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
        max_chunks=settings.MAX_CHUNKS_PER_DESTINATION,
    )

    chunk_models = [DestinationChunk(chunk_index=index, text=chunk_text) for index, chunk_text in enumerate(chunk_texts)]
    chunked_document = ChunkedDestinationDocument(
        destination=processed_document.destination,
        source=processed_document.source,
        title=processed_document.title,
        wikivoyage_title=processed_document.wikivoyage_title,
        url=processed_document.url,
        chunks=chunk_models,
        chunked_at=datetime.now(timezone.utc),
    )

    settings.chunks_data_path.mkdir(parents=True, exist_ok=True)
    destination_file = output_file_path(chunked_document.destination)
    destination_file.write_text(chunked_document.model_dump_json(indent=2), encoding="utf-8")
    logger.info(
        "Saved chunked destination document",
        extra={
            "event": "document_chunk",
            "destination": chunked_document.destination,
            "file_path": str(destination_file),
            "status": "saved",
        },
    )


def chunk_all_documents() -> None:
    """Chunk every processed document and continue when one file fails."""
    settings = get_settings()
    for file_path in sorted(settings.processed_data_path.glob("*.json")):
        try:
            process_file(file_path)
        except Exception as exc:
            logger.error(
                "Failed to chunk destination document",
                extra={
                    "event": "document_chunk",
                    "file_path": str(file_path),
                    "status": "failed",
                    "error": str(exc),
                },
            )


def main() -> None:
    """Run the chunking step from the command line."""
    chunk_all_documents()


if __name__ == "__main__":
    main()
