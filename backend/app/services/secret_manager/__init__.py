"""
Secret Manager Package.

Exposes the active SecretManager provider instance and convenience routing methods.
"""

from app.config import settings
from app.services.secret_manager.base import SecretManager
from app.services.secret_manager.local import LocalSecretStore

_active_manager: SecretManager = None


def get_secret_manager() -> SecretManager:
    """Resolve and return the configured SecretManager provider."""
    global _active_manager
    if _active_manager is None:
        provider_type = getattr(settings, "SECRET_MANAGER_PROVIDER", "local").lower()
        if provider_type == "local":
            _active_manager = LocalSecretStore()
        else:
            raise ValueError(f"Unsupported secret manager provider: '{provider_type}'")
    return _active_manager


# --- Convenience Wrappers ---


def store_secret(db, value: str) -> str:
    """Encrypt and store a secret."""
    return get_secret_manager().store_secret(db, value)


def retrieve_secret(db, secret_ref: str) -> str:
    """Retrieve and decrypt a secret."""
    return get_secret_manager().retrieve_secret(db, secret_ref)


def delete_secret(db, secret_ref: str) -> None:
    """Delete a secret."""
    return get_secret_manager().delete_secret(db, secret_ref)


def rotate_secrets(db) -> dict:
    """Rotate all secrets."""
    return get_secret_manager().rotate_secrets(db)
