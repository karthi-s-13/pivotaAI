"""
HuggingFace Embedding Provider.

Uses sentence-transformers to generate embeddings locally.
Model is loaded once and cached as a singleton.
"""

import logging
from typing import List

from app.ai.providers.embeddings.base import EmbeddingProvider
from app.ai.config import ai_settings

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """HuggingFace sentence-transformers embedding provider."""

    def __init__(self, model_name: str | None = None):
        self._model_name = model_name or ai_settings.EMBEDDING_MODEL
        self._model = None
        self._dimensions = ai_settings.EMBEDDING_DIMENSIONS

    def _load_model(self):
        """Lazy-load the sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self._model_name}")
                self._model = SentenceTransformer(self._model_name)
                self._dimensions = self._model.get_embedding_dimension()
                logger.info(
                    f"Embedding model loaded: {self._model_name} "
                    f"(dim={self._dimensions})"
                )
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text."""
        self._load_model()
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts."""
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return [e.tolist() for e in embeddings]

    def get_dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""
        return self._dimensions

    def health_check(self) -> bool:
        """Check if the embedding model is loaded and operational."""
        try:
            self._load_model()
            # Quick test embedding
            test = self._model.encode("test", normalize_embeddings=True)
            return len(test) > 0
        except Exception as e:
            logger.warning(f"Embedding health check failed: {e}")
            return False


# Singleton instance
_provider_instance: HuggingFaceEmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get or create the singleton embedding provider instance."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = HuggingFaceEmbeddingProvider()
    return _provider_instance
