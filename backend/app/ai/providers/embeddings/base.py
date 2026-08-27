"""
Embedding Provider Interface.

Abstract base class for embedding providers. Enables swapping embedding
backends (HuggingFace, OpenAI, Cohere, etc.) without changing the pipeline.
"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single text.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector as a list of floats.
        """
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors.
        """
        pass

    @abstractmethod
    def get_dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the embedding model is loaded and ready."""
        pass
