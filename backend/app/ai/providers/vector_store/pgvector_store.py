"""
pgVector Store Implementation.

Uses PostgreSQL with the pgvector extension for vector similarity search.
Leverages Pivota's existing PostgreSQL database — no extra infrastructure needed.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from app.db.base import engine
from app.ai.config import ai_settings
from app.ai.providers.vector_store.base import (
    VectorStore,
    VectorDocument,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)

# SQL for creating the schema_embeddings table with pgvector
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_embeddings (
    id VARCHAR(255) PRIMARY KEY,
    collection VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector({dimensions}),
    metadata JSONB DEFAULT '{{}}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

_CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_schema_embeddings_collection
    ON schema_embeddings (collection);
"""

_CREATE_VECTOR_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_schema_embeddings_vector
    ON schema_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
"""


class PgVectorStore(VectorStore):
    """pgVector-based vector store using Pivota's PostgreSQL database."""

    def __init__(self):
        self._dimensions = ai_settings.EMBEDDING_DIMENSIONS
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Create the pgvector extension and embeddings table if needed."""
        if self._initialized:
            return

        try:
            with engine.connect() as conn:
                # Enable pgvector extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

                # Check if table exists and column dimensions match self._dimensions
                check_dim_sql = """
                SELECT atttypmod
                FROM pg_attribute
                WHERE attrelid = 'schema_embeddings'::regclass
                  AND attname = 'embedding';
                """
                try:
                    current_dim = conn.execute(text(check_dim_sql)).scalar()
                    if current_dim and current_dim != self._dimensions:
                        logger.warning(
                            f"Dimension mismatch in schema_embeddings: database has atttypmod {current_dim}, "
                            f"config expects {self._dimensions}. Dropping table to recreate with correct dimensions."
                        )
                        conn.execute(text("DROP TABLE IF EXISTS schema_embeddings CASCADE;"))
                except Exception:
                    pass  # Table might not exist yet, which is fine

                # Create embeddings table
                create_sql = _CREATE_TABLE_SQL.format(dimensions=self._dimensions)
                conn.execute(text(create_sql))

                # Create indexes
                conn.execute(text(_CREATE_INDEX_SQL))

                # Only create IVFFlat index if there are enough rows
                count = conn.execute(
                    text("SELECT COUNT(*) FROM schema_embeddings;")
                ).scalar()
                if count and count >= 100:
                    try:
                        conn.execute(text(_CREATE_VECTOR_INDEX_SQL))
                    except Exception:
                        pass  # IVFFlat needs enough data

                conn.commit()
                self._initialized = True
                logger.info("pgVector store initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pgVector store: {e}")
            # Still mark as initialized to avoid repeated failures
            self._initialized = True
            raise

    def upsert(
        self,
        collection: str,
        documents: List[VectorDocument],
    ) -> int:
        """Insert or update documents in the vector store."""
        self._ensure_initialized()

        if not documents:
            return 0

        count = 0
        with engine.connect() as conn:
            for doc in documents:
                embedding_str = "[" + ",".join(str(v) for v in doc.embedding) + "]"
                metadata_str = json.dumps(doc.metadata or {})

                conn.execute(
                    text("""
                        INSERT INTO schema_embeddings (id, collection, content, embedding, metadata)
                        VALUES (:id, :collection, :content, CAST(:embedding AS vector), CAST(:metadata AS jsonb))
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            created_at = NOW()
                    """),
                    {
                        "id": doc.id,
                        "collection": collection,
                        "content": doc.content,
                        "embedding": embedding_str,
                        "metadata": metadata_str,
                    },
                )
                count += 1

            conn.commit()

        logger.debug(f"Upserted {count} documents into collection '{collection}'")
        return count

    def search(
        self,
        collection: str,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Search for similar documents using cosine similarity."""
        self._ensure_initialized()

        embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        # Build query with optional metadata filter
        where_clauses = ["collection = :collection"]
        params: Dict[str, Any] = {
            "collection": collection,
            "embedding": embedding_str,
            "top_k": top_k,
        }

        if filter_metadata:
            for key, value in filter_metadata.items():
                param_key = f"meta_{key}"
                where_clauses.append(f"metadata->>'{key}' = :{param_key}")
                params[param_key] = str(value)

        where_sql = " AND ".join(where_clauses)

        query = text(f"""
            SELECT
                id,
                content,
                metadata,
                1 - (embedding <=> CAST(:embedding AS vector)) AS score
            FROM schema_embeddings
            WHERE {where_sql}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)

        results = []
        with engine.connect() as conn:
            rows = conn.execute(query, params).fetchall()
            for row in rows:
                metadata = row[2] if isinstance(row[2], dict) else json.loads(row[2]) if row[2] else {}
                results.append(
                    VectorSearchResult(
                        id=row[0],
                        content=row[1],
                        metadata=metadata,
                        score=float(row[3]) if row[3] else 0.0,
                    )
                )

        return results

    def delete(
        self,
        collection: str,
        document_ids: List[str],
    ) -> int:
        """Delete documents by ID from a collection."""
        self._ensure_initialized()

        if not document_ids:
            return 0

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM schema_embeddings
                    WHERE collection = :collection AND id = ANY(:ids)
                """),
                {"collection": collection, "ids": document_ids},
            )
            conn.commit()
            return result.rowcount

    def delete_collection(self, collection: str) -> None:
        """Delete all documents in a collection."""
        self._ensure_initialized()

        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM schema_embeddings WHERE collection = :collection"),
                {"collection": collection},
            )
            conn.commit()
            logger.info(f"Deleted collection '{collection}'")


# Singleton instance
_store_instance: PgVectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the singleton vector store instance."""
    global _store_instance
    if _store_instance is None:
        _store_instance = PgVectorStore()
    return _store_instance
