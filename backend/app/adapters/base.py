"""
Base Datasource Adapter Interface.

All database provider adapters must implement this interface to ensure provider-agnostic core operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConnectionTestResult:
    """Result of testing a database connection with staged diagnostics."""

    success: bool
    message: str
    latency_ms: Optional[float] = None
    server_version: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)


class DatasourceAdapter(ABC):
    """
    Abstract Base Class defining the adapter interface for all database providers in Pivota.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the adapter with connection configuration.

        Args:
            config: Connection configuration parameters.
        """
        self.config = config

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate the connection configuration.

        Raises:
            ValueError: If required config settings are missing or invalid.
        """
        pass

    @abstractmethod
    def test_connection(self) -> ConnectionTestResult:
        """
        Test the database connection executing staged diagnostic checks.

        Returns:
            ConnectionTestResult containing connection success, steps, latency, and details.
        """
        pass

    @abstractmethod
    def connect(self) -> Any:
        """
        Establish connection and return the driver connection/client object.
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Close the active database connection.
        """
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """
        Perform a simple health check query.

        Returns:
            dict containing:
                "status": "connected" | "disconnected" | "error"
                "timestamp": ISO datetime string
                "latency_ms": float or None
                "error": str or None
        """
        pass

    @abstractmethod
    def discover(self) -> dict:
        """
        Run database/schema/object discovery, returning normalized metadata.

        Returns:
            dict containing:
                databases: list of database names
                schemas: list of schema names
                objects: list of object dictionaries
                columns: list of column dictionaries
                relationships: list of relationship dictionaries
                statistics: dictionary of metadata statistics
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
    def list_objects(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """
        List all tables/collections in a schema/database.

        Returns:
            list of dicts with: name, type ("TABLE" | "COLLECTION"), estimated_row_count, description
        """
        pass

    @abstractmethod
    def get_columns(self, database: Optional[str] = None, schema: Optional[str] = None, object_name: str = None) -> List[dict]:
        """
        List all columns/fields in a table/collection.

        Returns:
            list of dicts with: name, data_type, nullable, ordinal_position,
            is_primary_key, is_foreign_key, default_value, description
        """
        pass

    @abstractmethod
    def get_relationships(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """
        Retrieve all foreign key/relationships in a schema/database.

        Returns:
            list of dicts with: from_table, from_column, to_table, to_column, type ("foreign_key")
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> dict:
        """
        Retrieve the capabilities dictionary of the database provider.
        """
        pass
