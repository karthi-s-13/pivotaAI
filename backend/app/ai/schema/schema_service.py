"""
AI Schema Service.

Retrieves database schema information using the existing Pivota metadata catalog.
Formats schema data into structured text documents for embedding and LLM context.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.metadata import (
    DatabaseMetadata,
    SchemaMetadata,
    ObjectMetadata,
    ColumnMetadata,
    RelationshipMetadata,
)

logger = logging.getLogger(__name__)


def get_schema_for_data_source(
    db: Session,
    data_source_id: str,
    organization_id: str,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve full schema information for a data source from the metadata catalog.

    Returns a structured dict with databases, schemas, tables, columns, and relationships.
    """
    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == data_source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        return {}

    result = {
        "provider": ds.provider,
        "data_source_name": ds.name,
        "data_source_description": ds.description or "",
        "databases": [],
    }

    # Query databases
    db_query = db.query(DatabaseMetadata).filter(
        DatabaseMetadata.data_source_id == data_source_id,
        DatabaseMetadata.organization_id == organization_id,
    )
    if database_name:
        db_query = db_query.filter(DatabaseMetadata.name == database_name)

    databases = db_query.all()

    for db_meta in databases:
        db_info = {
            "name": db_meta.name,
            "owner": db_meta.owner or "",
            "encoding": db_meta.encoding or "",
            "schemas": [],
        }

        # Query schemas
        schema_query = db.query(SchemaMetadata).filter(
            SchemaMetadata.database_id == db_meta.id,
            SchemaMetadata.organization_id == organization_id,
        )
        if schema_name:
            schema_query = schema_query.filter(SchemaMetadata.name == schema_name)

        schemas = schema_query.all()

        for sch_meta in schemas:
            schema_info = {
                "name": sch_meta.name,
                "owner": sch_meta.owner or "",
                "tables": [],
            }

            # Query objects (tables/views)
            objects = (
                db.query(ObjectMetadata)
                .filter(
                    ObjectMetadata.schema_id == sch_meta.id,
                    ObjectMetadata.organization_id == organization_id,
                )
                .all()
            )

            for obj_meta in objects:
                # Query columns
                columns = (
                    db.query(ColumnMetadata)
                    .filter(
                        ColumnMetadata.object_id == obj_meta.id,
                        ColumnMetadata.organization_id == organization_id,
                    )
                    .order_by(ColumnMetadata.ordinal_position)
                    .all()
                )

                table_info = {
                    "name": obj_meta.name,
                    "type": obj_meta.type,
                    "description": obj_meta.description or "",
                    "row_count_estimate": obj_meta.row_count_estimate,
                    "columns": [
                        {
                            "name": col.name,
                            "data_type": col.data_type,
                            "nullable": col.nullable,
                            "is_primary_key": col.is_primary_key,
                            "is_foreign_key": col.is_foreign_key,
                            "default_value": col.default_value,
                            "description": col.description or "",
                        }
                        for col in columns
                    ],
                }
                schema_info["tables"].append(table_info)

            db_info["schemas"].append(schema_info)

        result["databases"].append(db_info)

    # Query relationships
    relationships = (
        db.query(RelationshipMetadata)
        .filter(
            RelationshipMetadata.data_source_id == data_source_id,
            RelationshipMetadata.organization_id == organization_id,
        )
        .all()
    )

    # Resolve relationship table names
    rel_list = []
    for rel in relationships:
        from_obj = db.query(ObjectMetadata).filter(ObjectMetadata.id == rel.from_object_id).first()
        to_obj = db.query(ObjectMetadata).filter(ObjectMetadata.id == rel.to_object_id).first()
        if from_obj and to_obj:
            rel_list.append({
                "from_table": from_obj.name,
                "from_columns": rel.from_columns,
                "to_table": to_obj.name,
                "to_columns": rel.to_columns,
            })

    result["relationships"] = rel_list
    return result


def format_schema_for_llm(
    schema_data: Dict[str, Any],
    relevant_tables: Optional[List[str]] = None,
) -> str:
    """
    Format schema information into a compact text context for the LLM.

    If relevant_tables is provided, only include those tables.
    """
    if not schema_data:
        return "No schema information available."

    lines = []
    lines.append("DATABASE CONTEXT\n")
    lines.append(f"Provider: {schema_data.get('provider', 'unknown')}")
    lines.append(f"Data Source: {schema_data.get('data_source_name', 'unknown')}")
    if schema_data.get("data_source_description"):
        lines.append(f"Description: {schema_data['data_source_description']}")

    for db_info in schema_data.get("databases", []):
        db_line = f"\nDatabase: {db_info['name']}"
        if db_info.get("owner"):
            db_line += f" (Owner: {db_info['owner']})"
        if db_info.get("encoding"):
            db_line += f" (Encoding: {db_info['encoding']})"
        lines.append(db_line)

        for schema_info in db_info.get("schemas", []):
            sch_line = f"Schema: {schema_info['name']}"
            if schema_info.get("owner"):
                sch_line += f" (Owner: {schema_info['owner']})"
            lines.append(sch_line)
            lines.append("")

            tables = schema_info.get("tables", [])
            if relevant_tables:
                tables = [t for t in tables if t["name"] in relevant_tables]

            if not tables:
                lines.append("(No matching tables)")
                continue

            lines.append("TABLES\n")
            for table in tables:
                lines.append(f"  {table['name']} ({table['type']})")
                if table.get("description"):
                    lines.append(f"    Description: {table['description']}")
                if table.get("row_count_estimate"):
                    lines.append(f"    Estimated rows: {table['row_count_estimate']}")

                lines.append("    Columns:")
                for col in table.get("columns", []):
                    pk = " [PK]" if col.get("is_primary_key") else ""
                    fk = " [FK]" if col.get("is_foreign_key") else ""
                    nullable = " NULL" if col.get("nullable") else " NOT NULL"
                    lines.append(
                        f"      - {col['name']} {col['data_type']}{nullable}{pk}{fk}"
                    )
                lines.append("")

    # Relationships
    rels = schema_data.get("relationships", [])
    if rels:
        lines.append("RELATIONSHIPS\n")
        for rel in rels:
            from_cols = ", ".join(rel["from_columns"])
            to_cols = ", ".join(rel["to_columns"])
            lines.append(
                f"  {rel['from_table']}.{from_cols} → {rel['to_table']}.{to_cols}"
            )

    return "\n".join(lines)


def generate_schema_documents(
    schema_data: Dict[str, Any],
    data_source_id: str,
) -> List[Dict[str, Any]]:
    """
    Generate individual text documents for each table for embedding.

    Returns a list of dicts with 'id', 'content', 'metadata'.
    """
    documents = []

    provider = schema_data.get("provider", "unknown")
    ds_name = schema_data.get("data_source_name", "unknown")
    ds_desc = schema_data.get("data_source_description", "")

    for db_info in schema_data.get("databases", []):
        db_name = db_info["name"]

        for schema_info in db_info.get("schemas", []):
            sch_name = schema_info["name"]

            for table in schema_info.get("tables", []):
                doc_id = f"{data_source_id}:{db_name}:{sch_name}:{table['name']}"
                lines = []
                lines.append(f"Provider: {provider}")
                lines.append(f"Data Source: {ds_name}")
                if ds_desc:
                    lines.append(f"Data Source Description: {ds_desc}")
                
                db_line = f"Database: {db_name}"
                if db_info.get("owner"):
                    db_line += f" (Owner: {db_info['owner']})"
                if db_info.get("encoding"):
                    db_line += f" (Encoding: {db_info['encoding']})"
                lines.append(db_line)

                sch_line = f"Schema: {sch_name}"
                if schema_info.get("owner"):
                    sch_line += f" (Owner: {schema_info['owner']})"
                lines.append(sch_line)
                
                lines.append(f"Table: {table['name']} ({table['type']})")

                if table.get("description"):
                    lines.append(f"Description: {table['description']}")
                if table.get("row_count_estimate"):
                    lines.append(f"Estimated rows: {table['row_count_estimate']}")

                lines.append("\nColumns:")
                for col in table.get("columns", []):
                    pk = " [PRIMARY KEY]" if col.get("is_primary_key") else ""
                    fk = " [FOREIGN KEY]" if col.get("is_foreign_key") else ""
                    lines.append(f"  {col['name']} {col['data_type']}{pk}{fk}")

                # Find relationships for this table
                for rel in schema_data.get("relationships", []):
                    if rel["from_table"] == table["name"]:
                        from_cols = ", ".join(rel["from_columns"])
                        to_cols = ", ".join(rel["to_columns"])
                        lines.append(
                            f"\nRelationship: {table['name']}.{from_cols} → "
                            f"{rel['to_table']}.{to_cols}"
                        )
                    elif rel["to_table"] == table["name"]:
                        from_cols = ", ".join(rel["from_columns"])
                        to_cols = ", ".join(rel["to_columns"])
                        lines.append(
                            f"\nReferenced by: {rel['from_table']}.{from_cols} → "
                            f"{table['name']}.{to_cols}"
                        )

                content = "\n".join(lines)
                documents.append({
                    "id": doc_id,
                    "content": content,
                    "metadata": {
                        "data_source_id": data_source_id,
                        "provider": provider,
                        "database": db_name,
                        "schema": sch_name,
                        "table": table["name"],
                        "type": table["type"],
                    },
                })

    return documents


def get_table_names_for_data_source(
    db: Session,
    data_source_id: str,
    organization_id: str,
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
) -> List[str]:
    """Get a flat list of table names for a data source."""
    query = (
        db.query(ObjectMetadata.name)
        .filter(
            ObjectMetadata.data_source_id == data_source_id,
            ObjectMetadata.organization_id == organization_id,
        )
    )

    if database_name and schema_name:
        # Join through schema and database
        query = (
            query
            .join(SchemaMetadata, ObjectMetadata.schema_id == SchemaMetadata.id)
            .join(DatabaseMetadata, SchemaMetadata.database_id == DatabaseMetadata.id)
            .filter(
                DatabaseMetadata.name == database_name,
                SchemaMetadata.name == schema_name,
            )
        )

    return [row[0] for row in query.all()]
