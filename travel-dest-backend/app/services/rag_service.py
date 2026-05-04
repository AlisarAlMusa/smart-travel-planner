"""Retrieve destination chunks from Postgres + pgvector for the agent."""
# implements embed query and retrieval of similar chunks based on cosine distance

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import DestinationChunk


class RAGService:
    """Read similar destinations from the chunk table using vector distance."""

    def __init__(
        self,
        db_factory: sessionmaker[Session],
        embedding_client: Any,
        embedding_deployment: str,
    ) -> None:
        """Store the DB session factory and embedding client."""
        self.db_factory = db_factory
        self.embedding_client = embedding_client
        self.embedding_deployment = embedding_deployment

    async def embed_query(self, query: str) -> list[float]:
        """Create an embedding for a user retrieval query."""
        response = self.embedding_client.embeddings.create(
            model=self.embedding_deployment,
            input=query,
        )
        return response.data[0].embedding

    def retrieve_similar_destinations(self, query_embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        """Run a pgvector cosine-distance query against stored chunks."""
        with self.db_factory() as db:
            similarity_score = (1 - DestinationChunk.embedding.cosine_distance(query_embedding)).label(
                "similarity_score"
            )
            statement = (
                select(
                    DestinationChunk.destination,
                    DestinationChunk.title,
                    DestinationChunk.url,
                    DestinationChunk.chunk_index,
                    DestinationChunk.chunk_text,
                    similarity_score,
                )
                .order_by(DestinationChunk.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            )
            rows = db.execute(statement).all()

        return [
            {
                "destination": row.destination,
                "title": row.title,
                "url": row.url,
                "chunk_index": row.chunk_index,
                "chunk_text": row.chunk_text,
                "similarity_score": float(row.similarity_score),
            }
            for row in rows
        ]
