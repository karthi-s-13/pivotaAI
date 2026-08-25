"""
Supabase Connector.

Connects to Supabase cloud PostgreSQL, discovers its database/schema catalogs,
metadata, vector columns, RLS security configurations, functions, triggers, and extensions.
"""

import re
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.supabase.config import SupabaseConnectionConfig
from app.connectors.supabase.diagnostics import run_diagnostics
from app.connectors.postgresql.extractor import PostgreSQLMetadataExtractor


class SupabaseConnector(BaseConnector):
    """Production-grade Supabase metadata connector leveraging PostgreSQL reuse."""

    provider = "supabase"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.supabase_config = SupabaseConnectionConfig.from_dict(config)
        self._conn = None

    def _get_connection(self):
        """Establish connection if not active, caching it."""
        if self._conn is None or self._conn.closed:
            conn_params = self.supabase_config.to_psycopg2_params()
            self._conn = psycopg2.connect(**conn_params)
        return self._conn

    def validate_config(self) -> None:
        """Validate connection configuration settings."""
        self.supabase_config.validate()

    def test_connection(self) -> ConnectionTestResult:
        """Run step-by-step diagnostic connection checklist."""
        return run_diagnostics(self.supabase_config)

    def get_server_info(self) -> Dict[str, Any]:
        """Fetch database server version metadata."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT version(), current_setting('TimeZone'), current_user;")
            row = cursor.fetchone()
            version, timezone_str, current_user = row[0], row[1], row[2]
            return {
                "server_version": version,
                "database": self.supabase_config.database,
                "user": current_user,
                "timezone": timezone_str,
            }
        finally:
            cursor.close()

    def list_databases(self) -> List[str]:
        """List databases on the server."""
        # Supabase projects generally restrict discovery to target database (typically 'postgres')
        return [self.supabase_config.database]

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """List schemas, applying configurations for included, excluded, and platform schemas."""
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)
        raw_schemas = extractor.get_schemas()

        # Config extraction
        p_config = self.supabase_config.provider_config
        include_managed = p_config.get("include_provider_managed_schemas", False)
        included = p_config.get("included_schemas", [])
        excluded = p_config.get("excluded_schemas", [])

        # Define platform managed schemas
        platform_schemas = {
            "auth",
            "storage",
            "realtime",
            "extensions",
            "graphql",
            "supabase",
            "pg_catalog",
            "information_schema",
            "pg_toast",
        }

        filtered_schemas = []
        for s in raw_schemas:
            # Respect explicit filters if provided
            if included and s not in included:
                continue
            if excluded and s in excluded:
                continue

            # Check for platform schemas exclusion
            if s in platform_schemas and not include_managed:
                if s != "public":  # Public schema should always be queried unless excluded explicitly
                    continue

            filtered_schemas.append(s)

        return filtered_schemas

    def list_objects(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tables and views inside the target schema, retrieving RLS details."""
        target_schema = schema or "public"
        conn = self._get_connection()

        # Fetch standard tables and views using PostgreSQL metadata extractor
        extractor = PostgreSQLMetadataExtractor(conn)
        objects = extractor.get_objects(target_schema)

        # Query RLS (Row Level Security) metadata on tables in schema
        rls_map = {}
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            rls_query = """
                SELECT 
                    relname AS table_name,
                    relrowsecurity AS rls_enabled,
                    relforcerowsecurity AS rls_forced
                FROM pg_class c
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s AND c.relkind = 'r';
            """
            cursor.execute(rls_query, (target_schema,))
            rls_rows = cursor.fetchall()
            for row in rls_rows:
                rls_map[row["table_name"]] = {
                    "rls_enabled": row["rls_enabled"],
                    "rls_forced": row["rls_forced"]
                }
        except Exception:
            pass
        finally:
            cursor.close()

        # Fetch RLS policy definitions
        policies_map = {}
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            pol_query = """
                SELECT 
                    policyname AS policy_name,
                    tablename AS table_name,
                    cmd AS command,
                    roles::text AS roles
                FROM pg_policies
                WHERE schemaname = %s;
            """
            cursor.execute(pol_query, (target_schema,))
            pol_rows = cursor.fetchall()
            for row in pol_rows:
                tbl = row["table_name"]
                if tbl not in policies_map:
                    policies_map[tbl] = []
                policies_map[tbl].append({
                    "policy_name": row["policy_name"],
                    "command": row["command"],
                    "roles": row["roles"]
                })
        except Exception:
            pass
        finally:
            cursor.close()

        # Decorate metadata response with RLS information and platform management indicators
        formatted_objects = []
        platform_schemas = {"auth", "storage", "realtime", "extensions", "graphql", "supabase"}

        for obj in objects:
            name = obj["name"]
            rls_info = rls_map.get(name, {"rls_enabled": False, "rls_forced": False})
            policies = policies_map.get(name, [])

            is_platform = target_schema in platform_schemas

            provider_metadata = {
                "project_ref": self.supabase_config.project_ref,
                "deployment": "managed_cloud",
                "connection_mode": "pooler" if self.supabase_config.pooler_enabled else "direct",
                "schema_role": "platform" if is_platform else "application",
                "provider_managed": is_platform,
                "rls_enabled": rls_info["rls_enabled"],
                "rls_forced": rls_info["rls_forced"],
                "policy_count": len(policies),
                "policies": policies
            }

            formatted_objects.append({
                "name": name,
                "type": obj["type"],
                "description": obj.get("description", ""),
                "estimated_row_count": obj.get("estimated_row_count", 0),
                "provider_metadata": provider_metadata
            })

        return formatted_objects

    def get_columns(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        object_name: str = None,
    ) -> List[Dict[str, Any]]:
        """List columns inside the table, parsing dimensions for pgvector elements."""
        target_schema = schema or "public"
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)

        # Retrieve standard columns
        columns = extractor.get_columns(target_schema, object_name)

        formatted = []
        for col in columns:
            data_type = col["data_type"]
            dimensions = None

            # Detect vector dimensions from vector data type (e.g. vector(384) or vector(1536))
            if "vector" in data_type.lower():
                match = re.search(r"vector\((\d+)\)", data_type.lower())
                if match:
                    dimensions = int(match.group(1))

            col_data = col.copy()
            if dimensions is not None:
                col_data["vector_dimensions"] = dimensions

            formatted.append(col_data)

        return formatted

    def get_relationships(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch foreign key constraints using standard PostgreSQL metadata extractor."""
        target_schema = schema or "public"
        conn = self._get_connection()
        extractor = PostgreSQLMetadataExtractor(conn)
        return extractor.get_relationships(target_schema)

    # ── Supabase-Specific Metadata Discovery ───────────────────────────────

    def get_extensions(self) -> List[Dict[str, Any]]:
        """List installed PostgreSQL extensions (e.g. pgvector, pgcrypto)."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = """
                SELECT 
                    extname AS extension_name,
                    extversion AS version,
                    n.nspname AS schema
                FROM pg_extension e
                JOIN pg_namespace n ON e.extnamespace = n.oid;
            """
            cursor.execute(query)
            return list(cursor.fetchall())
        except Exception:
            return []
        finally:
            cursor.close()

    def get_triggers(self, schema: str = "public") -> List[Dict[str, Any]]:
        """List active table triggers in the schema."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = """
                SELECT 
                    tgname AS trigger_name,
                    c.relname AS table_name,
                    CASE tgtype::integer & 2 WHEN 2 THEN 'BEFORE' ELSE 'AFTER' END AS timing,
                    CASE tgtype::integer & 4 WHEN 4 THEN 'INSERT' WHEN 8 THEN 'DELETE' WHEN 16 THEN 'UPDATE' ELSE 'ALL' END AS event,
                    CASE tgenabled WHEN 'D' THEN false ELSE true END AS enabled
                FROM pg_trigger t
                JOIN pg_class c ON t.tgrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = %s AND NOT tgisinternal;
            """
            cursor.execute(query, (schema,))
            return list(cursor.fetchall())
        except Exception:
            return []
        finally:
            cursor.close()

    def get_functions(self, schema: str = "public") -> List[Dict[str, Any]]:
        """List user-defined routines and stored functions in the schema."""
        conn = self._get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            query = """
                SELECT 
                    p.proname AS function_name,
                    n.nspname AS schema,
                    pg_get_function_arguments(p.oid) AS arguments,
                    pg_get_function_result(p.oid) AS return_type
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                LEFT JOIN pg_language l ON p.prolang = l.oid
                WHERE n.nspname = %s AND l.lanname IN ('sql', 'plpgsql');
            """
            cursor.execute(query, (schema,))
            return list(cursor.fetchall())
        except Exception:
            return []
        finally:
            cursor.close()

    def get_capabilities(self) -> Dict[str, Any]:
        """Fetch capabilities profile settings."""
        from app.adapters.registry import get_provider_capabilities
        return get_provider_capabilities("supabase")

    def close(self) -> None:
        """Close connection cleanly."""
        if self._conn and not self._conn.closed:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
