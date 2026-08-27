"""
Vector Store Interface.

Abstract base class for vector storage backends (pgVector, ChromaDB, Pinecone, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VectorDocument:
    """A document with its embedding and metadata."""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VectorSearchResult:
    """Result from a vector similarity search."""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float  # similarity score (higher = more similar)


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    def upsert(
        self,
        collection: str,
        documents: List[VectorDocument],
    ) -> int:
        """
        Insert or update documents in a collection.

        Args:
            collection: Collection/namespace identifier.
            documents: List of documents with embeddings.

        Returns:
            Number of documents upserted.
        """
        pass

    @abstractmethod
    def search(
        self,
        collection: str,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """
        Search for similar documents by embedding.

        Args:
            collection: Collection/namespace to search.
            query_embedding: Query vector.
            top_k: Number of results to return.
            filter_metadata: Optional metadata filters.

        Returns:
            List of matching documents with similarity scores.
        """
        pass

    @abstractmethod
    def delete(
        self,
        collection: str,
        document_ids: List[str],
    ) -> int:
        """
        Delete documents by ID.

        Args:
            collection: Collection/namespace.
            document_ids: List of document IDs to delete.

        Returns:
            Number of documents deleted.
        """
        pass

    @abstractmethod
    def delete_collection(self, collection: str) -> None:
        """
        Delete an entire collection.

        Args:
            collection: Collection/namespace to delete.
        """
        pass
