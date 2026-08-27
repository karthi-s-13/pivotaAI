"""
Pivota AI Configuration.

Centralized configuration for AI services loaded from environment variables.
"""

from app.config import settings

class AISettings:
    """AI-specific settings delegating to main application settings."""
    
    @property
    def LLM_PROVIDER(self) -> str:
        return settings.LLM_PROVIDER
        
    @property
    def LLM_MODEL(self) -> str:
        return settings.LLM_MODEL
        
    @property
    def OLLAMA_BASE_URL(self) -> str:
        return settings.OLLAMA_BASE_URL
        
    @property
    def EMBEDDING_PROVIDER(self) -> str:
        return settings.EMBEDDING_PROVIDER
        
    @property
    def EMBEDDING_MODEL(self) -> str:
        return settings.EMBEDDING_MODEL
        
    @property
    def AI_MAX_HISTORY_MESSAGES(self) -> int:
        return settings.AI_MAX_HISTORY_MESSAGES
        
    @property
    def AI_MAX_ROWS(self) -> int:
        return settings.AI_MAX_ROWS
        
    @property
    def AI_QUERY_TIMEOUT_MS(self) -> int:
        return settings.AI_QUERY_TIMEOUT_MS
        
    @property
    def AI_MAX_RETRIES(self) -> int:
        return settings.AI_MAX_RETRIES
        
    @property
    def AI_MAX_RESULT_SIZE_MB(self) -> int:
        return settings.AI_MAX_RESULT_SIZE_MB

    @property
    def EMBEDDING_DIMENSIONS(self) -> int:
        return settings.EMBEDDING_DIMENSIONS

    # Derived constants
    AI_SCHEMA_TOP_K: int = 10


ai_settings = AISettings()
