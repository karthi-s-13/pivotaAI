"""
PostgreSQL Catalog Metadata Extractor.

Executes performant read-only system catalog queries to discover databases,
schemas, tables, views, columns, composite primary keys, foreign keys, and indexes.
"""

from typing import Any, Dict, List, Optional
import psycopg2
import psycopg2.extras
from app.connectors.postgresql.config import PostgreSQLConnectionConfig


class PostgreSQLMetadataExtractor:
    """Handles read-only metadata extraction for PostgreSQL databases."""

    def __init__(self, conn):
        self.conn = conn

    def get_databases(self) -> List[Dict[str, Any]]:
        """List all non-template databases."""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT 
                datname AS name,
                pg_get_userbyid(datdba) AS owner,
                pg_encoding_to_char(encoding) AS encoding
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname;
            """
        )
        databases = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return databases

    def get_schemas(self, exclude_system: bool = True) -> List[Dict[str, Any]]:
        """List schemas in the connected database."""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if exclude_system:
            cursor.execute(
                """
                SELECT 
                    nspname AS name,
                    pg_get_userbyid(nspowner) AS owner
                FROM pg_namespace
                WHERE nspname NOT IN (
                    'pg_catalog', 'information_schema', 'pg_toast', 
                    'pg_temp_1', 'pg_toast_temp_1'
                ) AND nspname NOT LIKE 'pg_temp_%' AND nspname NOT LIKE 'pg_toast_temp_%'
                ORDER BY nspname;
                """
            )
        else:
            cursor.execute(
                """
                SELECT 
                    nspname AS name,
                    pg_get_userbyid(nspowner) AS owner
                FROM pg_namespace
                ORDER BY nspname;
                """
            )
        schemas = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return schemas

    def get_objects(self, schema_name: str) -> List[Dict[str, Any]]:
        """List tables and views in a specific schema."""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT 
                t.table_name AS name,
                CASE WHEN t.table_type = 'BASE TABLE' THEN 'TABLE' ELSE 'VIEW' END AS type,
                COALESCE(
                    obj_description(
                        (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass
                    ), 
                    ''
                ) AS description,
                COALESCE(s.n_live_tup, 0) AS estimated_row_count
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables s 
                ON t.table_schema = s.schemaname 
                AND t.table_name = s.relname
            WHERE t.table_schema = %s
            ORDER BY t.table_name;
            """,
            (schema_name,),
        )
        objects = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return objects

    def get_columns(self, schema_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all columns for all tables in a schema.
        Returns a dict mapping table_name -> List of columns.
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT 
                c.table_name,
                c.column_name AS name,
                c.ordinal_position,
                c.data_type,
                CASE 
                    WHEN c.character_maximum_length IS NOT NULL THEN c.data_type || '(' || c.character_maximum_length || ')'
                    WHEN c.numeric_precision IS NOT NULL AND c.numeric_scale IS NOT NULL THEN c.data_type || '(' || c.numeric_precision || ',' || c.numeric_scale || ')'
                    WHEN c.numeric_precision IS NOT NULL THEN c.data_type || '(' || c.numeric_precision || ')'
                    ELSE c.data_type
                END AS native_type,
                c.is_nullable = 'YES' AS nullable,
                c.column_default AS default_value,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                COALESCE(
                    col_description(
                        (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass,
                        c.ordinal_position
                    ),
                    ''
                ) AS description
            FROM information_schema.columns c
            WHERE c.table_schema = %s
            ORDER BY c.table_name, c.ordinal_position;
            """,
            (schema_name,),
        )
        columns_by_table = {}
        for row in cursor.fetchall():
            row_dict = dict(row)
            table_name = row_dict.pop("table_name")
            if table_name not in columns_by_table:
                columns_by_table[table_name] = []
            columns_by_table[table_name].append(row_dict)
        cursor.close()
        return columns_by_table

    def get_primary_keys(self, schema_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Find primary keys for all tables in a schema, supporting composite keys.
        Returns a dict mapping table_name -> { "constraint_name": str, "columns": List[str] }
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT 
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                kcu.ordinal_position
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = %s
            ORDER BY tc.table_name, kcu.ordinal_position;
            """,
            (schema_name,),
        )
        pks_by_table = {}
        for row in cursor.fetchall():
            table_name = row["table_name"]
            c_name = row["constraint_name"]
            col_name = row["column_name"]
            if table_name not in pks_by_table:
                pks_by_table[table_name] = {"constraint_name": c_name, "columns": []}
            pks_by_table[table_name]["columns"].append(col_name)
        cursor.close()
        return pks_by_table

    def get_foreign_keys(self, schema_name: str) -> List[Dict[str, Any]]:
        """
        Find foreign keys/relationships in a schema, supporting composite foreign keys.
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT
                c.conname AS constraint_name,
                ns1.nspname AS from_schema,
                tbl1.relname AS from_table,
                a1.attname AS from_column,
                ns2.nspname AS to_schema,
                tbl2.relname AS to_table,
                a2.attname AS to_column,
                CASE c.confupdtype 
                    WHEN 'a' THEN 'NO ACTION' WHEN 'r' THEN 'RESTRICT' 
                    WHEN 'c' THEN 'CASCADE' WHEN 'n' THEN 'SET NULL' WHEN 'd' THEN 'SET DEFAULT' 
                END AS update_action,
                CASE c.confdeltype 
                    WHEN 'a' THEN 'NO ACTION' WHEN 'r' THEN 'RESTRICT' 
                    WHEN 'c' THEN 'CASCADE' WHEN 'n' THEN 'SET NULL' WHEN 'd' THEN 'SET DEFAULT' 
                END AS delete_action,
                pos.n AS key_position
            FROM pg_constraint c
            JOIN pg_class tbl1 ON tbl1.oid = c.conrelid
            JOIN pg_namespace ns1 ON ns1.oid = tbl1.relnamespace
            JOIN pg_class tbl2 ON tbl2.oid = c.confrelid
            JOIN pg_namespace ns2 ON ns2.oid = tbl2.relnamespace
            JOIN LATERAL unnest(c.conkey) WITH ORDINALITY pos(attnum, n) ON true
            JOIN pg_attribute a1 ON a1.attrelid = c.conrelid AND a1.attnum = pos.attnum
            JOIN pg_attribute a2 ON a2.attrelid = c.confrelid AND a2.attnum = c.confkey[pos.n]
            WHERE c.contype = 'f' AND ns1.nspname = %s
            ORDER BY constraint_name, key_position;
            """,
            (schema_name,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()

        # Group rows by constraint_name to handle composite foreign keys
        fks_dict = {}
        for r in rows:
            c_name = r["constraint_name"]
            if c_name not in fks_dict:
                fks_dict[c_name] = {
                    "constraint_name": c_name,
                    "from_schema": r["from_schema"],
                    "from_table": r["from_table"],
                    "from_columns": [],
                    "to_schema": r["to_schema"],
                    "to_table": r["to_table"],
                    "to_columns": [],
                    "update_action": r["update_action"],
                    "delete_action": r["delete_action"],
                }
            fks_dict[c_name]["from_columns"].append(r["from_column"])
            fks_dict[c_name]["to_columns"].append(r["to_column"])

        return list(fks_dict.values())

    def get_indexes(self, schema_name: str) -> List[Dict[str, Any]]:
        """
        Find indexes in a schema, supporting composite indexes.
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT
                ns.nspname AS schema_name,
                tbl.relname AS table_name,
                idx.relname AS index_name,
                a.attname AS column_name,
                pos.n AS column_position,
                i.indisunique AS is_unique,
                i.indisprimary AS is_primary,
                am.amname AS index_type
            FROM pg_index i
            JOIN pg_class tbl ON tbl.oid = i.indrelid
            JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
            JOIN pg_class idx ON idx.oid = i.indexrelid
            JOIN pg_am am ON am.oid = idx.relam
            JOIN LATERAL unnest(i.indkey) WITH ORDINALITY pos(attnum, n) ON true
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = pos.attnum
            WHERE ns.nspname = %s
            ORDER BY schema_name, table_name, index_name, column_position;
            """,
            (schema_name,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()

        # Group rows by index_name
        indexes_dict = {}
        for r in rows:
            idx_name = r["index_name"]
            if idx_name not in indexes_dict:
                indexes_dict[idx_name] = {
                    "name": idx_name,
                    "table_name": r["table_name"],
                    "schema_name": r["schema_name"],
                    "columns": [],
                    "unique": r["is_unique"],
                    "primary": r["is_primary"],
                    "type": r["index_type"],
                }
            indexes_dict[idx_name]["columns"].append(r["column_name"])

        return list(indexes_dict.values())
