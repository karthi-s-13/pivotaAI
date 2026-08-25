"""
Base Secret Manager Interface.

Defines the contract for credential encryption, retrieval, deletion, and rotation.
"""

from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.orm import Session


class SecretManager(ABC):
    """Abstract interface defining required methods for Pivota Secret Storage."""

    @abstractmethod
    def store_secret(self, db: Session, value: str) -> str:
        """
        Encrypt and store a credential, returning a secret reference identifier.

        Args:
            db: Session instance.
            value: Plaintext secret to encrypt.

        Returns:
            Secret reference string (e.g. "secret:uuid").
        """
        pass

    @abstractmethod
    def retrieve_secret(self, db: Session, secret_ref: str) -> Optional[str]:
        """
        Decrypt and retrieve a credential value from its reference.

        Args:
            db: Session instance.
            secret_ref: Secret reference string (e.g. "secret:uuid").

        Returns:
            Plaintext secret or None if not found/invalid.
        """
        pass

    @abstractmethod
    def delete_secret(self, db: Session, secret_ref: str) -> None:
        """
        Delete a credential from the secret store.

        Args:
            db: Session instance.
            secret_ref: Secret reference string (e.g. "secret:uuid").
        """
        pass

    @abstractmethod
    def rotate_secrets(self, db: Session) -> dict:
        """
        Rotate secrets, re-encrypting them to verify key rotation compatibility.

        Args:
            db: Session instance.

        Returns:
            dict containing rotation results.
        """
        pass
class_name = "SecretManager"
