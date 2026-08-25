"""
PostgreSQL Connector Class.

Combines configuration normalization, diagnostics testing, and catalog queries.
"""

from typing import Dict, Any, List, Optional
import psycopg2

from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.postgresql.config import PostgreSQLConnectionConfig
from app.connectors.postgresql.diagnostics import run_diagnostics
from app.connectors.postgresql.extractor import PostgreSQLMetadataExtractor


class PostgreSQLConnector(BaseConnector):
    """Production-grade connector for PostgreSQL databases."""

    provider = "postgresql"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Normalize incoming settings into canonical config model
        self.pg_config = PostgreSQLConnectionConfig.from_dict(config)
        self._conn = None

    def _get_connection(self):
        """Establish connection if not active, caching it."""
        if self._conn is None or self._conn.closed:
            params = self.pg_config.to_psycopg2_params()
            self._conn = psycopg2.connect(**params)
        return self._conn

    def validate_config(self) -> None:
        """Validate settings configuration parameters."""
        # Config validation throws Pydantic ValidationError or custom exceptions
        if not self.pg_config.host:
            raise ValueError("Host is required for PostgreSQL connection")
        if not self.pg_config.database:
            raise ValueError("Database is required for PostgreSQL connection")

    def test_connection(self) -> ConnectionTestResult:
        """Run the structured 8-step connection diagnostics workflow."""
        return run_diagnostics(self.pg_config)

    def get_server_info(self) -> Dict[str, Any]:
        """Fetch general information on server session status."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version(), current_setting('TimeZone'), current_user;")
        row = cursor.fetchone()
        cursor.close()
        return {
            "server_version": row[0],
            "database": self.pg_config.database,
            "user": row[2],
            "timezone": row[1],
        }

    def list_databases(self) -> List[str]:
        """List all non-template databases."""
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)
        dbs = extractor.get_databases()
        return [db["name"] for db in dbs]

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """List schemas in the database."""
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)
        # Filters pg_catalog/information_schema by default
        schemas = extractor.get_schemas()
        return [s["name"] for s in schemas]

    def list_objects(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tables and views in the schema."""
        target_schema = schema or self.pg_config.schema_name or "public"
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)
        return extractor.get_objects(target_schema)

    def get_columns(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        object_name: str = None,
    ) -> List[Dict[str, Any]]:
        """List columns inside a table/view, mapping keys."""
        target_schema = schema or self.pg_config.schema_name or "public"
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)

        # Pull all columns for this schema
        columns_by_table = extractor.get_columns(target_schema)
        table_cols = columns_by_table.get(object_name, [])

        # Fetch Primary & Foreign Key lists to assign keys
        pks_by_table = extractor.get_primary_keys(target_schema)
        pk_cols = pks_by_table.get(object_name, {}).get("columns", [])

        # Foreign Key mapping
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
        """Retrieve relationship lists for the schema."""
        target_schema = schema or self.pg_config.schema_name or "public"
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)
        fks = extractor.get_foreign_keys(target_schema)

        # Convert to expected API format
        relationships = []
        for fk in fks:
            # Multi-column/composite keys mapped individually or as lists
            # Since existing frontends map individual keys, let's map each column pair
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
        """Fetch PostgreSQL capabilities registry settings."""
        from app.adapters.registry import get_provider_capabilities

        return get_provider_capabilities("postgresql")

    def close(self) -> None:
        """Close connection cleanly."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None
