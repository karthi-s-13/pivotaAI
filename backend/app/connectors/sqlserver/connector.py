"""
SQL Server Connector Class.

Combines configuration normalization, diagnostics testing, and catalog queries.
"""

from typing import Dict, Any, List, Optional
import pyodbc

from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.sqlserver.config import SQLServerConnectionConfig
from app.connectors.sqlserver.diagnostics import run_diagnostics
from app.connectors.sqlserver.extractor import SQLServerMetadataExtractor


class SQLServerConnector(BaseConnector):
    """Production-grade connector for Microsoft SQL Server databases."""

    provider = "sqlserver"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sql_config = SQLServerConnectionConfig.from_dict(config)
        self._conn = None

    def _get_connection(self):
        """Establish connection if not active, caching it."""
        if self._conn is None:
            conn_str = self.sql_config.to_odbc_connection_string()
            self._conn = pyodbc.connect(conn_str, timeout=self.sql_config.connect_timeout)
        return self._conn

    def validate_config(self) -> None:
        """Validate configuration settings."""
        if not self.sql_config.host:
            raise ValueError("Host is required for SQL Server connection")
        if not self.sql_config.database:
            raise ValueError("Database is required for SQL Server connection")
        if self.sql_config.authentication_method == "sql_server" and not self.sql_config.username:
            raise ValueError("Username is required for SQL Authentication")

    def test_connection(self) -> ConnectionTestResult:
        """Run connection diagnostics."""
        return run_diagnostics(self.sql_config)

    def get_server_info(self) -> Dict[str, Any]:
        """Fetch SQL Server status information."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION, @@SERVICENAME, ORIGINAL_LOGIN(), DB_NAME();")
        row = cursor.fetchone()
        version, service, login, db_name = row[0], row[1], row[2], row[3]
        cursor.close()
        return {
            "server_version": version.split("\n")[0] if version else "SQL Server",
            "database": db_name,
            "user": login,
            "timezone": None,
        }

    def list_databases(self) -> List[str]:
        """List user databases on the server."""
        conn = self._get_connection()
        extractor = SQLServerMetadataExtractor(conn)
        dbs = extractor.get_databases()
        return [db["name"] for db in dbs]

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """List user schemas."""
        conn = self._get_connection()
        extractor = SQLServerMetadataExtractor(conn)
        schemas = extractor.get_schemas()
        return [s["name"] for s in schemas]

    def list_objects(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tables and views."""
        target_schema = schema or "dbo"
        conn = self._get_connection()
        extractor = SQLServerMetadataExtractor(conn)
        return extractor.get_objects(target_schema)

    def get_columns(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        object_name: str = None,
    ) -> List[Dict[str, Any]]:
        """List columns inside a table, mapping keys."""
        target_schema = schema or "dbo"
        conn = self._get_connection()
        extractor = SQLServerMetadataExtractor(conn)

        # Pull all columns for this schema
        columns_by_table = extractor.get_columns(target_schema)
        table_cols = columns_by_table.get(object_name, [])

        # Fetch Primary Key list
        pks_by_table = extractor.get_primary_keys(target_schema)
        pk_cols = pks_by_table.get(object_name, {}).get("columns", [])

        # Fetch Foreign Key list
        fks = extractor.get_foreign_keys(target_schema)
        fk_cols = []
        for fk in fks:
            if fk["from_table"] == object_name:
                fk_cols.extend(fk["from_columns"])

        # Format column dictionaries
        formatted = []
        for col in table_cols:
            col_name = col["name"]
            formatted.append(
                {
                    "name": col_name,
                    "data_type": col["data_type"],
                    "nullable": col["nullable"],
                    "ordinal_position": col["ordinal_position"],
                    "is_primary_key": col_name in pk_cols,
                    "is_foreign_key": col_name in fk_cols,
                    "default_value": col["default_value"],
                    "description": col["description"],
                }
            )
        return formatted

    def get_relationships(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List foreign keys in the schema."""
        target_schema = schema or "dbo"
        conn = self._get_connection()
        extractor = SQLServerMetadataExtractor(conn)
        fks = extractor.get_foreign_keys(target_schema)

        relationships = []
        for fk in fks:
            for i in range(len(fk["from_columns"])):
                relationships.append(
                    {
                        "constraint_name": fk["constraint_name"],
                        "from_table": fk["from_table"],
                        "from_column": fk["from_columns"][i],
                        "to_table": fk["to_table"],
                        "to_column": fk["to_columns"][i],
                        "type": "foreign_key",
                        "update_action": fk["update_action"],
                        "delete_action": fk["delete_action"],
                    }
                )
        return relationships

    def get_capabilities(self) -> Dict[str, Any]:
        """Fetch SQL Server capabilities registry settings."""
        from app.adapters.registry import get_provider_capabilities
        return get_provider_capabilities("sqlserver")

    def close(self) -> None:
        """Close connection cleanly."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
