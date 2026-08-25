"""
MongoDB Relationship Inferencer.

Infers likely cross-collection references from field naming patterns
and type compatibility. Relationships are always marked as INFERRED —
MongoDB does not enforce foreign key constraints.

SECURITY NOTE:
  - Only field names, types, and occurrence rates are inspected.
  - No business data values are read or persisted.
  - Confidence scores are based on structural heuristics only.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from app.connectors.mongodb.schema_inferencer import FieldMetadata

# Minimum confidence threshold to report a relationship
MIN_CONFIDENCE = 0.5

# Pattern to detect foreign-key-like field names
_ID_SUFFIX_PATTERN = re.compile(r"^(.+)_id$", re.IGNORECASE)
_ID_PREFIX_PATTERN = re.compile(r"^id_(.+)$", re.IGNORECASE)
_REF_PATTERN = re.compile(r"^(.+)_ref$", re.IGNORECASE)


@dataclass
class InferredRelationship:
    """A candidate relationship inferred from structural heuristics."""
    source_collection: str
    source_field: str
    target_collection: str
    target_field: str
    relationship_type: str = "INFERRED_REFERENCE"
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


class MongoDBRelationshipInferencer:
    """
    Infers cross-collection references from schema metadata.

    Usage:
        inferencer = MongoDBRelationshipInferencer()
        relationships = inferencer.infer(collections_fields_map)

    Args:
        collections_fields_map: Dict[collection_name, List[FieldMetadata]]
    """

    def infer(
        self,
        collections_fields_map: Dict[str, List[FieldMetadata]],
    ) -> List[InferredRelationship]:
        """
        Infer likely cross-collection references.

        Returns a list of InferredRelationship objects with confidence ≥ MIN_CONFIDENCE.
        No business data values are ever accessed.
        """
        relationships: List[InferredRelationship] = []
        collection_names: Set[str] = set(collections_fields_map.keys())

        # Normalize collection names for lookup
        collection_name_lower = {c.lower(): c for c in collection_names}

        for source_coll, fields in collections_fields_map.items():
            for fmeta in fields:
                # Skip the _id field itself — it's a target, not a reference
                if fmeta.field_path == "_id":
                    continue

                # Only inspect top-level and immediate-nested fields
                if fmeta.depth > 2:
                    continue

                candidate = self._evaluate_field(
                    source_coll=source_coll,
                    fmeta=fmeta,
                    collection_name_lower=collection_name_lower,
                    collection_names=collection_names,
                )
                if candidate and candidate.confidence >= MIN_CONFIDENCE:
                    relationships.append(candidate)

        # Sort by confidence descending
        relationships.sort(key=lambda r: -r.confidence)
        return relationships

    def _evaluate_field(
        self,
        source_coll: str,
        fmeta: FieldMetadata,
        collection_name_lower: Dict[str, str],
        collection_names: Set[str],
    ) -> Optional[InferredRelationship]:
        """Evaluate a single field as a potential reference to another collection."""
        field_name = fmeta.field_path.split(".")[-1]  # Use leaf field name
        confidence = 0.0
        evidence = []

        # --- Heuristic 1: field ends in _id (e.g. customer_id, user_id) ---
        id_match = _ID_SUFFIX_PATTERN.match(field_name)
        if not id_match:
            return None  # Only process _id-pattern fields

        target_hint = id_match.group(1).lower()
        confidence += 0.35
        evidence.append("identifier_naming_pattern")

        # --- Heuristic 2: Matching collection exists ---
        # Try exact match, plural/singular variations
        target_coll = self._resolve_target_collection(
            target_hint, collection_name_lower, source_coll
        )
        if target_coll is None:
            # No matching collection found → weak confidence only
            # Still report if _id pattern is strong
            return None  # No target collection → skip

        confidence += 0.35
        evidence.append("target_collection_exists")

        # --- Heuristic 3: Type compatibility with ObjectId ---
        non_null_types = fmeta.observed_types - {"NULL"}
        if "IDENTIFIER" in non_null_types:
            confidence += 0.2
            evidence.append("objectid_type_compatibility")
        elif "STRING" in non_null_types:
            # String-based foreign keys are common
            confidence += 0.05
            evidence.append("string_type_compatibility")

        # --- Heuristic 4: Field occurrence rate indicates it's a join field ---
        if fmeta.occurrence_rate > 0.7:
            confidence += 0.1
            evidence.append("high_occurrence_rate")

        return InferredRelationship(
            source_collection=source_coll,
            source_field=fmeta.field_path,
            target_collection=target_coll,
            target_field="_id",
            relationship_type="INFERRED_REFERENCE",
            confidence=round(min(confidence, 1.0), 4),
            evidence=evidence,
        )

    def _resolve_target_collection(
        self,
        target_hint: str,
        collection_name_lower: Dict[str, str],
        source_coll: str,
    ) -> Optional[str]:
        """Try to find a collection matching the target hint with plural/singular variations."""
        # Direct match
        if target_hint in collection_name_lower:
            coll = collection_name_lower[target_hint]
            if coll.lower() != source_coll.lower():
                return coll

        # Plural: add 's'
        plural = target_hint + "s"
        if plural in collection_name_lower:
            coll = collection_name_lower[plural]
            if coll.lower() != source_coll.lower():
                return coll

        # Plural: add 'es'
        plural_es = target_hint + "es"
        if plural_es in collection_name_lower:
            coll = collection_name_lower[plural_es]
            if coll.lower() != source_coll.lower():
                return coll

        # Singular: remove trailing 's'
        if target_hint.endswith("s"):
            singular = target_hint[:-1]
            if singular in collection_name_lower:
                coll = collection_name_lower[singular]
                if coll.lower() != source_coll.lower():
                    return coll

        return None
