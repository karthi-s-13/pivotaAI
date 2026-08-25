"""
MySQL Connector Class.

Combines configuration normalization, diagnostics testing, and catalog queries.
"""

from typing import Dict, Any, List, Optional
import pymysql
import pymysql.cursors

from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.mysql.config import MySQLConnectionConfig
from app.connectors.mysql.diagnostics import run_diagnostics
from app.connectors.mysql.extractor import MySQLMetadataExtractor


class MySQLConnector(BaseConnector):
    """Production-grade connector for MySQL databases."""

    provider = "mysql"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mysql_config = MySQLConnectionConfig.from_dict(config)
        self._conn = None

    def _get_connection(self):
        """Establish connection if not active, caching it."""
        if self._conn is None or not self._conn.open:
            params = self.mysql_config.to_pymysql_params()
            params["cursorclass"] = pymysql.cursors.DictCursor
            self._conn = pymysql.connect(**params)
        return self._conn

    def validate_config(self) -> None:
        """Validate configuration settings."""
        if not self.mysql_config.host:
            raise ValueError("Host is required for MySQL connection")
        if not self.mysql_config.database:
            raise ValueError("Database is required for MySQL connection")

    def test_connection(self) -> ConnectionTestResult:
        """Run connection diagnostics."""
        return run_diagnostics(self.mysql_config)

    def get_server_info(self) -> Dict[str, Any]:
        """Fetch MySQL server status information."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT version(), @@time_zone, CURRENT_USER();")
            row = cursor.fetchone()
            vals = list(row.values()) if isinstance(row, dict) else list(row)
        return {
            "server_version": vals[0],
            "database": self.mysql_config.database,
            "user": vals[2],
            "timezone": vals[1],
        }

    def list_databases(self) -> List[str]:
        """List user databases on the server."""
        conn = self._get_connection()
        extractor = MySQLMetadataExtractor(conn)
        dbs = extractor.get_databases()
        return [db["name"] for db in dbs]

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """List schemas. MySQL maps schemas/databases synonymously."""
        conn = self._get_connection()
        extractor = MySQLMetadataExtractor(conn)
        schemas = extractor.get_schemas()
        return [s["name"] for s in schemas]

    def list_objects(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tables and views."""
        target_db = database or self.mysql_config.database
        conn = self._get_connection()
        extractor = MySQLMetadataExtractor(conn)
        return extractor.get_objects(target_db)

    def get_columns(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        object_name: str = None,
    ) -> List[Dict[str, Any]]:
        """List columns inside a table, mapping keys."""
        target_db = database or self.mysql_config.database
        conn = self._get_connection()
        extractor = MySQLMetadataExtractor(conn)

        # Pull all columns for this database
        columns_by_table = extractor.get_columns(target_db)
        table_cols = columns_by_table.get(object_name, [])

        # Fetch Primary Key list
        pks_by_table = extractor.get_primary_keys(target_db)
        pk_cols = pks_by_table.get(object_name, {}).get("columns", [])

        # Fetch Foreign Key list
        fks = extractor.get_foreign_keys(target_db)
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
        """List foreign keys in the database."""
        target_db = database or self.mysql_config.database
        conn = self._get_connection()
        extractor = MySQLMetadataExtractor(conn)
        fks = extractor.get_foreign_keys(target_db)

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
        """Fetch MySQL capabilities registry settings."""
        from app.adapters.registry import get_provider_capabilities
        return get_provider_capabilities("mysql")

    def close(self) -> None:
        """Close connection cleanly."""
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None
