"""
Metadata Database Models.

Represents the relational schema catalog for discovered database structures,
supporting multi-tenant scoping and composite keys.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class MetadataSnapshot(Base):
    """Tracks a single metadata discovery run and its summary stats."""

    __tablename__ = "metadata_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # running, success, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    databases_count = Column(Integer, default=0, nullable=False)
    schemas_count = Column(Integer, default=0, nullable=False)
    objects_count = Column(Integer, default=0, nullable=False)
    columns_count = Column(Integer, default=0, nullable=False)
    relationships_count = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    provider = Column(String(50), nullable=True)
    function_count = Column(Integer, default=0, nullable=False)
    trigger_count = Column(Integer, default=0, nullable=False)
    extension_count = Column(Integer, default=0, nullable=False)

    data_source = relationship("DataSource")
    organization = relationship("Organization")


class DatabaseMetadata(Base):
    """Represents a logical database discovered on an external host."""

    __tablename__ = "database_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    owner = Column(String(255), nullable=True)
    encoding = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    data_source = relationship("DataSource")
    organization = relationship("Organization")
    schemas = relationship("SchemaMetadata", back_populates="database", cascade="all, delete-orphan")


class SchemaMetadata(Base):
    """Represents a namespace schema inside a database."""

    __tablename__ = "schema_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    database_id = Column(String(36), ForeignKey("database_metadata.id", ondelete="CASCADE"), nullable=False, index=True)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    owner = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    provider_metadata = Column(JSON, nullable=True)

    database = relationship("DatabaseMetadata", back_populates="schemas")
    data_source = relationship("DataSource")
    organization = relationship("Organization")
    objects = relationship("ObjectMetadata", back_populates="schema", cascade="all, delete-orphan")


class ObjectMetadata(Base):
    """Represents a table or a view inside a schema."""

    __tablename__ = "object_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schema_id = Column(String(36), ForeignKey("schema_metadata.id", ondelete="CASCADE"), nullable=False, index=True)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # TABLE, VIEW
    description = Column(Text, nullable=True)
    row_count_estimate = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    provider_metadata = Column(JSON, nullable=True)

    schema = relationship("SchemaMetadata", back_populates="objects")
    data_source = relationship("DataSource")
    organization = relationship("Organization")
    columns = relationship("ColumnMetadata", back_populates="object", cascade="all, delete-orphan")
    indexes = relationship("IndexMetadata", back_populates="object", cascade="all, delete-orphan")


class ColumnMetadata(Base):
    """Represents a column definition inside a table or view."""

    __tablename__ = "column_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String(36), ForeignKey("object_metadata.id", ondelete="CASCADE"), nullable=False, index=True)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    ordinal_position = Column(Integer, nullable=False)
    data_type = Column(String(255), nullable=False)
    native_type = Column(String(255), nullable=True)
    nullable = Column(Boolean, default=True, nullable=False)
    default_value = Column(Text, nullable=True)
    character_maximum_length = Column(Integer, nullable=True)
    numeric_precision = Column(Integer, nullable=True)
    numeric_scale = Column(Integer, nullable=True)
    is_primary_key = Column(Boolean, default=False, nullable=False)
    is_foreign_key = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)

    object = relationship("ObjectMetadata", back_populates="columns")
    data_source = relationship("DataSource")
    organization = relationship("Organization")


class IndexMetadata(Base):
    """Represents an index defined on a table."""

    __tablename__ = "index_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String(36), ForeignKey("object_metadata.id", ondelete="CASCADE"), nullable=False, index=True)
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    columns = Column(JSON, nullable=False)  # List of column names (e.g. ["order_id", "tenant_id"])
    unique = Column(Boolean, default=False, nullable=False)
    primary = Column(Boolean, default=False, nullable=False)
    type = Column(String(50), nullable=True)  # e.g., btree, hash

    object = relationship("ObjectMetadata", back_populates="indexes")
    data_source = relationship("DataSource")
    organization = relationship("Organization")


class RelationshipMetadata(Base):
    """Represents a foreign key relationship constraint between tables."""

    __tablename__ = "relationship_metadata"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    constraint_name = Column(String(255), nullable=False)
    from_object_id = Column(String(36), ForeignKey("object_metadata.id", ondelete="CASCADE"), nullable=False, index=True)
    from_columns = Column(JSON, nullable=False)  # List of column names (composite)
    to_object_id = Column(String(36), ForeignKey("object_metadata.id", ondelete="CASCADE"), nullable=False, index=True)
    to_columns = Column(JSON, nullable=False)  # List of column names (composite)
    update_action = Column(String(50), nullable=True)
    delete_action = Column(String(50), nullable=True)

    data_source = relationship("DataSource")
    organization = relationship("Organization")
    from_object = relationship("ObjectMetadata", foreign_keys=[from_object_id])
    to_object = relationship("ObjectMetadata", foreign_keys=[to_object_id])
