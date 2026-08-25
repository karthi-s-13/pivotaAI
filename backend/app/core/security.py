"""
Pivota Security Module.

Handles password hashing, JWT token management, and credential encryption.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet

from app.config import settings


# --- Password Hashing ---

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    # bcrypt requires bytes
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except Exception:
        return False


# --- JWT Token Management ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data (must include 'sub' for user identifier).
        expires_delta: Optional custom expiry. Defaults to config value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiry.

    Args:
        data: Payload data (must include 'sub' for user identifier).

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# --- Credential Encryption ---

_fernet_cached: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """Get or generate a Fernet encryption instance."""
    global _fernet_cached
    if _fernet_cached is None:
        key = settings.ENCRYPTION_KEY
        if not key:
            # Stable dev key to prevent random failures across calls
            key = b"7sK-COTRr8gGopiLhJpSXAn7E2Ii-qBnBSavNUsRD0Y="
        elif isinstance(key, str):
            key = key.encode()
        _fernet_cached = Fernet(key)
    return _fernet_cached


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential string (e.g., database password)."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_credential(encrypted: str) -> str:
    """Decrypt an encrypted credential string."""
    f = _get_fernet()
    return f.decrypt(encrypted.encode()).decode()
