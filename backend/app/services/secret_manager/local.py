"""
Local Secret Store Provider.

Implements the SecretManager interface using the local secrets table and Fernet encryption.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import decrypt_credential, encrypt_credential
from app.models.secret import Secret
from app.services.secret_manager.base import SecretManager


class LocalSecretStore(SecretManager):
    """Local database-backed secret store utilizing Fernet encryption."""

    def store_secret(self, db: Session, value: str) -> str:
        """Encrypt and store secret in database."""
        if not value:
            return ""
        encrypted = encrypt_credential(value)
        secret = Secret(encrypted_value=encrypted)
        db.add(secret)
        db.commit()
        db.refresh(secret)
        return f"secret:{secret.id}"

    def retrieve_secret(self, db: Session, secret_ref: str) -> Optional[str]:
        """Retrieve and decrypt secret from database."""
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

    def delete_secret(self, db: Session, secret_ref: str) -> None:
        """Delete secret from database."""
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

    def rotate_secrets(self, db: Session) -> dict:
        """
        Rotate all stored secrets by decrypting and re-encrypting them.

        Simulates rotation verification to ensure key updates are compatible.
        """
        secrets = db.query(Secret).all()
        rotated_count = 0
        failed_count = 0

        for secret in secrets:
            try:
                decrypted = decrypt_credential(secret.encrypted_value)
                # Re-encrypt
                new_encrypted = encrypt_credential(decrypted)
                secret.encrypted_value = new_encrypted
                rotated_count += 1
            except Exception:
                failed_count += 1

        if rotated_count > 0:
            db.commit()

        return {
            "status": "success",
            "rotated_count": rotated_count,
            "failed_count": failed_count,
        }
