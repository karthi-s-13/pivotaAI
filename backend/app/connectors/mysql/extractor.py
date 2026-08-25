"""
MySQL Catalog Metadata Extractor.

Executes performant read-only system catalog queries to discover databases,
tables, views, columns, composite primary keys, foreign keys, and indexes.
"""

from typing import Any, Dict, List, Optional
import pymysql.cursors


class MySQLMetadataExtractor:
    """Handles read-only metadata extraction for MySQL databases."""

    def __init__(self, conn):
        self.conn = conn

    def get_databases(self) -> List[Dict[str, Any]]:
        """List all databases, excluding system tables by default."""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    schema_name AS name,
                    DEFAULT_CHARACTER_SET_NAME AS encoding
                FROM information_schema.SCHEMATA
                ORDER BY schema_name;
                """
            )
            databases = cursor.fetchall()

        system_dbs = {"information_schema", "mysql", "performance_schema", "sys"}
        return [db for db in databases if db["name"].lower() not in system_dbs]

    def get_schemas(self) -> List[Dict[str, Any]]:
        """MySQL does not support separate schemas; returns a compliance dummy."""
        return [{"name": "default", "owner": None}]

    def get_objects(self, database_name: str) -> List[Dict[str, Any]]:
        """List tables and views in a database."""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
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
                (database_name,),
            )
            objects = cursor.fetchall()
        return objects

    def get_columns(self, database_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get columns for all tables in a database, grouping by table name."""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    table_name,
                    column_name AS name,
                    ordinal_position,
                    data_type,
                    column_type AS native_type,
                    is_nullable = 'YES' AS nullable,
                    column_default AS default_value,
                    COALESCE(column_comment, '') AS description
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position;
                """,
                (database_name,),
            )
            rows = cursor.fetchall()

        columns_by_table = {}
        for row in rows:
            table_name = row.pop("table_name")
            if table_name not in columns_by_table:
                columns_by_table[table_name] = []
            columns_by_table[table_name].append(row)
        return columns_by_table

    def get_primary_keys(self, database_name: str) -> Dict[str, Dict[str, Any]]:
        """Get primary keys for all tables, supporting composite keys."""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    table_name,
                    constraint_name,
                    column_name,
                    ordinal_position
                FROM information_schema.key_column_usage
                WHERE constraint_name = 'PRIMARY' AND table_schema = %s
                ORDER BY table_name, ordinal_position;
                """,
                (database_name,),
            )
            rows = cursor.fetchall()

        pks_by_table = {}
        for row in rows:
            table_name = row["table_name"]
            c_name = row["constraint_name"]
            col_name = row["column_name"]
            if table_name not in pks_by_table:
                pks_by_table[table_name] = {"constraint_name": c_name, "columns": []}
            pks_by_table[table_name]["columns"].append(col_name)
        return pks_by_table

    def get_foreign_keys(self, database_name: str) -> List[Dict[str, Any]]:
        """Get foreign keys/relationships, supporting composite keys."""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    k.constraint_name,
                    k.table_schema AS from_schema,
                    k.table_name AS from_table,
                    k.column_name AS from_column,
                    k.referenced_table_schema AS to_schema,
                    k.referenced_table_name AS to_table,
                    k.referenced_column_name AS to_column,
                    r.update_rule AS update_action,
                    r.delete_rule AS delete_action,
                    k.ordinal_position AS key_position
                FROM information_schema.key_column_usage k
                JOIN information_schema.referential_constraints r
                  ON k.constraint_name = r.constraint_name
                  AND k.table_schema = r.constraint_schema
                WHERE k.referenced_table_name IS NOT NULL
                  AND k.table_schema = %s
                ORDER BY k.constraint_name, k.ordinal_position;
                """,
                (database_name,),
            )
            rows = cursor.fetchall()

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

    def get_indexes(self, database_name: str) -> List[Dict[str, Any]]:
        """Get indexes, supporting composite indexes."""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    table_schema AS schema_name,
                    table_name,
                    index_name,
                    column_name,
                    seq_in_index AS column_position,
                    non_unique = 0 AS is_unique,
                    index_name = 'PRIMARY' AS is_primary,
                    index_type
                FROM information_schema.statistics
                WHERE table_schema = %s
                ORDER BY table_name, index_name, seq_in_index;
                """,
                (database_name,),
            )
            rows = cursor.fetchall()

        indexes_dict = {}
        for r in rows:
            idx_name = r["index_name"]
            if idx_name not in indexes_dict:
                indexes_dict[idx_name] = {
                    "name": idx_name,
                    "table_name": r["table_name"],
                    "schema_name": r["schema_name"],
                    "columns": [],
                    "unique": bool(r["is_unique"]),
                    "primary": bool(r["is_primary"]),
                    "type": r["index_type"],
                }
            indexes_dict[idx_name]["columns"].append(r["column_name"])

        return list(indexes_dict.values())
