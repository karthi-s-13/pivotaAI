"""
Schema Retriever.

Performs semantic search against the vector store to find relevant
schema documents for a user's question.
"""

import logging
from typing import List, Optional

from app.ai.providers.embeddings import get_embedding_provider
from app.ai.providers.vector_store.pgvector_store import get_vector_store
from app.ai.providers.vector_store.base import VectorSearchResult
from app.ai.config import ai_settings

logger = logging.getLogger(__name__)


def retrieve_relevant_schemas(
    query: str,
    data_source_id: str,
    top_k: Optional[int] = None,
) -> List[VectorSearchResult]:
    """
    Retrieve the most relevant schema documents for a user query.

    Args:
        query: The user's natural language question.
        data_source_id: The data source to search within.
        top_k: Number of results to return (default from config).

    Returns:
        List of VectorSearchResult with schema document content and scores.
    """
    if top_k is None:
        top_k = ai_settings.AI_SCHEMA_TOP_K

    embedding_provider = get_embedding_provider()
    vector_store = get_vector_store()

    # Generate query embedding
    query_embedding = embedding_provider.embed_text(query)

    # Search vector store
    collection = f"schema_{data_source_id}"
    results = vector_store.search(
        collection=collection,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    logger.debug(
        f"Retrieved {len(results)} schema documents for query: '{query[:50]}...' "
        f"(data_source={data_source_id})"
    )
    return results


def get_relevant_table_names(
    query: str,
    data_source_id: str,
    top_k: int = 5,
) -> List[str]:
    """
    Get just the table names most relevant to a query.

    Args:
        query: The user's natural language question.
        data_source_id: The data source to search within.
        top_k: Number of results to return.

    Returns:
        List of table names.
    """
    results = retrieve_relevant_schemas(query, data_source_id, top_k)
    table_names = []
    for r in results:
        table = r.metadata.get("table")
        if table and table not in table_names:
            table_names.append(table)
    return table_names
