"""
Schema Indexer.

Generates embeddings for database schema metadata and stores them
in the vector store for semantic retrieval.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.ai.schema.schema_service import (
    get_schema_for_data_source,
    generate_schema_documents,
)
from app.ai.providers.embeddings import get_embedding_provider
from app.ai.providers.vector_store.pgvector_store import get_vector_store
from app.ai.providers.vector_store.base import VectorDocument

logger = logging.getLogger(__name__)


def _collection_name(data_source_id: str) -> str:
    """Generate a collection name for a data source."""
    return f"schema_{data_source_id}"


def index_data_source_schema(
    db: Session,
    data_source_id: str,
    organization_id: str,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
) -> int:
    """
    Index the schema of a data source into the vector store.

    Extracts metadata from the catalog, generates embeddings, and stores them.

    Returns:
        Number of documents indexed.
    """
    # Retrieve schema from existing metadata catalog
    schema_data = get_schema_for_data_source(
        db, data_source_id, organization_id, database_name, schema_name
    )
    if not schema_data or not schema_data.get("databases"):
        logger.warning(f"No schema data found for data source {data_source_id}")
        return 0

    # Generate text documents for each table
    documents = generate_schema_documents(schema_data, data_source_id)
    if not documents:
        logger.warning(f"No documents generated for data source {data_source_id}")
        return 0

    # Generate embeddings
    embedding_provider = get_embedding_provider()
    texts = [doc["content"] for doc in documents]
    embeddings = embedding_provider.embed_texts(texts)

    # Build vector documents
    vector_docs = []
    for doc, embedding in zip(documents, embeddings):
        vector_docs.append(
            VectorDocument(
                id=doc["id"],
                content=doc["content"],
                embedding=embedding,
                metadata=doc["metadata"],
            )
        )

    # Upsert into vector store
    collection = _collection_name(data_source_id)
    vector_store = get_vector_store()

    # Clear existing embeddings for this data source
    vector_store.delete_collection(collection)

    # Store new embeddings
    count = vector_store.upsert(collection, vector_docs)
    logger.info(
        f"Indexed {count} schema documents for data source {data_source_id}"
    )
    return count


def delete_data_source_index(data_source_id: str) -> None:
    """Remove all schema embeddings for a data source."""
    collection = _collection_name(data_source_id)
    vector_store = get_vector_store()
    vector_store.delete_collection(collection)
    logger.info(f"Deleted schema index for data source {data_source_id}")
