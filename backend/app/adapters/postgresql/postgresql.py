"""
PostgreSQL Database Adapter.

Implements the DatasourceAdapter interface for PostgreSQL databases using psycopg2.
"""

import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

from app.adapters.base import ConnectionTestResult, DatasourceAdapter


class PostgreSQLAdapter(DatasourceAdapter):
    """Adapter for PostgreSQL databases."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = int(config.get("port", 5432))
        self.database_name = config.get("database_name", "")
        self.username = config.get("username")
        self.password = config.get("password")
        self.ssl_enabled = config.get("ssl_enabled", False)
        self._conn = None

    def _get_connection_params(self) -> dict:
        """Build psycopg2 connection parameters."""
        params = {
            "host": self.host,
            "port": self.port,
            "dbname": self.database_name,
            "connect_timeout": 10,
        }
        if self.username:
            params["user"] = self.username
        if self.password:
            params["password"] = self.password
        if self.ssl_enabled:
            params["sslmode"] = "require"
        return params

    def validate_config(self) -> None:
        """Validate connection configurations."""
        if not self.host:
            raise ValueError("Host is required for PostgreSQL connection")
        if not self.database_name:
            raise ValueError("Database name is required for PostgreSQL connection")

    def connect(self) -> Any:
        """Establish connection and return the driver connection object."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self._get_connection_params())
        return self._conn

    def disconnect(self) -> None:
        """Close connection."""
        if self._conn and not self._conn.closed:
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
            # Skip subsequent steps
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
            # Perform TCP handshake check to verify basic connectivity
            socket.create_connection((self.host, self.port), timeout=5).close()
            step_net["status"] = "success"
            step_net["latency_ms"] = round((time.time() - start_step) * 1000, 2)
        except Exception as e:
            step_net["status"] = "failed"
            step_net["message"] = f"Network connection failed: {str(e)}"
            step_net["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            # Skip authentication & health
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
            conn = psycopg2.connect(**self._get_connection_params())
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

        # Step 4: Health check / Server version query
        step_health = {"name": "health", "status": "pending", "message": None, "latency_ms": None}
        steps.append(step_health)
        start_step = time.time()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            step_health["status"] = "success"
            step_health["latency_ms"] = round((time.time() - start_step) * 1000, 2)

            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                server_version=version,
                details={"host": self.host, "port": self.port, "database": self.database_name},
                steps=steps,
            )
        except Exception as e:
            step_health["status"] = "failed"
            step_health["message"] = f"Health query failed: {str(e)}"
            step_health["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            if conn and not conn.closed:
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
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
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
        cursor = conn.cursor()
        cursor.execute(
            "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"
        )
        databases = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return databases

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """List non-system schemas in the database."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
            """
        )
        schemas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return schemas

    def list_objects(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """List tables and views in a schema."""
        target_schema = schema or "public"
        conn = self.connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT 
                t.table_name as name,
                CASE WHEN t.table_type = 'BASE TABLE' THEN 'TABLE' ELSE 'VIEW' END as type,
                COALESCE(
                    obj_description(
                        (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass
                    ), 
                    ''
                ) as description,
                COALESCE(s.n_live_tup, 0) as estimated_row_count
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables s 
                ON t.table_schema = s.schemaname 
                AND t.table_name = s.relname
            WHERE t.table_schema = %s
            ORDER BY t.table_name;
            """,
            (target_schema,),
        )
        objects = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return objects

    def get_columns(
        self, database: Optional[str] = None, schema: Optional[str] = None, object_name: str = None
    ) -> List[dict]:
        """Get columns of a table."""
        target_schema = schema or "public"
        conn = self.connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT 
                c.column_name as name,
                c.data_type,
                c.is_nullable = 'YES' as nullable,
                c.ordinal_position,
                c.column_default as default_value,
                COALESCE(
                    col_description(
                        (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass,
                        c.ordinal_position
                    ),
                    ''
                ) as description,
                EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = c.table_schema
                        AND tc.table_name = c.table_name
                        AND kcu.column_name = c.column_name
                ) as is_primary_key,
                EXISTS (
                    SELECT 1 FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = c.table_schema
                        AND tc.table_name = c.table_name
                        AND kcu.column_name = c.column_name
                ) as is_foreign_key
            FROM information_schema.columns c
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position;
            """,
            (target_schema, object_name),
        )
        columns = []
        for row in cursor.fetchall():
            col = dict(row)
            columns.append(
                {
                    "name": col["name"],
                    "table_name": object_name,
                    "schema_name": target_schema,
                    "database_name": database or self.database_name,
                    "data_type": col["data_type"],
                    "nullable": col["nullable"],
                    "ordinal_position": col["ordinal_position"],
                    "default_value": str(col["default_value"]) if col["default_value"] is not None else None,
                    "description": col["description"],
                    "is_primary_key": col["is_primary_key"],
                    "is_foreign_key": col["is_foreign_key"],
                }
            )
        cursor.close()
        return columns

    def get_relationships(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """List foreign keys / relationships in a schema."""
        target_schema = schema or "public"
        conn = self.connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT
                tc.table_name AS from_table,
                kcu.column_name AS from_column,
                ccu.table_name AS to_table,
                ccu.column_name AS to_column
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = %s;
            """,
            (target_schema,),
        )
        relationships = []
        for row in cursor.fetchall():
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
        cursor.close()
        return relationships

    def get_capabilities(self) -> dict:
        """Get capabilities of PostgreSQL."""
        from app.adapters.registry import get_provider_capabilities

        return get_provider_capabilities("postgresql")

    def discover(self) -> dict:
        """Orchestrate full metadata discovery."""
        databases = self.list_databases()
        schemas = self.list_schemas()

        all_objects = []
        all_columns = []
        all_relationships = []

        for sch in schemas:
            objs = self.list_objects(schema=sch)
            all_objects.extend(objs)

            for obj in objs:
                cols = self.get_columns(schema=sch, object_name=obj["name"])
                all_columns.extend(cols)

            relations = self.get_relationships(schema=sch)
            all_relationships.extend(relations)

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
