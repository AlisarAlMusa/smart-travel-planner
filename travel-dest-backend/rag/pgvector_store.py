"""Database helpers for storing destination chunks and embeddings in pgvector."""

import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, TIMESTAMP, Column, Integer, MetaData, String, Table, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger
from app.db.session import engine


logger = get_logger(__name__)

metadata = MetaData()

destination_chunks_table = Table(
    "destination_chunks",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("destination", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("title", Text),
    Column("wikivoyage_title", Text),
    Column("url", Text),
    Column("chunk_index", Integer, nullable=False),
    Column("chunk_text", Text, nullable=False),
    Column("metadata", JSON),
    Column("embedding", Vector(1536)),
    Column("created_at", TIMESTAMP, server_default=func.now()),
)


def chunk_exists(destination: str, chunk_index: int) -> bool:
    """Check whether a destination chunk already exists in the database."""
    query = (
        select(destination_chunks_table.c.id)
        .where(destination_chunks_table.c.destination == destination)
        .where(destination_chunks_table.c.chunk_index == chunk_index)
        .limit(1)
    )

    with engine.begin() as connection:
        result = connection.execute(query).scalar_one_or_none()

    return result is not None


def insert_destination_chunk(
    destination: str,
    source: str,
    title: str,
    wikivoyage_title: str,
    url: str,
    chunk_index: int,
    chunk_text: str,
    metadata_payload: dict[str, Any],
    embedding: list[float],
) -> bool:
    """Insert one embedded chunk and skip duplicates without raising to the caller."""
    insert_query = destination_chunks_table.insert().values(
        id=uuid.uuid4(),
        destination=destination,
        source=source,
        title=title,
        wikivoyage_title=wikivoyage_title,
        url=url,
        chunk_index=chunk_index,
        chunk_text=chunk_text,
        metadata=metadata_payload,
        embedding=embedding,
    )

    try:
        with engine.begin() as connection:
            connection.execute(insert_query)
        return True
    except IntegrityError:
        logger.info(
            "Skipped duplicate destination chunk",
            extra={
                "event": "pgvector_insert",
                "destination": destination,
                "status": "duplicate",
            },
        )
        return False


def clear_destination_chunks() -> None:
    """Delete all destination chunks when a full reload is needed."""
    with engine.begin() as connection:
        connection.execute(destination_chunks_table.delete())
