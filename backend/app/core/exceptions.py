"""
Pivota Custom Exceptions and Global Error Handlers.
"""

from fastapi import HTTPException, status


class PivotaException(Exception):
    """Base exception for Pivota application errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(PivotaException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_FAILED")


class AuthorizationError(PivotaException):
    """Raised when user lacks permission."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, code="ACCESS_DENIED")


class NotFoundError(PivotaException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(message=message, code="NOT_FOUND")


class ConflictError(PivotaException):
    """Raised when a resource already exists."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, code="CONFLICT")


class ConnectionError(PivotaException):
    """Raised when a data source connection fails."""

    def __init__(self, message: str = "Connection failed"):
        super().__init__(message=message, code="CONNECTION_FAILED")


class ValidationError(PivotaException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, code="VALIDATION_ERROR")


# --- HTTP Exception Helpers ---

def raise_unauthorized(detail: str = "Could not validate credentials") -> None:
    """Raise a 401 Unauthorized HTTP exception."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_forbidden(detail: str = "Not enough permissions") -> None:
    """Raise a 403 Forbidden HTTP exception."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def raise_not_found(detail: str = "Resource not found") -> None:
    """Raise a 404 Not Found HTTP exception."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
    )


def raise_conflict(detail: str = "Resource already exists") -> None:
    """Raise a 409 Conflict HTTP exception."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )
