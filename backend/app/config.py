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

    # Credential Encryption
    ENCRYPTION_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'

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
