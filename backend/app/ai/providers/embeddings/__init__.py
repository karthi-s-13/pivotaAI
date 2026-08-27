"""
Embedding providers package.

Exposes a centralized factory function to get the active provider instance.
"""

from app.ai.providers.embeddings.base import EmbeddingProvider
from app.ai.config import ai_settings

_provider_instance: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get or create the singleton embedding provider instance based on configurations."""
    global _provider_instance
    if _provider_instance is None:
        provider_type = ai_settings.EMBEDDING_PROVIDER.lower().strip()
        
        if provider_type == "ollama":
            from app.ai.providers.embeddings.ollama_embeddings import OllamaEmbeddingProvider
            _provider_instance = OllamaEmbeddingProvider()
        else:
            # Fallback to HuggingFace
            from app.ai.providers.embeddings.huggingface_provider import HuggingFaceEmbeddingProvider
            _provider_instance = HuggingFaceEmbeddingProvider()
            
    return _provider_instance
