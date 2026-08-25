"""
Auth Pivota Service Configuration.

Loads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Auth service settings loaded from environment."""

    # Database (shared with Pivota backend)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/pivota"

    # JWT for auth service sessions
    SECRET_KEY: str = "auth-pivota-dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # TOTP shared secret (must match Pivota backend's TOTP_SECRET_KEY)
    TOTP_SECRET_KEY: str = "pivota-totp-shared-secret-key-2024"

    # Gmail SMTP for sending OTP emails
    SMTP_EMAIL: str = ""
    SMTP_APP_PASSWORD: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    # OTP settings
    OTP_EXPIRY_SECONDS: int = 300  # 5 minutes
    OTP_LENGTH: int = 6

    # CORS
    CORS_ORIGINS: str = '["http://localhost:3001", "http://localhost:3000"]'

    # App
    APP_NAME: str = "Auth Pivota"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = AuthSettings()
