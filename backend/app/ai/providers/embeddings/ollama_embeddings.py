"""
Ollama Embedding Provider.

Generates embeddings using local Ollama model (e.g. nomic-embed-text).
"""

import logging
from typing import List

from langchain_ollama import OllamaEmbeddings
from app.ai.providers.embeddings.base import EmbeddingProvider
from app.ai.config import ai_settings

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama-based embedding provider."""

    def __init__(self, model_name: str | None = None, base_url: str | None = None):
        self._model_name = model_name or ai_settings.EMBEDDING_MODEL
        self._base_url = base_url or ai_settings.OLLAMA_BASE_URL
        self._embeddings = None
        self._dimensions = ai_settings.EMBEDDING_DIMENSIONS

    def _load_model(self):
        """Lazy-load the Ollama embeddings model."""
        if self._embeddings is None:
            try:
                logger.info(f"Connecting to Ollama embeddings: {self._model_name} (url={self._base_url})")
                self._embeddings = OllamaEmbeddings(
                    model=self._model_name,
                    base_url=self._base_url,
                )
                # Test query to populate dimension
                test = self._embeddings.embed_query("test")
                self._dimensions = len(test)
                logger.info(f"Ollama embeddings model ready: {self._model_name} (dim={self._dimensions})")
            except Exception as e:
                logger.error(f"Failed to load Ollama embeddings: {e}")
                raise

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text."""
        self._load_model()
        return self._embeddings.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts."""
        self._load_model()
        return self._embeddings.embed_documents(texts)

    def get_dimensions(self) -> int:
        """Return dimensions of generated embedding vectors."""
        return self._dimensions

    def health_check(self) -> bool:
        """Check if the embedding service is ready."""
        try:
            self._load_model()
            test = self._embeddings.embed_query("test")
            return len(test) > 0
        except Exception as e:
            logger.warning(f"Ollama embedding health check failed: {e}")
            return False
