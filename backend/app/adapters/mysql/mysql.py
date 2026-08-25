"""
MySQL Database Adapter.

Implements the DatasourceAdapter interface for MySQL/MariaDB databases using pymysql.
"""

import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pymysql
import pymysql.cursors

from app.adapters.base import ConnectionTestResult, DatasourceAdapter


class MySQLAdapter(DatasourceAdapter):
    """Adapter for MySQL databases."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = int(config.get("port", 3306))
        self.database_name = config.get("database_name", "")
        self.username = config.get("username")
        self.password = config.get("password")
        self.ssl_enabled = config.get("ssl_enabled", False)
        self._conn = None

    def _get_connection_params(self) -> dict:
        """Build pymysql connection parameters."""
        params = {
            "host": self.host,
            "port": self.port,
            "database": self.database_name,
            "connect_timeout": 10,
            "cursorclass": pymysql.cursors.DictCursor,
        }
        if self.username:
            params["user"] = self.username
        if self.password:
            params["password"] = self.password
        if self.ssl_enabled:
            params["ssl"] = {"ssl": {}}
        return params

    def validate_config(self) -> None:
        """Validate connection configurations."""
        if not self.host:
            raise ValueError("Host is required for MySQL connection")
        if not self.database_name:
            raise ValueError("Database name is required for MySQL connection")

    def connect(self) -> Any:
        """Establish connection and return the driver connection object."""
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(**self._get_connection_params())
        return self._conn

    def disconnect(self) -> None:
        """Close connection."""
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None

    def test_connection(self) -> ConnectionTestResult:
        """Test connection executing staged diagnostic checks."""
        steps = []
        start_total = time.time()

        # Step 1: Validation
        step_val = {"name": "validation", "status": "pending", "message": None, "latency_ms": None}
        steps.append(step_val)
        start_step = time.time()
        try:
            self.validate_config()
            step_val["status"] = "success"
            step_val["latency_ms"] = round((time.time() - start_step) * 1000, 2)
        except Exception as e:
            step_val["status"] = "failed"
            step_val["message"] = str(e)
            step_val["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            # Skip remaining
            for remaining in ["network", "authentication", "health"]:
                steps.append({"name": remaining, "status": "skipped"})
            return ConnectionTestResult(
                success=False,
                message=f"Validation failed: {str(e)}",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                steps=steps,
            )

        # Step 2: Network check
        step_net = {"name": "network", "status": "pending", "message": None, "latency_ms": None}
        steps.append(step_net)
        start_step = time.time()
        try:
            # TCP connection check
            socket.create_connection((self.host, self.port), timeout=5).close()
            step_net["status"] = "success"
            step_net["latency_ms"] = round((time.time() - start_step) * 1000, 2)
        except Exception as e:
            step_net["status"] = "failed"
            step_net["message"] = f"Network connection failed: {str(e)}"
            step_net["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            # Skip remaining
            for remaining in ["authentication", "health"]:
                steps.append({"name": remaining, "status": "skipped"})
            return ConnectionTestResult(
                success=False,
                message=f"Network connection failed: {str(e)}",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                steps=steps,
            )

        # Step 3: Authentication
        step_auth = {"name": "authentication", "status": "pending", "message": None, "latency_ms": None}
        steps.append(step_auth)
        start_step = time.time()
        conn = None
        try:
            conn = pymysql.connect(**self._get_connection_params())
            step_auth["status"] = "success"
            step_auth["latency_ms"] = round((time.time() - start_step) * 1000, 2)
        except Exception as e:
            step_auth["status"] = "failed"
            step_auth["message"] = f"Authentication failed: {str(e)}"
            step_auth["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            steps.append({"name": "health", "status": "skipped"})
            return ConnectionTestResult(
                success=False,
                message=f"Authentication failed: {str(e)}",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                steps=steps,
            )

        # Step 4: Health check / Query test
        step_health = {"name": "health", "status": "pending", "message": None, "latency_ms": None}
        steps.append(step_health)
        start_step = time.time()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                version_str = list(version.values())[0] if isinstance(version, dict) else version[0]
            conn.close()

            step_health["status"] = "success"
            step_health["latency_ms"] = round((time.time() - start_step) * 1000, 2)

            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                server_version=version_str,
                details={"host": self.host, "port": self.port, "database": self.database_name},
                steps=steps,
            )
        except Exception as e:
            step_health["status"] = "failed"
            step_health["message"] = f"Health query failed: {str(e)}"
            step_health["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            if conn and conn.open:
                conn.close()
            return ConnectionTestResult(
                success=False,
                message=f"Health query failed: {str(e)}",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                steps=steps,
            )

    def health_check(self) -> dict:
        """Perform health check."""
        start = time.time()
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            latency = (time.time() - start) * 1000
            return {
                "status": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latency_ms": round(latency, 2),
                "error": None,
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latency_ms": None,
                "error": str(e),
            }

    def list_databases(self) -> List[str]:
        """List all databases on the server."""
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES;")
            rows = cursor.fetchall()
            databases = []
            for row in rows:
                databases.append(list(row.values())[0])
        system_dbs = {"information_schema", "mysql", "performance_schema", "sys"}
        return [db for db in databases if db.lower() not in system_dbs]

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """MySQL doesn't support schemas. Return default."""
        return ["default"]

    def list_objects(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """List tables and views in the database."""
        db = database or self.database_name
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    table_name AS name,
                    CASE WHEN table_type = 'BASE TABLE' THEN 'TABLE' ELSE 'VIEW' END AS type,
                    COALESCE(table_comment, '') AS description,
                    COALESCE(table_rows, 0) AS estimated_row_count
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name;
                """,
                (db,),
            )
            rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_columns(
        self, database: Optional[str] = None, schema: Optional[str] = None, object_name: str = None
    ) -> List[dict]:
        """Get columns of a table."""
        db = database or self.database_name
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    column_name AS name,
                    column_type AS data_type,
                    is_nullable = 'YES' AS nullable,
                    ordinal_position,
                    column_default AS default_value,
                    COALESCE(column_comment, '') AS description,
                    column_key = 'PRI' AS is_primary_key,
                    EXISTS (
                        SELECT 1 
                        FROM information_schema.key_column_usage
                        WHERE referenced_table_name IS NOT NULL
                          AND table_schema = %s
                          AND table_name = %s
                          AND column_name = c.column_name
                    ) AS is_foreign_key
                FROM information_schema.columns c
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (db, object_name, db, object_name),
            )
            rows = cursor.fetchall()

        columns = []
        for row in rows:
            col = dict(row)
            columns.append(
                {
                    "name": col["name"],
                    "table_name": object_name,
                    "schema_name": schema or "default",
                    "database_name": db,
                    "data_type": col["data_type"],
                    "nullable": bool(col["nullable"]),
                    "ordinal_position": int(col["ordinal_position"]),
                    "default_value": str(col["default_value"]) if col["default_value"] is not None else None,
                    "description": col["description"],
                    "is_primary_key": bool(col["is_primary_key"]),
                    "is_foreign_key": bool(col["is_foreign_key"]),
                }
            )
        return columns

    def get_relationships(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """List foreign keys / relationships in the database."""
        db = database or self.database_name
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    table_name AS from_table,
                    column_name AS from_column,
                    referenced_table_name AS to_table,
                    referenced_column_name AS to_column
                FROM
                    information_schema.key_column_usage
                WHERE
                    referenced_table_name IS NOT NULL
                    AND table_schema = %s;
                """,
                (db,),
            )
            rows = cursor.fetchall()
        relationships = []
        for row in rows:
            rel = dict(row)
            relationships.append(
                {
                    "from_table": rel["from_table"],
                    "from_column": rel["from_column"],
                    "to_table": rel["to_table"],
                    "to_column": rel["to_column"],
                    "type": "foreign_key",
                }
            )
        return relationships

    def get_capabilities(self) -> dict:
        """Get capabilities of MySQL."""
        from app.adapters.registry import get_provider_capabilities

        return get_provider_capabilities("mysql")

    def discover(self) -> dict:
        """Orchestrate full metadata discovery."""
        databases = self.list_databases()
        schemas = self.list_schemas()

        all_objects = self.list_objects()
        all_columns = []

        for obj in all_objects:
            cols = self.get_columns(object_name=obj["name"])
            all_columns.extend(cols)

        all_relationships = self.get_relationships()

        stats = {
            "databases_count": len(databases),
            "schemas_count": len(schemas),
            "objects_count": len(all_objects),
            "columns_count": len(all_columns),
            "relationships_count": len(all_relationships),
        }

        return {
            "databases": databases,
            "schemas": schemas,
            "objects": all_objects,
            "columns": all_columns,
            "relationships": all_relationships,
            "statistics": stats,
        }
