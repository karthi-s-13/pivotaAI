"""
Connector Platform Manager.

Registers and instantiates connector implementations. Wraps legacy adapters
for MySQL and MongoDB to maintain backward compatibility.
"""

from typing import Dict, Any, Type, List, Optional
import os

from app.connectors.base import BaseConnector, ConnectionTestResult, ConnectionTestStep
from app.adapters.registry import get_provider_capabilities


class WrappedAdapterConnector(BaseConnector):
    """Wraps legacy database adapters to conform to the new BaseConnector interface."""

    def __init__(self, provider: str, adapter_cls: Type, config: Dict[str, Any]):
        super().__init__(config)
        self.provider = provider
        self._adapter = adapter_cls(config)

    def validate_config(self) -> None:
        self._adapter.validate_config()

    def test_connection(self) -> ConnectionTestResult:
        res = self._adapter.test_connection()
        steps = []
        if hasattr(res, "steps") and res.steps:
            for step in res.steps:
                steps.append(
                    ConnectionTestStep(
                        name=step.get("name", ""),
                        status=step.get("status", ""),
                        message=step.get("message"),
                        latency_ms=step.get("latency_ms"),
                    )
                )
        else:
            # Fallback mock step for legacy compatibility
            steps.append(
                ConnectionTestStep(
                    name="authentication",
                    status="success" if res.success else "failed",
                    message=res.message if not res.success else None,
                    latency_ms=res.latency_ms,
                )
            )

        return ConnectionTestResult(
            success=res.success,
            message=res.message,
            latency_ms=res.latency_ms,
            server_version=res.server_version,
            details=res.details,
            steps=steps,
        )

    def get_server_info(self) -> Dict[str, Any]:
        return {
            "server_version": self.config.get("server_version", "Unknown"),
            "database": self.config.get("database_name", ""),
            "user": self.config.get("username", ""),
            "timezone": None,
        }

    def list_databases(self) -> List[str]:
        return self._adapter.list_databases()

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        return self._adapter.list_schemas(database)

    def list_objects(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # Map objects to expected keys
        objs = self._adapter.list_objects(database, schema)
        return objs

    def get_columns(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        object_name: str = None,
    ) -> List[Dict[str, Any]]:
        return self._adapter.get_columns(database, schema, object_name)

    def get_relationships(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self._adapter.get_relationships(database, schema)

    def get_capabilities(self) -> Dict[str, Any]:
        return self._adapter.get_capabilities()

    def close(self) -> None:
        self._adapter.disconnect()


_CONNECTOR_REGISTRY: Dict[str, Type[BaseConnector]] = {}


def register_connector(provider_type: str, connector_cls: Type[BaseConnector]) -> None:
    """Register a connector class for a provider type."""
    _CONNECTOR_REGISTRY[provider_type] = connector_cls


def get_connector(provider_type: str, config: Dict[str, Any]) -> BaseConnector:
    """
    Retrieve and initialize a database connector.

    All four providers (postgresql, mysql, sqlserver, mongodb) use native
    BaseConnector implementations. No legacy adapter wrapping is needed.
    """
    _lazy_import_connectors()

    if provider_type == "postgresql":
        from app.connectors.postgresql.connector import PostgreSQLConnector
        return PostgreSQLConnector(config)
    elif provider_type == "mysql":
        from app.connectors.mysql.connector import MySQLConnector
        return MySQLConnector(config)
    elif provider_type == "sqlserver":
        from app.connectors.sqlserver.connector import SQLServerConnector
        return SQLServerConnector(config)
    elif provider_type == "mongodb":
        from app.connectors.mongodb.connector import MongoDBConnector
        return MongoDBConnector(config)
    elif provider_type == "supabase":
        from app.connectors.supabase.connector import SupabaseConnector
        return SupabaseConnector(config)

    connector_cls = _CONNECTOR_REGISTRY.get(provider_type)
    if not connector_cls:
        supported = ", ".join(list(_CONNECTOR_REGISTRY.keys()))
        raise ValueError(
            f"Unsupported provider type: '{provider_type}'. "
            f"Supported providers: {supported}"
        )

    return connector_cls(config)


def get_supported_providers() -> List[str]:
    """Retrieve supported provider type strings."""
    return ["postgresql", "mysql", "sqlserver", "mongodb", "supabase"]


def _lazy_import_connectors() -> None:
    """Lazy imports to prevent circular dependency errors."""
    if "postgresql" not in _CONNECTOR_REGISTRY:
        from app.connectors.postgresql.connector import PostgreSQLConnector
        register_connector("postgresql", PostgreSQLConnector)
    if "mysql" not in _CONNECTOR_REGISTRY:
        from app.connectors.mysql.connector import MySQLConnector
        register_connector("mysql", MySQLConnector)
    if "sqlserver" not in _CONNECTOR_REGISTRY:
        from app.connectors.sqlserver.connector import SQLServerConnector
        register_connector("sqlserver", SQLServerConnector)
    if "mongodb" not in _CONNECTOR_REGISTRY:
        from app.connectors.mongodb.connector import MongoDBConnector
        register_connector("mongodb", MongoDBConnector)
    if "supabase" not in _CONNECTOR_REGISTRY:
        from app.connectors.supabase.connector import SupabaseConnector
        register_connector("supabase", SupabaseConnector)
