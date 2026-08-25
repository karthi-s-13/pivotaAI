"""
MongoDB Enterprise Connector.

Implements the BaseConnector interface for MongoDB.
Supports self-hosted MongoDB and MongoDB Atlas.

Architecture:
  MongoDBConnector
    ↓
  MongoDBConnectionConfig   (config parsing + validation + SSRF protection)
    ↓
  MongoDBConnectionDiagnostics  (8-step staged diagnostics)
    ↓
  MongoDBMetadataExtractor  (databases, collections, indexes, schema inference)
    ↓
  MongoDBSchemaInferencer   (field discovery via bounded $sample)
    ↓
  MongoDBRelationshipInferencer (inferred cross-collection references)
    ↓
  PyMongo → MongoDB / Atlas
"""

from typing import Any, Dict, List, Optional

from app.connectors.base import BaseConnector, ConnectionTestResult
from app.connectors.mongodb.config import MongoDBConnectionConfig
from app.connectors.mongodb.diagnostics import MongoDBConnectionDiagnostics
from app.connectors.mongodb.extractor import MongoDBMetadataExtractor, SYSTEM_DATABASES


class MongoDBConnector(BaseConnector):
    """
    Enterprise-grade MongoDB connector implementing the BaseConnector interface.

    Supports:
      - Self-hosted MongoDB and MongoDB Atlas
      - mongodb:// and mongodb+srv:// URIs
      - Username/password authentication with configurable authSource
      - TLS encryption with certificate validation
      - Schema inference from sampled documents (no business data persisted)
      - Collection, index, and inferred relationship discovery
    """

    provider = "mongodb"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mongo_config = MongoDBConnectionConfig.from_dict(config)
        self._client = None

    # ── Config Validation ──────────────────────────────────────────────────

    def validate_config(self) -> None:
        """Validate connection configuration. Raises ValueError if invalid."""
        self.mongo_config.validate()

    # ── Connection Test ────────────────────────────────────────────────────

    def test_connection(self) -> ConnectionTestResult:
        """
        Run the 8-step staged MongoDB connection diagnostics.
        Client is created and closed internally — never cached here.
        """
        diagnostics = MongoDBConnectionDiagnostics(self.mongo_config)
        return diagnostics.run()

    # ── Server Info ────────────────────────────────────────────────────────

    def get_server_info(self) -> Dict[str, Any]:
        """Retrieve MongoDB server metadata (version, topology, replica set)."""
        client = self._get_client()
        try:
            extractor = MongoDBMetadataExtractor(client)
            info = extractor.get_server_info()
            info["database"] = self.mongo_config.database or ""
            info["user"] = self.mongo_config.username or ""
            return info
        finally:
            self._close_client(client)

    # ── Database Discovery ─────────────────────────────────────────────────

    def list_databases(self) -> List[str]:
        """List all accessible non-system databases."""
        client = self._get_client()
        try:
            extractor = MongoDBMetadataExtractor(client)
            return extractor.list_database_names(include_system=False)
        finally:
            self._close_client(client)

    # ── Schema Compatibility Layer ─────────────────────────────────────────

    def list_schemas(self, database: Optional[str] = None) -> List[str]:
        """
        MongoDB has no schema layer.
        Returns ["default"] for compatibility with the generic sync loop.
        """
        return ["default"]

    # ── Object (Collection) Discovery ─────────────────────────────────────

    def list_objects(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all collections (and views) in the target database.

        Returns dicts compatible with the generic ObjectMetadata model:
          name, type ("COLLECTION" or "VIEW"), estimated_row_count, description
        """
        db_name = database or self.mongo_config.database or ""
        if not db_name:
            return []

        client = self._get_client()
        try:
            extractor = MongoDBMetadataExtractor(client)
            collections = extractor.list_collections(db_name)
            return [
                {
                    "name": c["name"],
                    "type": c["type"],  # "COLLECTION" or "VIEW"
                    "description": c.get("description", ""),
                    "estimated_row_count": c.get("estimated_document_count", 0),
                    "provider_metadata": c.get("provider_metadata", {}),
                }
                for c in collections
            ]
        finally:
            self._close_client(client)

    # ── Field (Column) Discovery ───────────────────────────────────────────

    def get_columns(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        object_name: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Infer fields from a collection via bounded document sampling.

        Maps FieldMetadata to the standard `get_columns()` column dict format.
        No business values are stored — only structural field metadata.
        """
        db_name = database or self.mongo_config.database or ""
        if not db_name or not object_name:
            return []

        client = self._get_client()
        try:
            extractor = MongoDBMetadataExtractor(client)
            sample_size = self.mongo_config.sample_size
            fields = extractor.infer_schema(db_name, object_name, sample_size=sample_size)
            return extractor.field_metadata_to_columns(fields, object_name, db_name)
        finally:
            self._close_client(client)

    # ── Relationships ──────────────────────────────────────────────────────

    def get_relationships(
        self, database: Optional[str] = None, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        MongoDB has no enforced FK constraints.
        Returns empty list — inferred relationships are handled in the sync service.
        """
        return []

    def get_inferred_relationships(
        self, database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Run inferred relationship analysis across all collections in a database.
        Results are marked as INFERRED_REFERENCE — never authoritative constraints.
        """
        from app.connectors.mongodb.relationship_inferencer import MongoDBRelationshipInferencer

        db_name = database or self.mongo_config.database or ""
        if not db_name:
            return []

        client = self._get_client()
        try:
            extractor = MongoDBMetadataExtractor(client)
            collections = extractor.list_collections(db_name)

            # Build field map for each collection
            collections_fields_map = {}
            for coll in collections:
                coll_name = coll["name"]
                if coll["type"] == "VIEW":
                    continue
                fields = extractor.infer_schema(
                    db_name, coll_name, sample_size=min(self.mongo_config.sample_size, 200)
                )
                if fields:
                    collections_fields_map[coll_name] = fields

            # Run relationship inference
            inferencer = MongoDBRelationshipInferencer()
            relationships = inferencer.infer(collections_fields_map)

            return [
                {
                    "source_collection": r.source_collection,
                    "source_field": r.source_field,
                    "target_collection": r.target_collection,
                    "target_field": r.target_field,
                    "relationship_type": r.relationship_type,
                    "confidence": r.confidence,
                    "evidence": r.evidence,
                    # Map to generic relationship contract fields
                    "from_table": r.source_collection,
                    "from_column": r.source_field,
                    "to_table": r.target_collection,
                    "to_column": r.target_field,
                    "type": "inferred",
                    "constraint_name": f"INFERRED:{r.source_collection}.{r.source_field}->{r.target_collection}.{r.target_field}",
                }
                for r in relationships
            ]
        finally:
            self._close_client(client)

    # ── Capabilities ───────────────────────────────────────────────────────

    def get_capabilities(self) -> Dict[str, Any]:
        """Return MongoDB capability profile from the registry."""
        from app.adapters.registry import get_provider_capabilities
        return get_provider_capabilities("mongodb")

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close any cached client connection."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            finally:
                self._client = None

    # ── Internal Helpers ───────────────────────────────────────────────────

    def _get_client(self) -> Any:
        """Create a new MongoClient for use in a single operation scope."""
        import pymongo
        kwargs = self.mongo_config.to_pymongo_kwargs()
        return pymongo.MongoClient(**kwargs)

    def _close_client(self, client: Any) -> None:
        """Safely close a client created for a single operation."""
        if client:
            try:
                client.close()
            except Exception:
                pass

    def _get_connection(self) -> Any:
        """
        Return a cached client for use in extractor contexts.
        Caller is responsible for calling close() when done.
        """
        if self._client is None:
            import pymongo
            kwargs = self.mongo_config.to_pymongo_kwargs()
            self._client = pymongo.MongoClient(**kwargs)
        return self._client
