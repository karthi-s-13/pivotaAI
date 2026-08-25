"""
DataSource SQLAlchemy Model.

Represents an external database connection registered in Pivota.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class DataSource(Base):
    """Represents an external database data source."""

    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Identity
    provider = Column(String(50), nullable=False, index=True)  # postgresql, mysql, mongodb
    environment = Column(String(50), default="development", nullable=False)  # development, staging, production

    # Connectivity
    host = Column(String(500), nullable=True)
    port = Column(Integer, nullable=True)
    connection_mode = Column(String(50), default="direct", nullable=False)  # direct, private_agent, vpn, vpc
    network_mode = Column(String(50), default="public", nullable=False)  # public, private
    provider_config = Column(JSON, nullable=True)  # Provider-specific configurations (e.g. replica_set, warehouse)

    # Security
    auth_method = Column(String(50), default="password", nullable=False)  # password, token, key, none
    tls = Column(Boolean, default=False, nullable=False)
    secret_reference = Column(String(255), nullable=True)
    access_policy = Column(JSON, nullable=True)

    # Health
    health_status = Column(String(50), default="unknown", nullable=False)  # connected, disconnected, error, unknown
    health_last_check = Column(DateTime(timezone=True), nullable=True)
    health_last_error = Column(Text, nullable=True)

    # Metadata & Stats
    metadata_normalized = Column(JSON, nullable=True)
    databases_count = Column(Integer, default=0, nullable=False)
    tables_count = Column(Integer, default=0, nullable=False)
    columns_count = Column(Integer, default=0, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(50), default="active", nullable=False)  # active, inactive, deleted

    # Organization & Creator
    organization_id = Column(
        String(36), ForeignKey("organizations.id"), nullable=False, index=True
    )
    created_by = Column(
        String(36), nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="data_sources")

    # Compatibility Properties/Getters/Setters
    @property
    def provider_type(self) -> str:
        return self.provider

    @provider_type.setter
    def provider_type(self, value: str):
        self.provider = value

    @property
    def ssl_enabled(self) -> bool:
        return self.tls

    @ssl_enabled.setter
    def ssl_enabled(self, value: bool):
        self.tls = value

    @property
    def connection_status(self) -> str:
        return self.health_status

    @connection_status.setter
    def connection_status(self, value: str):
        self.health_status = value

    @property
    def last_tested_at(self) -> Optional[datetime]:
        return self.health_last_check

    @last_tested_at.setter
    def last_tested_at(self, value: Optional[datetime]):
        self.health_last_check = value

    @property
    def connection_error(self) -> Optional[str]:
        return self.health_last_error

    @connection_error.setter
    def connection_error(self, value: Optional[str]):
        self.health_last_error = value

    @property
    def username(self) -> Optional[str]:
        if self.provider_config:
            return self.provider_config.get("username")
        return None

    @username.setter
    def username(self, value: Optional[str]):
        if not self.provider_config:
            self.provider_config = {}
        self.provider_config["username"] = value

    @property
    def database_name(self) -> Optional[str]:
        if self.provider_config:
            return self.provider_config.get("database_name")
        return None

    @database_name.setter
    def database_name(self, value: Optional[str]):
        if not self.provider_config:
            self.provider_config = {}
        self.provider_config["database_name"] = value

    @property
    def connection_string(self) -> Optional[str]:
        if self.provider_config:
            return self.provider_config.get("connection_string")
        return None

    @connection_string.setter
    def connection_string(self, value: Optional[str]):
        if not self.provider_config:
            self.provider_config = {}
        self.provider_config["connection_string"] = value

    @property
    def replica_set(self) -> Optional[str]:
        if self.provider_config:
            return self.provider_config.get("replica_set")
        return None

    @replica_set.setter
    def replica_set(self, value: Optional[str]):
        if not self.provider_config:
            self.provider_config = {}
        self.provider_config["replica_set"] = value

    @property
    def auth_source(self) -> Optional[str]:
        if self.provider_config:
            return self.provider_config.get("auth_source")
        return None

    @auth_source.setter
    def auth_source(self, value: Optional[str]):
        if not self.provider_config:
            self.provider_config = {}
        self.provider_config["auth_source"] = value
