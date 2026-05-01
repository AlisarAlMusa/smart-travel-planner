CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS destination_chunks (
    id UUID PRIMARY KEY,
    destination TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT,
    wikivoyage_title TEXT,
    url TEXT,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(destination, chunk_index)
);

CREATE INDEX IF NOT EXISTS destination_chunks_embedding_idx
ON destination_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS destination_chunks_destination_idx
ON destination_chunks(destination);
