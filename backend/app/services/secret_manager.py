"""
Secret Manager Service.

Handles credential storage by encrypting passwords and storing them in an isolated secrets table.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import decrypt_credential, encrypt_credential
from app.models.secret import Secret


def store_secret(db: Session, value: str) -> str:
    """
    Encrypt a secret value, store it in the secrets table, and return a reference identifier.

    Args:
        db: SQLAlchemy Session.
        value: The plaintext credential.

    Returns:
        A secret reference string (e.g. "secret:uuid").
    """
    if not value:
        return ""
    encrypted = encrypt_credential(value)
    secret = Secret(encrypted_value=encrypted)
    db.add(secret)
    db.commit()
    db.refresh(secret)
    return f"secret:{secret.id}"


def retrieve_secret(db: Session, secret_ref: str) -> Optional[str]:
    """
    Retrieve and decrypt a secret value using its reference.

    Args:
        db: SQLAlchemy Session.
        secret_ref: The secret reference string (e.g. "secret:uuid").

    Returns:
        The decrypted plaintext credential or None if not found/invalid.
    """
    if not secret_ref or not secret_ref.startswith("secret:"):
        return None
    try:
        secret_id = secret_ref.split(":", 1)[1]
        secret = db.query(Secret).filter(Secret.id == secret_id).first()
        if not secret:
            return None
        return decrypt_credential(secret.encrypted_value)
    except Exception:
        return None


def delete_secret(db: Session, secret_ref: str) -> None:
    """
    Delete a secret from the secrets table.

    Args:
        db: SQLAlchemy Session.
        secret_ref: The secret reference string (e.g. "secret:uuid").
    """
    if not secret_ref or not secret_ref.startswith("secret:"):
        return
    try:
        secret_id = secret_ref.split(":", 1)[1]
        secret = db.query(Secret).filter(Secret.id == secret_id).first()
        if secret:
            db.delete(secret)
            db.commit()
    except Exception:
        pass
