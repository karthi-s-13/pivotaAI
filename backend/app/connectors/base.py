"""
Base Database Connector Interface.

All database provider connectors must implement this interface to ensure provider-agnostic core operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConnectionTestStep:
    """Result of a single staged connection testing step."""
    name: str  # e.g., "validation", "network", "tls", "authentication", "database_access", "metadata_access"
    status: str  # "success", "failed", "skipped", "pending"
    message: Optional[str] = None
    latency_ms: Optional[float] = None


@dataclass
class ConnectionTestResult:
    """Result of testing a database connection with diagnostics details."""
    success: bool
    message: str
    latency_ms: Optional[float] = None
    server_version: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    steps: List[ConnectionTestStep] = field(default_factory=list)


class BaseConnector(ABC):
    """
    Abstract Base Class defining the connector interface for database providers.
    """

    provider: str

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with connection configuration.

        Args:
            config: Normalized connection configuration parameters.
        """
        self.config = config

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate the connection configuration.

        Raises:
            ConnectorError or sub-class: If configuration is invalid.
        """
        pass

    @abstractmethod
    def test_connection(self) -> ConnectionTestResult:
        """
        Test the database connection executing staged diagnostic checks.

        Returns:
            ConnectionTestResult containing connection status, latency, and steps.
        """
        pass

    @abstractmethod
    def get_server_info(self) -> Dict[str, Any]:
        """
        Fetch server information (version, current DB, timezone).

        Returns:
            Dict containing:
                "server_version": str
                "database": str
                "user": str
                "timezone": Optional[str]
        """
        pass

    @abstractmethod
    def list_databases(self) -> List[str]:
        """
        List all accessible databases.
        """
        pass

    @abstractmethod
    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """
        List all schemas in a database.
        """
        pass

    @abstractmethod
    def list_objects(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all tables/views in a schema/database.

        Returns:
            list of dicts with: name, type ("TABLE" | "VIEW"), estimated_row_count, description
        """
        pass

    @abstractmethod
    def get_columns(self, database: Optional[str] = None, schema: Optional[str] = None, object_name: str = None) -> List[Dict[str, Any]]:
        """
        List all columns in a table/view.

        Returns:
            list of dicts with: name, data_type, nullable, ordinal_position,
            is_primary_key, is_foreign_key, default_value, description
        """
        pass

    @abstractmethod
    def get_relationships(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all foreign key/relationships in a schema/database.

        Returns:
            list of dicts with: from_table, from_column, to_table, to_column, type ("foreign_key")
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Retrieve the capabilities dictionary of the database provider.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the active connection.
        """
        pass
