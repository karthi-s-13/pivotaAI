"""
Connector Registry.

Delegates provider-mapping operations to the ConnectorManager.
"""

from typing import Dict, Any
from app.connectors.base import BaseConnector
from app.connectors.manager import get_connector as manager_get_connector, get_supported_providers as manager_get_supported_providers


def get_connector(provider_type: str, config: Dict[str, Any]) -> BaseConnector:
    """
    Get a connector instance for the given provider type.
    """
    return manager_get_connector(provider_type, config)


def get_supported_providers() -> list[str]:
    """Return list of supported provider type strings."""
    return manager_get_supported_providers()
