"""
Pivota Backend Configuration.

Loads settings from environment variables / .env file.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_NAME: str = "Pivota Data Navigator"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database (Pivota's own PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/pivota"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        from urllib.parse import urlparse
        try:
            parsed = urlparse(v)
        except Exception as e:
            raise ValueError(f"Invalid DATABASE_URL format: {e}")
        
        scheme = parsed.scheme.lower()
        if not scheme:
            raise ValueError("DATABASE_URL is missing a scheme protocol")
            
        base_scheme = scheme.split("+")[0]
        ALLOWED_SCHEMES = {"postgresql", "postgres", "mysql", "mongodb", "mongodb+srv", "mssql", "sqlserver"}
        if base_scheme not in ALLOWED_SCHEMES:
            raise ValueError(
                f"Unsupported database scheme in DATABASE_URL: '{scheme}'. "
                f"Allowed schemes: {', '.join(sorted(list(ALLOWED_SCHEMES)))}"
            )
        return v

    # JWT
    SECRET_KEY: str = "pivota-dev-secret-key-change-in-production-2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 2FA / TOTP (shared secret with Auth Pivota service)
    TOTP_SECRET_KEY: str = "pivota-totp-shared-secret-key-2024"
    AUTH_SERVICE_URL: str = "http://localhost:8001"

    # Credential Encryption
    ENCRYPTION_KEY: str = ""

    # Gmail SMTP for sending IAM invitation emails
    SMTP_EMAIL: str = ""
    SMTP_APP_PASSWORD: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    # AI Copilot Configuration
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3.2:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_PROVIDER: str = "ollama"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    EMBEDDING_DIMENSIONS: int = 768
    AI_MAX_HISTORY_MESSAGES: int = 12
    AI_MAX_ROWS: int = 1000
    AI_QUERY_TIMEOUT_MS: int = 10000
    AI_MAX_RETRIES: int = 2
    AI_MAX_RESULT_SIZE_MB: int = 10

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000","http://localhost:3001"]'

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
