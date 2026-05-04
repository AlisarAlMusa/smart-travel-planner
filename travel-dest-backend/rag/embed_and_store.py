"""Create Azure OpenAI embeddings for chunks and store them in Postgres with pgvector."""

from pathlib import Path
from time import sleep

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.rag import ChunkedDestinationDocument
from app.services.azure_openai import build_azure_openai_client
from openai import BadRequestError
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from rag.pgvector_store import chunk_exists, insert_destination_chunk

logger = get_logger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_not_exception_type(BadRequestError),
    reraise=True,
)
def create_embedding(chunk_text: str) -> list[float]:
    """Request one embedding from Azure OpenAI using the deployment name."""
    settings = get_settings()
    client = build_azure_openai_client()
    response = client.embeddings.create(
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=chunk_text,
    )
    return response.data[0].embedding


def split_for_embedding(text: str, max_words: int) -> list[str]:
    """Split oversized chunk text into embedding-safe word windows."""
    words = text.split()
    if not words:
        return []

    if len(words) <= max_words:
        return [" ".join(words)]

    return [
        " ".join(words[start_index : start_index + max_words])
        for start_index in range(0, len(words), max_words)
    ]


def embedding_chunk_index(original_chunk_index: int, part_index: int, total_parts: int) -> int:
    """Return a stable DB chunk index, avoiding collisions for split chunks."""
    if total_parts == 1:
        return original_chunk_index

    return 100_000 + (original_chunk_index * 1_000) + part_index


def process_chunk_file(file_path: Path) -> None:
    """Read one chunk file, embed each chunk, and store it in the database."""
    settings = get_settings()
    chunked_document = ChunkedDestinationDocument.model_validate_json(
        file_path.read_text(encoding="utf-8")
    )

    for chunk in chunked_document.chunks:
        try:
            embedding_texts = split_for_embedding(
                chunk.text,
                max_words=settings.EMBEDDING_MAX_INPUT_WORDS,
            )

            if len(embedding_texts) > 1:
                logger.info(
                    "Split oversized destination chunk before embedding",
                    extra={
                        "event": "embedding_chunk_split",
                        "destination": chunked_document.destination,
                        "original_chunk_index": chunk.chunk_index,
                        "part_count": len(embedding_texts),
                        "original_word_count": len(chunk.text.split()),
                    },
                )

            for part_index, embedding_text in enumerate(embedding_texts):
                db_chunk_index = embedding_chunk_index(
                    original_chunk_index=chunk.chunk_index,
                    part_index=part_index,
                    total_parts=len(embedding_texts),
                )

                if chunk_exists(chunked_document.destination, db_chunk_index):
                    logger.info(
                        "Chunk already exists in database",
                        extra={
                            "event": "embedding_store",
                            "destination": chunked_document.destination,
                            "chunk_index": db_chunk_index,
                            "status": "skipped",
                        },
                    )
                    continue

                embedding = create_embedding(embedding_text)
                if settings.EMBEDDING_REQUEST_DELAY_SECONDS > 0:
                    logger.info(
                        "Pausing after embedding request to respect rate limits",
                        extra={
                            "event": "embedding_rate_limit_pause",
                            "destination": chunked_document.destination,
                            "delay_seconds": settings.EMBEDDING_REQUEST_DELAY_SECONDS,
                        },
                    )
                    sleep(settings.EMBEDDING_REQUEST_DELAY_SECONDS)

                inserted = insert_destination_chunk(
                    destination=chunked_document.destination,
                    source=chunked_document.source,
                    title=chunked_document.title,
                    wikivoyage_title=chunked_document.wikivoyage_title,
                    url=chunked_document.url,
                    chunk_index=db_chunk_index,
                    chunk_text=embedding_text,
                    metadata_payload={
                        "destination": chunked_document.destination,
                        "source": chunked_document.source,
                        "url": chunked_document.url,
                        "chunk_index": db_chunk_index,
                        "original_chunk_index": chunk.chunk_index,
                        "embedding_part_index": part_index,
                        "embedding_part_count": len(embedding_texts),
                    },
                    embedding=embedding,
                )

                if inserted:
                    logger.info(
                        "Stored embedded destination chunk",
                        extra={
                            "event": "embedding_store",
                            "destination": chunked_document.destination,
                            "chunk_index": db_chunk_index,
                            "file_path": str(file_path),
                            "status": "saved",
                        },
                    )
        except Exception as exc:
            logger.error(
                "Failed to embed or store destination chunk",
                extra={
                    "event": "embedding_store",
                    "destination": chunked_document.destination,
                    "file_path": str(file_path),
                    "status": "failed",
                    "error": str(exc),
                },
                exc_info=True,
            )


def embed_and_store_all() -> None:
    """Process every chunk file and continue when one destination fails."""
    settings = get_settings()
    for file_path in sorted(settings.chunks_data_path.glob("*_chunks.json")):
        try:
            process_chunk_file(file_path)
        except Exception as exc:
            logger.error(
                "Failed to process chunk file",
                extra={
                    "event": "embedding_store",
                    "file_path": str(file_path),
                    "status": "failed",
                    "error": str(exc),
                },
                exc_info=True,
            )


def main() -> None:
    """Run the embedding and storage step from the command line."""
    embed_and_store_all()


if __name__ == "__main__":
    main()
