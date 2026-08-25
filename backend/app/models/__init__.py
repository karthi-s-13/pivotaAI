"""
Models package.

Import all models here so SQLAlchemy can discover them for table creation.
"""

from app.models.organization import Organization
from app.models.user import User
from app.models.data_source import DataSource
from app.models.audit_log import AuditLog
from app.models.secret import Secret
from app.models.iam_policy import IAMPolicy
from app.models.iam_user import IAMUser
from app.models.metadata import (
    MetadataSnapshot,
    DatabaseMetadata,
    SchemaMetadata,
    ObjectMetadata,
    ColumnMetadata,
    IndexMetadata,
    RelationshipMetadata,
)

__all__ = [
    "Organization",
    "User",
    "DataSource",
    "AuditLog",
    "Secret",
    "IAMPolicy",
    "IAMUser",
    "MetadataSnapshot",
    "DatabaseMetadata",
    "SchemaMetadata",
    "ObjectMetadata",
    "ColumnMetadata",
    "IndexMetadata",
    "RelationshipMetadata",
]
