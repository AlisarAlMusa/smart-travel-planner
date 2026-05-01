"""Document schemas shared by the RAG ingestion pipeline."""

from datetime import datetime

from pydantic import BaseModel, Field


class RawDestinationDocument(BaseModel):
    """Validated shape for raw Wikivoyage content saved to disk."""

    destination: str
    source: str
    title: str
    wikivoyage_title: str
    url: str
    raw_text: str
    fetched_at: datetime


class ProcessedDestinationDocument(BaseModel):
    """Validated shape for cleaned destination content."""

    destination: str
    source: str
    title: str
    wikivoyage_title: str
    url: str
    clean_text: str
    processed_at: datetime


class DestinationChunk(BaseModel):
    """One chunk of destination text ready for embeddings."""

    chunk_index: int
    text: str = Field(min_length=1)


class ChunkedDestinationDocument(BaseModel):
    """Validated shape for chunked destination documents."""

    destination: str
    source: str
    title: str
    wikivoyage_title: str
    url: str
    chunks: list[DestinationChunk]
    chunked_at: datetime

