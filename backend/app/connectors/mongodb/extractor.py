"""
MongoDB Metadata Extractor.

Extracts server info, databases, collections, indexes, and inferred field
schema from a live MongoDB connection.

All metadata is structural only — no business data values are persisted.
"""

from typing import Any, Dict, List, Optional

from app.connectors.mongodb.schema_inferencer import MongoDBSchemaInferencer, FieldMetadata
from app.connectors.mongodb.type_mapper import get_canonical_type

# System databases to exclude from normal discovery
SYSTEM_DATABASES = {"admin", "config", "local"}


class MongoDBMetadataExtractor:
    """Extracts metadata from a live MongoDB connection using PyMongo."""

    def __init__(self, client: Any):
        """
        Args:
            client: Active MongoClient instance.
        """
        self._client = client

    # ── Server Info ────────────────────────────────────────────────────────

    def get_server_info(self) -> Dict[str, Any]:
        """
        Retrieve safe server metadata.
        Returns version, topology, and replica set info. Never exposes credentials.
        """
        info: Dict[str, Any] = {
            "server_version": "unknown",
            "database": None,
            "user": None,
            "timezone": None,
            "topology": "unknown",
            "replica_set": None,
            "max_wire_version": None,
        }

        try:
            server_info = self._client.server_info()
            info["server_version"] = f"MongoDB {server_info.get('version', 'unknown')}"
        except Exception:
            pass

        try:
            # Get topology from server description
            topology = self._client.topology_description
            info["topology"] = str(topology.topology_type).replace("TopologyType.", "")
        except Exception:
            pass

        try:
            # Get replica set info from command
            rs_info = self._client.admin.command("isMaster")
            info["replica_set"] = rs_info.get("setName")
            info["max_wire_version"] = rs_info.get("maxWireVersion")
            if rs_info.get("setName"):
                info["topology"] = "ReplicaSet"
            elif rs_info.get("msg") == "isdbgrid":
                info["topology"] = "Sharded"
        except Exception:
            pass

        return info

    # ── Databases ──────────────────────────────────────────────────────────

    def list_databases(self, include_system: bool = False) -> List[Dict[str, Any]]:
        """
        List accessible databases with metadata.
        Excludes system databases (admin, config, local) unless include_system=True.
        """
        try:
            raw = self._client.list_databases()
        except Exception:
            # Fallback: try list_database_names
            try:
                names = self._client.list_database_names()
                raw = [{"name": n, "sizeOnDisk": 0, "empty": False} for n in names]
            except Exception:
                return []

        result = []
        for db in raw:
            name = db.get("name", "")
            if not include_system and name in SYSTEM_DATABASES:
                continue
            result.append({
                "name": name,
                "size_on_disk": db.get("sizeOnDisk", 0),
                "empty": db.get("empty", False),
            })

        return sorted(result, key=lambda d: d["name"])

    def list_database_names(self, include_system: bool = False) -> List[str]:
        """Return just the list of accessible database names."""
        return [d["name"] for d in self.list_databases(include_system=include_system)]

    # ── Collections ────────────────────────────────────────────────────────

    def list_collections(self, db_name: str) -> List[Dict[str, Any]]:
        """
        List all collections and views in a database.
        Captures collection type, options, capped, timeseries metadata.
        """
        try:
            db = self._client[db_name]
            raw = list(db.list_collections())
        except Exception:
            return []

        result = []
        for col in raw:
            name = col.get("name", "")
            coll_type = col.get("type", "collection")  # "collection" or "view"
            options = col.get("options", {})

            capped = bool(options.get("capped", False))
            ts_opts = options.get("timeseries")
            is_timeseries = ts_opts is not None

            # Estimated document count
            doc_count = 0
            try:
                doc_count = db[name].estimated_document_count()
            except Exception:
                pass

            entry: Dict[str, Any] = {
                "name": name,
                "type": "VIEW" if coll_type == "view" else "COLLECTION",
                "estimated_document_count": doc_count,
                "description": "",
                "capped": capped,
                "is_timeseries": is_timeseries,
                "provider_metadata": {
                    "collection_type": coll_type,
                    "capped": capped,
                    "timeseries": bool(is_timeseries),
                    "max_size": options.get("size"),
                    "max_documents": options.get("max"),
                },
            }

            # Timeseries specifics
            if is_timeseries and ts_opts:
                entry["provider_metadata"]["time_field"] = ts_opts.get("timeField")
                entry["provider_metadata"]["meta_field"] = ts_opts.get("metaField")
                entry["provider_metadata"]["granularity"] = ts_opts.get("granularity")

            result.append(entry)

        return sorted(result, key=lambda c: c["name"])

    # ── Indexes ────────────────────────────────────────────────────────────

    def get_indexes(self, db_name: str, collection_name: str) -> List[Dict[str, Any]]:
        """
        Extract indexes from a collection.
        Supports compound, unique, sparse, TTL, partial, hidden indexes.
        """
        try:
            db = self._client[db_name]
            raw = list(db[collection_name].list_indexes())
        except Exception:
            return []

        result = []
        for idx in raw:
            key_doc = idx.get("key", {})
            columns = list(key_doc.keys())

            result.append({
                "name": idx.get("name", ""),
                "columns": columns,
                "key_pattern": dict(key_doc),
                "unique": bool(idx.get("unique", False)),
                "sparse": bool(idx.get("sparse", False)),
                "primary": idx.get("name") == "_id_",
                "type": "compound" if len(columns) > 1 else "single",
                "expire_after_seconds": idx.get("expireAfterSeconds"),
                "partial_filter": idx.get("partialFilterExpression"),
                "hidden": bool(idx.get("hidden", False)),
            })

        return result

    # ── Schema Inference ───────────────────────────────────────────────────

    def infer_schema(
        self,
        db_name: str,
        collection_name: str,
        sample_size: int = 500,
        max_depth: int = 5,
    ) -> List[FieldMetadata]:
        """
        Run schema inference on a collection by sampling documents.
        Returns FieldMetadata objects (structural only, no values stored).
        """
        try:
            db = self._client[db_name]
            collection = db[collection_name]
            inferencer = MongoDBSchemaInferencer()
            return inferencer.infer(collection, sample_size=sample_size, max_depth=max_depth)
        except Exception:
            return []

    def field_metadata_to_columns(
        self,
        fields: List[FieldMetadata],
        collection_name: str,
        db_name: str,
    ) -> List[Dict[str, Any]]:
        """
        Convert FieldMetadata list to the standard `get_columns()` dict format
        expected by the generic connector contract and DataSourceService.
        """
        columns = []
        for idx, fmeta in enumerate(fields, start=1):
            columns.append({
                "name": fmeta.field_path,
                "table_name": collection_name,
                "schema_name": "default",
                "database_name": db_name,
                "data_type": fmeta.canonical_type.lower(),
                "native_type": fmeta.native_type,
                "nullable": fmeta.nullable,
                "ordinal_position": idx,
                "default_value": None,
                "description": "",
                "is_primary_key": fmeta.field_path == "_id" or fmeta.is_identifier,
                "is_foreign_key": False,
                # MongoDB-specific extras stored in a provider_metadata blob
                "provider_metadata": {
                    "field_path": fmeta.field_path,
                    "observed_types": list(fmeta.observed_types),
                    "is_array": fmeta.is_array,
                    "is_object": fmeta.is_object,
                    "is_identifier": fmeta.is_identifier,
                    "occurrence_rate": fmeta.occurrence_rate,
                    "confidence": fmeta.confidence,
                    "depth": fmeta.depth,
                },
            })
        return columns
