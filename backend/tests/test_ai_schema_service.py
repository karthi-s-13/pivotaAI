"""
Unit Tests for AI Schema formatting and document extraction.
"""

from app.ai.schema.schema_service import format_schema_for_llm, generate_schema_documents


def test_format_schema_for_llm():
    """Verify that metadata schema is formatted correctly for the LLM prompt."""
    schema_data = {
        "provider": "postgresql",
        "data_source_name": "Ecommerce DB",
        "data_source_description": "Main store backend database",
        "databases": [
            {
                "name": "ecommerce",
                "owner": "postgres",
                "encoding": "UTF8",
                "schemas": [
                    {
                        "name": "public",
                        "owner": "db_admin",
                        "tables": [
                            {
                                "name": "customers",
                                "type": "TABLE",
                                "description": "Customer accounts table",
                                "row_count_estimate": 500,
                                "columns": [
                                    {"name": "id", "data_type": "integer", "nullable": False, "is_primary_key": True},
                                    {"name": "name", "data_type": "varchar", "nullable": True, "is_primary_key": False},
                                    {"name": "email", "data_type": "varchar", "nullable": True, "is_primary_key": False},
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        "relationships": [
            {
                "from_table": "orders",
                "from_columns": ["customer_id"],
                "to_table": "customers",
                "to_columns": ["id"]
            }
        ]
    }

    formatted = format_schema_for_llm(schema_data)
    
    assert "Provider: postgresql" in formatted
    assert "Description: Main store backend database" in formatted
    assert "Database: ecommerce (Owner: postgres) (Encoding: UTF8)" in formatted
    assert "Schema: public (Owner: db_admin)" in formatted
    assert "customers (TABLE)" in formatted
    assert "Customer accounts table" in formatted
    assert "- id integer NOT NULL [PK]" in formatted
    assert "orders.customer_id → customers.id" in formatted


def test_generate_schema_documents():
    """Verify schema document representation builder for embeddings."""
    schema_data = {
        "provider": "postgresql",
        "data_source_name": "Ecommerce DB",
        "data_source_description": "Main store backend database",
        "databases": [
            {
                "name": "ecommerce",
                "owner": "postgres",
                "encoding": "UTF8",
                "schemas": [
                    {
                        "name": "public",
                        "owner": "db_admin",
                        "tables": [
                            {
                                "name": "customers",
                                "type": "TABLE",
                                "description": "Customer accounts table",
                                "row_count_estimate": 500,
                                "columns": [
                                    {"name": "id", "data_type": "integer", "nullable": False, "is_primary_key": True},
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        "relationships": []
    }

    docs = generate_schema_documents(schema_data, "ds-123")
    assert len(docs) == 1
    assert docs[0]["id"] == "ds-123:ecommerce:public:customers"
    assert docs[0]["metadata"]["table"] == "customers"
    assert "Data Source Description: Main store backend database" in docs[0]["content"]
    assert "Database: ecommerce (Owner: postgres) (Encoding: UTF8)" in docs[0]["content"]
    assert "Schema: public (Owner: db_admin)" in docs[0]["content"]
    assert "Table: customers (TABLE)" in docs[0]["content"]
    assert "id integer [PRIMARY KEY]" in docs[0]["content"]

