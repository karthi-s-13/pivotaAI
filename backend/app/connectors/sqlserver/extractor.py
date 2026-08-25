"""
SQL Server Catalog Metadata Extractor.

Executes performant read-only system catalog queries to discover databases,
schemas, tables, views, columns, composite primary keys, foreign keys, and indexes.
"""

from typing import Any, Dict, List, Optional


class SQLServerMetadataExtractor:
    """Handles read-only metadata extraction for SQL Server databases."""

    def __init__(self, conn):
        self.conn = conn

    def get_databases(self) -> List[Dict[str, Any]]:
        """List all user databases."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                name,
                collation_name AS encoding
            FROM sys.databases
            WHERE name NOT IN ('master', 'model', 'msdb', 'tempdb')
            ORDER BY name;
            """
        )
        rows = cursor.fetchall()
        databases = [{"name": r[0], "encoding": r[1]} for r in rows]
        cursor.close()
        return databases

    def get_schemas(self) -> List[Dict[str, Any]]:
        """List user schemas in the database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                s.name,
                u.name AS owner
            FROM sys.schemas s
            JOIN sys.sysusers u ON s.principal_id = u.uid
            WHERE s.name NOT IN (
                'information_schema', 'sys', 'guest', 'INFORMATION_SCHEMA',
                'db_owner', 'db_accessadmin', 'db_securityadmin', 'db_ddladmin',
                'db_backupoperator', 'db_datareader', 'db_datawriter',
                'db_denydatareader', 'db_denydatawriter'
            )
            ORDER BY s.name;
            """
        )
        rows = cursor.fetchall()
        schemas = [{"name": r[0], "owner": r[1]} for r in rows]
        cursor.close()
        return schemas

    def get_objects(self, schema_name: str) -> List[Dict[str, Any]]:
        """List tables and views in a schema."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                o.name,
                CASE WHEN o.type = 'U' THEN 'TABLE' ELSE 'VIEW' END AS type,
                COALESCE(CAST(ep.value AS VARCHAR(max)), '') AS description,
                COALESCE(
                    (SELECT SUM(p.rows) 
                     FROM sys.partitions p 
                     WHERE p.object_id = o.object_id AND p.index_id IN (0, 1)), 
                    0
                ) AS estimated_row_count
            FROM sys.objects o
            LEFT JOIN sys.extended_properties ep
                ON o.object_id = ep.major_id 
                AND ep.minor_id = 0 
                AND ep.name = 'MS_Description'
            WHERE o.schema_id = SCHEMA_ID(?) 
              AND o.type IN ('U', 'V')
            ORDER BY o.name;
            """,
            (schema_name,),
        )
        rows = cursor.fetchall()
        objects = [
            {
                "name": r[0],
                "type": r[1],
                "description": r[2],
                "estimated_row_count": int(r[3]),
            }
            for r in rows
        ]
        cursor.close()
        return objects

    def get_columns(self, schema_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all columns for all tables in a schema, grouped by table name."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                o.name AS table_name,
                c.name AS name,
                c.column_id AS ordinal_position,
                t.name AS data_type,
                CASE 
                    WHEN t.name IN ('char', 'varchar', 'binary', 'varbinary') THEN t.name + '(' + CASE WHEN c.max_length = -1 THEN 'max' ELSE CAST(c.max_length AS VARCHAR) END + ')'
                    WHEN t.name IN ('nchar', 'nvarchar') THEN t.name + '(' + CASE WHEN c.max_length = -1 THEN 'max' ELSE CAST(c.max_length / 2 AS VARCHAR) END + ')'
                    WHEN t.name IN ('decimal', 'numeric') THEN t.name + '(' + CAST(c.precision AS VARCHAR) + ',' + CAST(c.scale AS VARCHAR) + ')'
                    ELSE t.name
                END AS native_type,
                c.is_nullable AS nullable,
                COALESCE(d.definition, '') AS default_value,
                COALESCE(CAST(ep.value AS VARCHAR(max)), '') AS description
            FROM sys.columns c
            JOIN sys.objects o ON c.object_id = o.object_id
            JOIN sys.types t ON c.user_type_id = t.user_type_id
            LEFT JOIN sys.default_constraints d ON c.default_object_id = d.object_id
            LEFT JOIN sys.extended_properties ep 
                ON c.object_id = ep.major_id 
                AND c.column_id = ep.minor_id 
                AND ep.name = 'MS_Description'
            WHERE o.schema_id = SCHEMA_ID(?) AND o.type IN ('U', 'V')
            ORDER BY o.name, c.column_id;
            """,
            (schema_name,),
        )
        rows = cursor.fetchall()

        columns_by_table = {}
        for r in rows:
            table_name = r[0]
            col_info = {
                "name": r[1],
                "ordinal_position": int(r[2]),
                "data_type": r[3],
                "native_type": r[4],
                "nullable": bool(r[5]),
                "default_value": r[6] if r[6] else None,
                "description": r[7],
            }
            if table_name not in columns_by_table:
                columns_by_table[table_name] = []
            columns_by_table[table_name].append(col_info)
        cursor.close()
        return columns_by_table

    def get_primary_keys(self, schema_name: str) -> Dict[str, Dict[str, Any]]:
        """Get primary keys for all tables, supporting composite keys."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                o.name AS table_name,
                i.name AS constraint_name,
                c.name AS column_name,
                ic.key_ordinal AS ordinal_position
            FROM sys.indexes i
            JOIN sys.objects o ON i.object_id = o.object_id
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON i.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.is_primary_key = 1
              AND o.schema_id = SCHEMA_ID(?)
            ORDER BY o.name, ic.key_ordinal;
            """,
            (schema_name,),
        )
        rows = cursor.fetchall()

        pks_by_table = {}
        for r in rows:
            table_name = r[0]
            c_name = r[1]
            col_name = r[2]
            if table_name not in pks_by_table:
                pks_by_table[table_name] = {"constraint_name": c_name, "columns": []}
            pks_by_table[table_name]["columns"].append(col_name)
        cursor.close()
        return pks_by_table

    def get_foreign_keys(self, schema_name: str) -> List[Dict[str, Any]]:
        """Get foreign keys/relationships, supporting composite keys."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                fk.name AS constraint_name,
                SCHEMA_NAME(fk.schema_id) AS from_schema,
                OBJECT_NAME(fk.parent_object_id) AS from_table,
                c1.name AS from_column,
                SCHEMA_NAME(t.schema_id) AS to_schema,
                OBJECT_NAME(fk.referenced_object_id) AS to_table,
                c2.name AS to_column,
                fk.update_referential_action_desc AS update_action,
                fk.delete_referential_action_desc AS delete_action,
                fkc.constraint_column_id AS key_position
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.columns c1 ON fkc.parent_object_id = c1.object_id AND fkc.parent_column_id = c1.column_id
            JOIN sys.columns c2 ON fkc.referenced_object_id = c2.object_id AND fkc.referenced_column_id = c2.column_id
            JOIN sys.tables t ON fk.referenced_object_id = t.object_id
            WHERE fk.schema_id = SCHEMA_ID(?)
            ORDER BY constraint_name, key_position;
            """,
            (schema_name,),
        )
        rows = cursor.fetchall()

        fks_dict = {}
        for r in rows:
            c_name = r[0]
            if c_name not in fks_dict:
                fks_dict[c_name] = {
                    "constraint_name": c_name,
                    "from_schema": r[1],
                    "from_table": r[2],
                    "from_columns": [],
                    "to_schema": r[4],
                    "to_table": r[5],
                    "to_columns": [],
                    "update_action": r[7].replace("_", " "),
                    "delete_action": r[8].replace("_", " "),
                }
            fks_dict[c_name]["from_columns"].append(r[3])
            fks_dict[c_name]["to_columns"].append(r[6])

        cursor.close()
        return list(fks_dict.values())

    def get_indexes(self, schema_name: str) -> List[Dict[str, Any]]:
        """Get indexes, supporting composite indexes."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                SCHEMA_NAME(o.schema_id) AS schema_name,
                o.name AS table_name,
                i.name AS index_name,
                c.name AS column_name,
                ic.key_ordinal AS column_position,
                i.is_unique,
                i.is_primary_key AS is_primary,
                i.type_desc AS index_type
            FROM sys.indexes i
            JOIN sys.objects o ON i.object_id = o.object_id
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON i.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.is_primary_key = 0 
              AND i.name IS NOT NULL
              AND o.schema_id = SCHEMA_ID(?)
              AND o.type = 'U'
            ORDER BY o.name, i.name, ic.key_ordinal;
            """,
            (schema_name,),
        )
        rows = cursor.fetchall()

        indexes_dict = {}
        for r in rows:
            idx_name = r[2]
            if idx_name not in indexes_dict:
                indexes_dict[idx_name] = {
                    "name": idx_name,
                    "table_name": r[1],
                    "schema_name": r[0],
                    "columns": [],
                    "unique": bool(r[5]),
                    "primary": bool(r[6]),
                    "type": r[7],
                }
            indexes_dict[idx_name]["columns"].append(r[3])

        cursor.close()
        return list(indexes_dict.values())
