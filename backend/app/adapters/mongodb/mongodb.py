"""
MongoDB Database Adapter.

Implements the DatasourceAdapter interface for MongoDB databases using pymongo.
"""

import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pymongo import MongoClient
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

from app.adapters.base import ConnectionTestResult, DatasourceAdapter


class MongoDBAdapter(DatasourceAdapter):
    """Adapter for MongoDB databases."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = int(config.get("port", 27017)) if config.get("port") else None
        self.database_name = config.get("database_name", "")
        self.username = config.get("username")
        self.password = config.get("password")
        self.connection_string = config.get("connection_string")
        self.auth_source = config.get("auth_source", "admin")
        self.replica_set = config.get("replica_set")
        self.ssl_enabled = config.get("ssl_enabled", False)
        self._client = None

    def _get_client(self) -> MongoClient:
        """Create or return the existing MongoClient."""
        if self._client is None:
            if self.connection_string:
                self._client = MongoClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                )
            else:
                kwargs = {
                    "host": self.host,
                    "port": self.port or 27017,
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

    def validate_config(self) -> None:
        """Validate connection configuration."""
        if not self.connection_string:
            if not self.host:
                raise ValueError("Host or connection_string is required for MongoDB connection")
            if not self.database_name:
                raise ValueError("Database name is required for MongoDB connection")

    def connect(self) -> Any:
        """Establish connection and return the MongoClient object."""
        return self._get_client()

    def disconnect(self) -> None:
        """Close MongoClient connection."""
        if self._client:
            self._client.close()
            self._client = None

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
            # Resolve check targets from configuration or URI string
            host_to_check = self.host
            port_to_check = self.port

            if self.connection_string:
                try:
                    parsed_uri = urlparse(self.connection_string)
                    host_to_check = parsed_uri.hostname
                    port_to_check = parsed_uri.port
                except Exception:
                    pass

            if host_to_check:
                if port_to_check:
                    socket.create_connection((host_to_check, port_to_check), timeout=5).close()
                else:
                    socket.gethostbyname(host_to_check)

            step_net["status"] = "success"
            step_net["latency_ms"] = round((time.time() - start_step) * 1000, 2)
        except Exception as e:
            step_net["status"] = "failed"
            step_net["message"] = f"Network connectivity failed: {str(e)}"
            step_net["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            for remaining in ["authentication", "health"]:
                steps.append({"name": remaining, "status": "skipped"})
            return ConnectionTestResult(
                success=False,
                message=f"Network connectivity failed: {str(e)}",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                steps=steps,
            )

        # Step 3: Authentication / Ping
        step_auth = {"name": "authentication", "status": "pending", "message": None, "latency_ms": None}
        steps.append(step_auth)
        start_step = time.time()
        try:
            client = self._get_client()
            client.admin.command("ping")
            step_auth["status"] = "success"
            step_auth["latency_ms"] = round((time.time() - start_step) * 1000, 2)
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            step_auth["status"] = "failed"
            step_auth["message"] = f"Connection/timeout error: {str(e)}"
            step_auth["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            steps.append({"name": "health", "status": "skipped"})
            return ConnectionTestResult(
                success=False,
                message=f"Authentication failed: {str(e)}",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                steps=steps,
            )
        except (OperationFailure, ConfigurationError) as e:
            step_auth["status"] = "failed"
            step_auth["message"] = f"Authentication/Configuration error: {str(e)}"
            step_auth["latency_ms"] = round((time.time() - start_step) * 1000, 2)
            steps.append({"name": "health", "status": "skipped"})
            return ConnectionTestResult(
                success=False,
                message=f"Authentication failed: {str(e)}",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                steps=steps,
            )

        # Step 4: Health query / Server version details
        step_health = {"name": "health", "status": "pending", "message": None, "latency_ms": None}
        steps.append(step_health)
        start_step = time.time()
        try:
            server_info = client.server_info()
            version = server_info.get("version", "unknown")
            step_health["status"] = "success"
            step_health["latency_ms"] = round((time.time() - start_step) * 1000, 2)

            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                latency_ms=round((time.time() - start_total) * 1000, 2),
                server_version=f"MongoDB {version}",
                details={"host": self.host, "port": self.port, "database": self.database_name},
                steps=steps,
            )
        except Exception as e:
            step_health["status"] = "failed"
            step_health["message"] = f"Health query failed: {str(e)}"
            step_health["latency_ms"] = round((time.time() - start_step) * 1000, 2)
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
            client = self.connect()
            client.admin.command("ping")
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
        """List all accessible databases."""
        client = self.connect()
        system_dbs = {"admin", "local", "config"}
        all_dbs = client.list_database_names()
        return [db for db in all_dbs if db not in system_dbs]

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """MongoDB doesn't have schemas in the SQL sense. Returns default."""
        return ["default"]

    def list_objects(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """List collections in the database."""
        db_name = database or self.database_name
        client = self.connect()
        db = client[db_name]
        collections = []

        for name in db.list_collection_names():
            try:
                count = db[name].estimated_document_count()
            except Exception:
                count = 0

            collections.append(
                {
                    "name": name,
                    "type": "COLLECTION",
                    "description": "",
                    "estimated_row_count": count,
                }
            )

        return sorted(collections, key=lambda x: x["name"])

    def get_columns(
        self, database: Optional[str] = None, schema: Optional[str] = None, object_name: str = None
    ) -> List[dict]:
        """Infer document fields by sampling documents from a collection."""
        db_name = database or self.database_name
        client = self.connect()
        db = client[db_name]
        collection = db[object_name]

        sample_docs = list(collection.find().limit(100))
        if not sample_docs:
            return []

        field_info: Dict[str, Dict[str, Any]] = {}
        for doc in sample_docs:
            self._extract_fields(doc, field_info, prefix="")

        columns = []
        for idx, (field_name, info) in enumerate(sorted(field_info.items()), start=1):
            columns.append(
                {
                    "name": field_name,
                    "table_name": object_name,
                    "schema_name": schema or "default",
                    "database_name": db_name,
                    "data_type": info.get("type", "unknown"),
                    "nullable": True,
                    "ordinal_position": idx,
                    "default_value": None,
                    "description": "",
                    "is_primary_key": field_name == "_id",
                    "is_foreign_key": False,
                }
            )

        return columns

    def _extract_fields(self, doc: dict, field_info: Dict[str, Dict[str, Any]], prefix: str) -> None:
        """Recursively extract field names and types from a document."""
        for key, value in doc.items():
            full_key = f"{prefix}.{key}" if prefix else key
            python_type = type(value).__name__

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
                if field_info[full_key]["type"] != mapped_type and mapped_type != "null":
                    field_info[full_key]["type"] = "mixed"

            if isinstance(value, dict) and prefix.count(".") < 2:
                self._extract_fields(value, field_info, full_key)

    def get_relationships(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[dict]:
        """MongoDB does not have native schema relationships."""
        return []

    def get_capabilities(self) -> dict:
        """Get capabilities of MongoDB."""
        from app.adapters.registry import get_provider_capabilities

        return get_provider_capabilities("mongodb")

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
