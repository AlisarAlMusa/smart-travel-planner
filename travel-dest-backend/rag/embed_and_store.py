"""Create Azure OpenAI embeddings for chunks and store them in Postgres with pgvector."""

from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.rag import ChunkedDestinationDocument
from app.services.azure_openai import build_azure_openai_client
from rag.pgvector_store import chunk_exists, insert_destination_chunk


logger = get_logger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
def create_embedding(chunk_text: str) -> list[float]:
    """Request one embedding from Azure OpenAI using the deployment name."""
    settings = get_settings()
    client = build_azure_openai_client()
    response = client.embeddings.create(
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=chunk_text,
    )
    return response.data[0].embedding


def process_chunk_file(file_path: Path) -> None:
    """Read one chunk file, embed each chunk, and store it in the database."""
    chunked_document = ChunkedDestinationDocument.model_validate_json(file_path.read_text(encoding="utf-8"))

    for chunk in chunked_document.chunks:
        try:
            if chunk_exists(chunked_document.destination, chunk.chunk_index):
                logger.info(
                    "Chunk already exists in database",
                    extra={
                        "event": "embedding_store",
                        "destination": chunked_document.destination,
                        "status": "skipped",
                    },
                )
                continue

            embedding = create_embedding(chunk.text)
            inserted = insert_destination_chunk(
                destination=chunked_document.destination,
                source=chunked_document.source,
                title=chunked_document.title,
                wikivoyage_title=chunked_document.wikivoyage_title,
                url=chunked_document.url,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.text,
                metadata_payload={
                    "destination": chunked_document.destination,
                    "source": chunked_document.source,
                    "url": chunked_document.url,
                    "chunk_index": chunk.chunk_index,
                },
                embedding=embedding,
            )

            if inserted:
                logger.info(
                    "Stored embedded destination chunk",
                    extra={
                        "event": "embedding_store",
                        "destination": chunked_document.destination,
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
