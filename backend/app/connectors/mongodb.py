"""
MongoDB Connector.

Connects to MongoDB instances (local or Atlas cloud) using pymongo
and extracts metadata by sampling collections and inferring structure.
"""

import time
from typing import List, Dict, Any

from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
    ConfigurationError,
)

from app.connectors.base import BaseConnector, ConnectionTestResult


class MongoDBConnector(BaseConnector):
    """Connector for MongoDB databases (local or Atlas cloud)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.port = config.get("port", 27017)
        self.connection_string = config.get("connection_string")
        self.auth_source = config.get("auth_source", "admin")
        self.replica_set = config.get("replica_set")
        self._client = None

    def _get_client(self) -> MongoClient:
        """Create or return existing MongoClient."""
        if self._client is None:
            if self.connection_string:
                # Use connection string (Atlas or full URI)
                self._client = MongoClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                )
            else:
                # Build connection from individual params
                kwargs = {
                    "host": self.host,
                    "port": self.port,
                    "serverSelectionTimeoutMS": 10000,
                    "connectTimeoutMS": 10000,
                }
                if self.username and self.password:
                    kwargs["username"] = self.username
                    kwargs["password"] = self.password
                    kwargs["authSource"] = self.auth_source
                if self.replica_set:
                    kwargs["replicaSet"] = self.replica_set
                if self.ssl_enabled:
                    kwargs["tls"] = True
                    kwargs["tlsAllowInvalidCertificates"] = True

                self._client = MongoClient(**kwargs)

        return self._client

    def test_connection(self) -> ConnectionTestResult:
        """Test the MongoDB connection."""
        start = time.time()
        try:
            client = self._get_client()
            # The ping command forces a connection attempt
            result = client.admin.command("ping")
            latency = (time.time() - start) * 1000

            # Get server info
            server_info = client.server_info()
            version = server_info.get("version", "unknown")

            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                latency_ms=round(latency, 2),
                server_version=f"MongoDB {version}",
                details={
                    "host": self.host,
                    "port": self.port,
                    "database": self.database_name,
                },
            )
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            latency = (time.time() - start) * 1000
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                latency_ms=round(latency, 2),
            )
        except (OperationFailure, ConfigurationError) as e:
            latency = (time.time() - start) * 1000
            return ConnectionTestResult(
                success=False,
                message=f"Authentication/config error: {str(e)}",
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
        """List all accessible databases."""
        client = self._get_client()
        # Filter out system databases
        system_dbs = {"admin", "local", "config"}
        all_dbs = client.list_database_names()
        return [db for db in all_dbs if db not in system_dbs]

    def list_schemas(self, database: str) -> List[str]:
        """
        MongoDB doesn't have schemas in the SQL sense.
        Return a single 'default' schema for compatibility.
        """
        return ["default"]

    def list_tables(self, database: str, schema: str) -> List[Dict[str, Any]]:
        """List all collections in a database (collections → tables)."""
        client = self._get_client()
        db = client[database]
        collections = []

        for name in db.list_collection_names():
            # Get estimated document count
            try:
                count = db[name].estimated_document_count()
            except Exception:
                count = 0

            collections.append({
                "name": name,
                "type": "COLLECTION",
                "description": "",
                "estimated_row_count": count,
            })

        return sorted(collections, key=lambda x: x["name"])

    def list_columns(self, database: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """
        Infer document fields by sampling documents from a collection.
        MongoDB is schema-less, so we sample to discover the structure.
        """
        client = self._get_client()
        db = client[database]
        collection = db[table]

        # Sample up to 100 documents to infer fields
        sample_docs = list(collection.find().limit(100))

        if not sample_docs:
            return []

        # Aggregate all field names and their types
        field_info: Dict[str, Dict[str, Any]] = {}

        for doc in sample_docs:
            self._extract_fields(doc, field_info, prefix="")

        # Convert to column list
        columns = []
        for idx, (field_name, info) in enumerate(sorted(field_info.items()), start=1):
            columns.append({
                "name": field_name,
                "data_type": info.get("type", "unknown"),
                "nullable": True,  # MongoDB fields are inherently optional
                "ordinal_position": idx,
                "default_value": None,
                "description": "",
                "is_primary_key": field_name == "_id",
                "is_foreign_key": False,
            })

        return columns

    def _extract_fields(
        self, doc: dict, field_info: Dict[str, Dict[str, Any]], prefix: str
    ) -> None:
        """Recursively extract field names and types from a document."""
        for key, value in doc.items():
            full_key = f"{prefix}.{key}" if prefix else key
            python_type = type(value).__name__

            # Map Python types to readable types
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "double",
                "bool": "boolean",
                "datetime": "datetime",
                "ObjectId": "objectId",
                "list": "array",
                "dict": "object",
                "NoneType": "null",
                "Decimal128": "decimal",
            }
            mapped_type = type_map.get(python_type, python_type)

            if full_key not in field_info:
                field_info[full_key] = {"type": mapped_type, "count": 1}
            else:
                field_info[full_key]["count"] += 1
                # If type differs, mark as mixed
                if field_info[full_key]["type"] != mapped_type and mapped_type != "null":
                    field_info[full_key]["type"] = "mixed"

            # Recurse into nested objects (but not too deep)
            if isinstance(value, dict) and prefix.count(".") < 2:
                self._extract_fields(value, field_info, full_key)

    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
