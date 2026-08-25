"""
Adapter Registry.

Registers and instantiates database adapters, and manages the capability registry.
"""

import json
import os
from typing import Any, Dict, List, Type

from app.adapters.base import DatasourceAdapter

_ADAPTER_REGISTRY: Dict[str, Type[DatasourceAdapter]] = {}
_CAPABILITIES_CACHE: Dict[str, Dict[str, Any]] = {}


def load_capabilities() -> Dict[str, Dict[str, Any]]:
    """Load capability profiles from capabilities.json."""
    global _CAPABILITIES_CACHE
    if not _CAPABILITIES_CACHE:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(dir_path, "capabilities.json")
        try:
            with open(json_path, "r") as f:
                _CAPABILITIES_CACHE = json.load(f)
        except Exception:
            # Fallback hardcoded defaults if JSON is missing or unreadable
            _CAPABILITIES_CACHE = {
                "postgresql": {"sql": True, "schemas": True, "transactions": True, "relationships": "full"},
                "supabase": {
                    "sql": True, "schemas": True, "transactions": True, "relationships": "full",
                    "functions": True, "triggers": True, "extensions": True, "rls": True,
                    "managed_cloud": True, "connection_pooler": True, "vector_extension_detection": True,
                    "schema_inference": False
                },
                "mysql": {"sql": True, "schemas": False, "transactions": True, "relationships": "full"},
                "sqlserver": {
                    "sql": True, "schemas": True, "transactions": True, "relationships": "full",
                    "databases": True, "tables": True, "views": True, "columns": True, "indexes": True,
                    "primary_keys": True, "foreign_keys": True, "constraints": True,
                    "stored_procedures": True, "functions": True, "triggers": True,
                    "sequences": True, "synonyms": True
                },
                "mongodb": {
                    "sql": False, "schemas": False, "collections": True,
                    "databases": True, "indexes": True, "schema_inference": True,
                    "nested_documents": True, "arrays": True, "transactions": False,
                    "relationships": "inferred", "views": True, "fixed_schema": False,
                    "category": "nosql",
                },
            }
    return _CAPABILITIES_CACHE


def register_adapter(provider: str, adapter_cls: Type[DatasourceAdapter]) -> None:
    """Register an adapter class for a provider type."""
    _ADAPTER_REGISTRY[provider] = adapter_cls


def get_adapter(provider: str, config: Dict[str, Any]) -> DatasourceAdapter:
    """
    Get an initialized adapter instance for the given provider.

    Args:
        provider: The provider name (e.g. "postgresql", "mysql", "mongodb").
        config: Connection configuration parameters.

    Returns:
        An instance of DatasourceAdapter.
    """
    _lazy_import_adapters()

    adapter_cls = _ADAPTER_REGISTRY.get(provider)
    if not adapter_cls:
        supported = ", ".join(_ADAPTER_REGISTRY.keys())
        raise ValueError(
            f"Unsupported provider: '{provider}'. "
            f"Supported providers: {supported}"
        )

    # Initialize adapter
    adapter = adapter_cls(config)
    # Automatically validate config on instantiation
    adapter.validate_config()
    return adapter


def get_provider_capabilities(provider: str) -> Dict[str, Any]:
    """Retrieve capabilities list for a provider from capabilities registry."""
    caps = load_capabilities()
    if provider not in caps:
        raise ValueError(f"No capabilities registered for provider '{provider}'")
    return caps[provider]


def get_supported_providers() -> List[str]:
    """Retrieve a list of supported providers."""
    _lazy_import_adapters()
    return list(_ADAPTER_REGISTRY.keys())


def _lazy_import_adapters() -> None:
    """Lazy-load adapter modules to register them to prevent circular imports."""
    if not _ADAPTER_REGISTRY:
        from app.adapters.mongodb.mongodb import MongoDBAdapter
        from app.adapters.mysql.mysql import MySQLAdapter
        from app.adapters.postgresql.postgresql import PostgreSQLAdapter

        register_adapter("postgresql", PostgreSQLAdapter)
        register_adapter("mysql", MySQLAdapter)
        register_adapter("mongodb", MongoDBAdapter)
