"""
Data Source Pydantic Schemas.

Conforms to the refined 6-section normalized Datasource data model.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# --- Section Schemas ---

class IdentitySection(BaseModel):
    """Identity details for the datasource."""

    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=255)
    provider: str = Field(..., pattern="^(postgresql|mysql|sqlserver|mongodb|supabase)$")
    environment: str = Field(default="development", pattern="^(development|staging|production)$")


class ConnectivitySection(BaseModel):
    """Connectivity details for the datasource."""

    host: Optional[str] = None
    port: Optional[int] = Field(None, gt=0, le=65535)
    connection_mode: str = Field(default="direct", pattern="^(direct|private_agent|vpn|vpc)$")
    network_mode: str = Field(default="public", pattern="^(public|private)$")
    provider_config: Optional[Dict[str, Any]] = Field(default_factory=dict)  # Arbitrary provider settings


class SecuritySection(BaseModel):
    """Security and Auth details for the datasource (responses)."""

    auth_method: str = Field(default="password", pattern="^(password|token|key|none)$")
    tls: bool = False
    secret_reference: Optional[str] = None
    access_policy: Optional[Dict[str, Any]] = None


class SecuritySectionCreate(BaseModel):
    """Security and Auth details for the datasource (requests)."""

    auth_method: str = Field(default="password", pattern="^(password|token|key|none)$")
    tls: bool = False
    password: Optional[str] = None  # Transmitted plain, never saved plain
    secret_reference: Optional[str] = None
    access_policy: Optional[Dict[str, Any]] = None


class CapabilitiesSection(BaseModel):
    """Provider adapter capabilities."""

    sql: bool
    schemas: bool
    transactions: bool
    relationships: str  # "full", "partial", "inferred", "none"


class HealthSection(BaseModel):
    """Datasource connection health details."""

    status: str = "unknown"  # connected, disconnected, error, unknown
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None


class MetadataSection(BaseModel):
    """Normalized metadata structure discovered from datasource."""

    databases: List[str] = []
    schemas: List[str] = []
    objects: List[Dict[str, Any]] = []
    columns: List[Dict[str, Any]] = []
    relationships: List[Dict[str, Any]] = []
    statistics: Optional[Dict[str, Any]] = None


# --- Requests ---

class DataSourceCreate(BaseModel):
    """Create request payload."""

    identity: IdentitySection
    connectivity: ConnectivitySection
    security: SecuritySectionCreate
    description: Optional[str] = None
    connection_string: Optional[str] = None  # User can optionally provide raw URI string


class DataSourceUpdate(BaseModel):
    """Update request payload."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    connectivity: Optional[ConnectivitySection] = None
    security: Optional[SecuritySectionCreate] = None
    environment: Optional[str] = None
    connection_string: Optional[str] = None  # User can optionally update via raw URI string


class ConnectionTestRequest(BaseModel):
    """Request to test a connection without saving it."""

    provider: str = Field(..., pattern="^(postgresql|mysql|sqlserver|mongodb|supabase)$")
    host: Optional[str] = None
    port: Optional[int] = Field(None, gt=0, le=65535)
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None
    ssl_enabled: bool = False
    provider_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


# --- Responses ---

class ConnectionTestStep(BaseModel):
    """Result of a single staged connection testing step."""

    name: str  # "validation", "network", "authentication", "health"
    status: str  # "success", "failed", "skipped", "pending"
    message: Optional[str] = None
    latency_ms: Optional[float] = None


class ConnectionTestResult(BaseModel):
    """Result of a connection test containing staged diagnostics."""

    success: bool
    message: str
    latency_ms: Optional[float] = None
    server_version: Optional[str] = None
    details: Optional[dict] = None
    steps: List[ConnectionTestStep] = []


class DataSourceResponse(BaseModel):
    """Normalized response payload."""

    identity: IdentitySection
    connectivity: ConnectivitySection
    security: SecuritySection
    capabilities: CapabilitiesSection
    health: HealthSection
    metadata: MetadataSection
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    organization_id: str

    @classmethod
    def from_orm_model(cls, ds: Any, capabilities: Dict[str, Any]) -> "DataSourceResponse":
        """Construct response schema from SQLAlchemy database model and capabilities."""
        identity = IdentitySection(
            id=ds.id,
            name=ds.name,
            provider=ds.provider,
            environment=ds.environment,
        )
        connectivity = ConnectivitySection(
            host=ds.host,
            port=ds.port,
            connection_mode=ds.connection_mode,
            network_mode=ds.network_mode,
            provider_config=ds.provider_config or {},
        )
        security = SecuritySection(
            auth_method=ds.auth_method,
            tls=ds.tls,
            secret_reference=ds.secret_reference,
            access_policy=ds.access_policy,
        )
        caps = CapabilitiesSection(
            sql=capabilities.get("sql", False),
            schemas=capabilities.get("schemas", False),
            transactions=capabilities.get("transactions", False),
            relationships=capabilities.get("relationships", "none"),
        )
        health = HealthSection(
            status=ds.health_status,
            last_check=ds.health_last_check,
            last_error=ds.health_last_error,
        )

        meta_dict = ds.metadata_normalized or {}
        metadata = MetadataSection(
            databases=meta_dict.get("databases", []),
            schemas=meta_dict.get("schemas", []),
            objects=meta_dict.get("objects", []),
            columns=meta_dict.get("columns", []),
            relationships=meta_dict.get("relationships", []),
            statistics=meta_dict.get("statistics", {}),
        )

        return cls(
            identity=identity,
            connectivity=connectivity,
            security=security,
            capabilities=caps,
            health=health,
            metadata=metadata,
            description=ds.description,
            created_at=ds.created_at,
            updated_at=ds.updated_at,
            created_by=ds.created_by,
            organization_id=ds.organization_id,
        )

    model_config = {"from_attributes": True}
