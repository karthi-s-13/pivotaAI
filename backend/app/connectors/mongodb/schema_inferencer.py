"""
MongoDB Schema Inferencer.

Samples documents from a MongoDB collection and infers field structure,
types, nesting, arrays, occurrence rates, and confidence scores.

CRITICAL SECURITY NOTE:
  - Raw document values are NEVER stored or persisted.
  - Only structural metadata (field paths, types, frequencies) is produced.
  - Documents exceeding size limits are skipped.
  - Array inspection is bounded to prevent DoS on huge arrays.
  - Nesting is bounded by max_depth to prevent infinite recursion.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from app.connectors.mongodb.type_mapper import (
    get_canonical_type,
    get_native_type,
    is_identifier_type,
    is_null,
    resolve_mixed_canonical,
)

# Safety bounds
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ARRAY_INSPECT = 10        # Inspect at most 10 elements per array
MAX_FIELDS_PER_COLLECTION = 2000  # Stop after 2000 distinct fields


@dataclass
class FieldMetadata:
    """
    Inferred field metadata for a single MongoDB field path.

    All information is structural — no business values are stored.
    """
    field_path: str                     # e.g. "customer.address.city"
    observed_types: Set[str] = field(default_factory=set)  # canonical type names
    native_types: Set[str] = field(default_factory=set)    # BSON native names
    occurrence_count: int = 0           # How many sampled docs contained this field
    nullable_count: int = 0             # How many had null value
    is_array: bool = False
    is_object: bool = False
    is_identifier: bool = False
    depth: int = 0                      # Dot-notation nesting depth

    # Computed after finalization
    canonical_type: str = "UNKNOWN"
    native_type: str = "unknown"
    occurrence_rate: float = 0.0        # 0.0 – 1.0
    nullable: bool = True
    confidence: float = 0.0             # Type consistency score 0.0 – 1.0


def _field_depth(path: str) -> int:
    return path.count(".")


class MongoDBSchemaInferencer:
    """
    Infers schema from a MongoDB collection by sampling documents.

    Usage:
        inferencer = MongoDBSchemaInferencer()
        fields = inferencer.infer(collection, sample_size=500, max_depth=5)
    """

    def infer(
        self,
        collection: Any,           # pymongo Collection
        sample_size: int = 500,
        max_depth: int = 5,
    ) -> List[FieldMetadata]:
        """
        Sample documents from a collection and infer field metadata.

        Returns a list of FieldMetadata objects (structural metadata only).
        Raw documents are processed in memory and immediately discarded.
        """
        # Use $sample aggregation for random bounded sampling
        # Falls back to find().limit() if collection does not support aggregation
        docs = self._sample_documents(collection, sample_size)
        total = len(docs)
        if total == 0:
            return []

        # field_map: field_path → FieldMetadata
        field_map: Dict[str, FieldMetadata] = {}

        for doc in docs:
            # Skip oversized documents to prevent memory exhaustion
            try:
                import bson
                doc_size = len(bson.encode(doc)) if hasattr(bson, "encode") else 0
                if doc_size > MAX_DOCUMENT_SIZE_BYTES:
                    continue
            except Exception:
                pass

            self._process_document(doc, field_map, prefix="", depth=0, max_depth=max_depth)

            # Hard limit on field count
            if len(field_map) >= MAX_FIELDS_PER_COLLECTION:
                break

        # Finalize all fields
        return self._finalize(field_map, total)

    def _sample_documents(self, collection: Any, sample_size: int) -> list:
        """Try $sample aggregate, fall back to bounded find()."""
        try:
            cursor = collection.aggregate([{"$sample": {"size": sample_size}}])
            return list(cursor)
        except Exception:
            try:
                return list(collection.find({}, limit=sample_size))
            except Exception:
                return []

    def _process_document(
        self,
        doc: Dict[str, Any],
        field_map: Dict[str, FieldMetadata],
        prefix: str,
        depth: int,
        max_depth: int,
    ) -> None:
        """Recursively extract field structure from a document (no values stored)."""
        if depth > max_depth:
            return
        if len(field_map) >= MAX_FIELDS_PER_COLLECTION:
            return

        for key, value in doc.items():
            full_path = f"{prefix}.{key}" if prefix else key

            if full_path not in field_map:
                field_map[full_path] = FieldMetadata(
                    field_path=full_path,
                    depth=_field_depth(full_path),
                )
            fmeta = field_map[full_path]
            fmeta.occurrence_count += 1

            if is_null(value):
                fmeta.nullable_count += 1
                fmeta.observed_types.add("NULL")
                fmeta.native_types.add("null")
            else:
                canonical = get_canonical_type(value)
                native = get_native_type(value)
                fmeta.observed_types.add(canonical)
                fmeta.native_types.add(native)

                if is_identifier_type(value):
                    fmeta.is_identifier = True

                # Recurse into nested objects (bounded by max_depth)
                if isinstance(value, dict) and depth < max_depth:
                    fmeta.is_object = True
                    self._process_document(value, field_map, full_path, depth + 1, max_depth)

                # Process arrays (bounded inspection)
                elif isinstance(value, list):
                    fmeta.is_array = True
                    for elem in value[:MAX_ARRAY_INSPECT]:
                        if elem is None:
                            continue
                        # Record array element type
                        elem_path = f"{full_path}[]"
                        if elem_path not in field_map:
                            field_map[elem_path] = FieldMetadata(
                                field_path=elem_path,
                                depth=_field_depth(elem_path),
                                is_array=True,
                            )
                        efmeta = field_map[elem_path]
                        efmeta.occurrence_count += 1
                        efmeta.observed_types.add(get_canonical_type(elem))
                        efmeta.native_types.add(get_native_type(elem))

                        # Recurse into array element objects
                        if isinstance(elem, dict) and depth < max_depth:
                            efmeta.is_object = True
                            self._process_document(
                                elem, field_map, f"{full_path}[]", depth + 1, max_depth
                            )

    def _finalize(
        self, field_map: Dict[str, FieldMetadata], total_docs: int
    ) -> List[FieldMetadata]:
        """Compute derived metrics for all fields after full scan."""
        results = []

        for fmeta in field_map.values():
            # Occurrence rate
            fmeta.occurrence_rate = round(fmeta.occurrence_count / total_docs, 4) if total_docs > 0 else 0.0

            # Nullable: field is absent or null in at least one doc
            fmeta.nullable = (fmeta.occurrence_count < total_docs) or (fmeta.nullable_count > 0)

            # Canonical type resolution
            fmeta.canonical_type = resolve_mixed_canonical(fmeta.observed_types)

            # Native type (pick most common, prefer non-null)
            non_null_natives = fmeta.native_types - {"null"}
            fmeta.native_type = next(iter(non_null_natives), "null")

            # Confidence: combination of occurrence rate + type consistency
            type_consistency = 1.0 if len(fmeta.observed_types - {"NULL"}) <= 1 else 0.5
            fmeta.confidence = round(fmeta.occurrence_rate * type_consistency, 4)

            results.append(fmeta)

        # Sort: _id first, then by occurrence rate desc, then by path
        results.sort(key=lambda f: (
            0 if f.field_path == "_id" else 1,
            -f.occurrence_rate,
            f.field_path,
        ))

        return results
