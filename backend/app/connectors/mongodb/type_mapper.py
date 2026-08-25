"""
MongoDB Type Mapper.

Maps Python/BSON runtime types to Pivota canonical type names.
Never touches business data values — only inspects types.
"""

from typing import Any


# BSON type class names → Pivota canonical types
_BSON_TYPE_MAP = {
    "str": "STRING",
    "int": "INTEGER",
    "float": "NUMBER",
    "bool": "BOOLEAN",
    "datetime": "DATETIME",
    "Timestamp": "DATETIME",
    "ObjectId": "IDENTIFIER",
    "Decimal128": "NUMBER",
    "Int64": "INTEGER",
    "bytes": "BINARY",
    "Binary": "BINARY",
    "dict": "OBJECT",
    "list": "ARRAY",
    "NoneType": "NULL",
    "Regex": "STRING",
    "Code": "STRING",
    "DBRef": "REFERENCE",
    "MinKey": "SPECIAL",
    "MaxKey": "SPECIAL",
    "uuid": "STRING",
    "UUID": "STRING",
}

# BSON native type name strings (for storing native_type)
_BSON_NATIVE_MAP = {
    "str": "string",
    "int": "int32",
    "float": "double",
    "bool": "bool",
    "datetime": "date",
    "Timestamp": "timestamp",
    "ObjectId": "objectId",
    "Decimal128": "decimal128",
    "Int64": "int64",
    "bytes": "binData",
    "Binary": "binData",
    "dict": "object",
    "list": "array",
    "NoneType": "null",
    "Regex": "regex",
    "Code": "javascript",
    "DBRef": "dbPointer",
    "MinKey": "minKey",
    "MaxKey": "maxKey",
}


def get_canonical_type(value: Any) -> str:
    """Return Pivota canonical type string for a Python value."""
    type_name = type(value).__name__
    return _BSON_TYPE_MAP.get(type_name, "UNKNOWN")


def get_native_type(value: Any) -> str:
    """Return native BSON type name string for a Python value."""
    type_name = type(value).__name__
    return _BSON_NATIVE_MAP.get(type_name, type_name.lower())


def is_identifier_type(value: Any) -> bool:
    """Return True if value is of an ObjectId-like identifier type."""
    type_name = type(value).__name__
    return type_name in ("ObjectId",)


def is_null(value: Any) -> bool:
    """Return True if value is None/null."""
    return value is None


def resolve_mixed_canonical(types: set) -> str:
    """Given a set of observed canonical types, return merged canonical type."""
    # Remove NULL from the set for merging (null is just 'nullable')
    non_null = types - {"NULL"}
    if not non_null:
        return "NULL"
    if len(non_null) == 1:
        return next(iter(non_null))
    return "MIXED"
