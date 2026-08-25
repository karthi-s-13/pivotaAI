"""
PostgreSQL Connector.

Connects to PostgreSQL databases using psycopg2 and extracts metadata
from information_schema and pg_catalog.
"""

import time
from typing import List, Dict, Any

import psycopg2
import psycopg2.extras

from app.connectors.base import BaseConnector, ConnectionTestResult


class PostgreSQLConnector(BaseConnector):
    """Connector for PostgreSQL databases (local or remote)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.port = config.get("port", 5432)
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

    def _connect(self):
        """Establish a connection if not already connected."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self._get_connection_params())
        return self._conn

    def test_connection(self) -> ConnectionTestResult:
        """Test the PostgreSQL connection."""
        start = time.time()
        try:
            conn = psycopg2.connect(**self._get_connection_params())
            latency = (time.time() - start) * 1000

            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                latency_ms=round(latency, 2),
                server_version=version,
                details={"host": self.host, "port": self.port, "database": self.database_name},
            )
        except psycopg2.OperationalError as e:
            latency = (time.time() - start) * 1000
            error_msg = str(e).strip()
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {error_msg}",
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ConnectionTestResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                latency_ms=round(latency, 2),
            )

    def list_databases(self) -> List[str]:
        """List all accessible databases on the PostgreSQL server."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname;
        """)
        databases = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return databases

    def list_schemas(self, database: str) -> List[str]:
        """List non-system schemas in the connected database."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return schemas

    def list_tables(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """List all tables in a schema with metadata."""
        conn = self._connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT 
                t.table_name as name,
                t.table_type as type,
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
        """, (schema,))
        tables = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return tables

    def list_columns(self, database: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """List all columns in a table with full metadata."""
        conn = self._connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
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
        """, (schema, table))
        columns = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return columns

    def close(self) -> None:
        """Close the PostgreSQL connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None
