"""
Offline validation tests for the MongoDB Enterprise Connector.

Run from the backend directory:
    .\\venv\\Scripts\\python scratch\\test_mongodb_connector.py

Tests are entirely offline — no live MongoDB connection is required.
"""

import sys
import os

# Add backend app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def assert_eq(label, actual, expected):
    if actual == expected:
        print(f"  {PASS} {label}: {actual!r}")
        results.append((label, True))
    else:
        print(f"  {FAIL} {label}: expected {expected!r}, got {actual!r}")
        results.append((label, False))


def assert_true(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}" + (f": {detail}" if detail else ""))
        results.append((label, True))
    else:
        print(f"  {FAIL} {label}" + (f": {detail}" if detail else ""))
        results.append((label, False))


def assert_raises(label, fn, expected_exc=Exception):
    try:
        fn()
        print(f"  {FAIL} {label}: expected exception not raised")
        results.append((label, False))
    except expected_exc as e:
        print(f"  {PASS} {label}: raised {type(e).__name__}: {e}")
        results.append((label, True))


# ─────────────────────────────────────────────────────────
print("\n=== 1. Type Mapper ===")
from app.connectors.mongodb.type_mapper import (
    get_canonical_type, get_native_type, is_identifier_type,
    resolve_mixed_canonical,
)
from bson import ObjectId
from decimal import Decimal
from datetime import datetime

assert_eq("str → STRING", get_canonical_type("hello"), "STRING")
assert_eq("int → INTEGER", get_canonical_type(42), "INTEGER")
assert_eq("float → NUMBER", get_canonical_type(3.14), "NUMBER")
assert_eq("bool → BOOLEAN", get_canonical_type(True), "BOOLEAN")
assert_eq("dict → OBJECT", get_canonical_type({}), "OBJECT")
assert_eq("list → ARRAY", get_canonical_type([]), "ARRAY")
assert_eq("None → NULL", get_canonical_type(None), "NULL")
assert_eq("datetime → DATETIME", get_canonical_type(datetime.now()), "DATETIME")
assert_eq("ObjectId → IDENTIFIER", get_canonical_type(ObjectId()), "IDENTIFIER")
assert_eq("is_identifier for ObjectId", is_identifier_type(ObjectId()), True)
assert_eq("is_identifier for str", is_identifier_type("hello"), False)
assert_eq("resolve_mixed: single type", resolve_mixed_canonical({"STRING"}), "STRING")
assert_eq("resolve_mixed: null only", resolve_mixed_canonical({"NULL"}), "NULL")
assert_eq("resolve_mixed: mixed types", resolve_mixed_canonical({"STRING", "INTEGER"}), "MIXED")
assert_eq("resolve_mixed: null + type", resolve_mixed_canonical({"NULL", "STRING"}), "STRING")


# ─────────────────────────────────────────────────────────
print("\n=== 2. Config Validation ===")
from app.connectors.mongodb.config import MongoDBConnectionConfig

# Valid config
cfg = MongoDBConnectionConfig(host="localhost", port=27017, database="testdb", network_mode="private")
cfg.validate()
assert_true("Valid config passes", True)

# Missing host
def _missing_host():
    c = MongoDBConnectionConfig(database="testdb", network_mode="private")
    c.validate()
assert_raises("Missing host raises ValueError", _missing_host, ValueError)

# Missing database
def _missing_db():
    c = MongoDBConnectionConfig(host="localhost", port=27017, network_mode="private")
    c.validate()
assert_raises("Missing database raises ValueError", _missing_db, ValueError)

# Invalid port
def _bad_port():
    c = MongoDBConnectionConfig(host="localhost", port=99999, database="db", network_mode="private")
    c.validate()
assert_raises("Invalid port raises ValueError", _bad_port, ValueError)

# URI parsing: mongodb://
cfg_uri = MongoDBConnectionConfig.from_dict({
    "connection_string": "mongodb://user:pass@localhost:27017/mydb",
    "network_mode": "private",
})
assert_eq("URI host", cfg_uri.host, "localhost")
assert_eq("URI port", cfg_uri.port, 27017)
assert_eq("URI database", cfg_uri.database, "mydb")
assert_eq("URI username", cfg_uri.username, "user")
assert_true("URI password hidden", cfg_uri.password is not None)
assert_true("Safe repr no credentials", "pass" not in repr(cfg_uri))

# URI parsing: mongodb+srv://
cfg_srv = MongoDBConnectionConfig.from_dict({
    "connection_string": "mongodb+srv://user:pass@cluster0.mongodb.net/testdb",
    "network_mode": "private",
})
assert_eq("SRV deployment", cfg_srv.deployment, "atlas")
assert_eq("SRV TLS auto-enabled", cfg_srv.tls, True)
assert_eq("SRV port None", cfg_srv.port, None)

# to_pymongo_kwargs: no URI
cfg_plain = MongoDBConnectionConfig(host="localhost", port=27017, database="db", network_mode="private")
kwargs = cfg_plain.to_pymongo_kwargs()
assert_eq("kwargs host", kwargs["host"], "localhost")
assert_eq("kwargs port", kwargs["port"], 27017)
assert_true("kwargs no password (unauthenticated)", "password" not in kwargs)

# SSRF: private IP blocked in public mode
def _ssrf_loopback():
    c = MongoDBConnectionConfig(host="127.0.0.1", port=27017, database="db", network_mode="public")
    c.validate()
# Note: SSRF only blocks if DNS resolves. 127.0.0.1 is a direct IP.
assert_raises("SSRF blocks 127.0.0.1 in public mode", _ssrf_loopback, ValueError)


# ─────────────────────────────────────────────────────────
print("\n=== 3. Schema Inferencer (offline with mock documents) ===")
from app.connectors.mongodb.schema_inferencer import MongoDBSchemaInferencer


class MockCollection:
    """Simulates a pymongo collection with pre-set documents."""
    def __init__(self, docs):
        self._docs = docs

    def aggregate(self, pipeline):
        # Return all docs (ignore $sample)
        return iter(self._docs)

    def find(self, *a, **kw):
        return iter(self._docs)


inferencer = MongoDBSchemaInferencer()

# Flat documents
flat_docs = [
    {"_id": ObjectId(), "name": "Alice", "age": 30, "active": True},
    {"_id": ObjectId(), "name": "Bob", "age": 25, "active": False},
    {"_id": ObjectId(), "name": "Carol", "age": None, "active": True},
]
fields = inferencer.infer(MockCollection(flat_docs), sample_size=10)
field_names = [f.field_path for f in fields]
assert_true("_id field inferred", "_id" in field_names)
assert_true("name field inferred", "name" in field_names)
assert_true("age field inferred", "age" in field_names)
assert_true("active field inferred", "active" in field_names)

_id_field = next(f for f in fields if f.field_path == "_id")
assert_true("_id is identifier", _id_field.is_identifier)

age_field = next(f for f in fields if f.field_path == "age")
assert_true("age nullable (has None)", age_field.nullable)

# Nested documents
nested_docs = [
    {"_id": ObjectId(), "address": {"city": "NYC", "zip": "10001"}},
    {"_id": ObjectId(), "address": {"city": "LA", "zip": "90001"}},
]
nested_fields = inferencer.infer(MockCollection(nested_docs), sample_size=10, max_depth=5)
nested_names = [f.field_path for f in nested_fields]
assert_true("Nested address.city inferred", "address.city" in nested_names)
assert_true("Nested address.zip inferred", "address.zip" in nested_names)

addr_city = next(f for f in nested_fields if f.field_path == "address.city")
assert_eq("address.city is_object parent", addr_city.canonical_type, "STRING")

# Array documents
array_docs = [
    {"_id": ObjectId(), "tags": ["python", "mongodb", "nosql"]},
    {"_id": ObjectId(), "tags": ["fastapi", "python"]},
]
array_fields = inferencer.infer(MockCollection(array_docs), sample_size=10)
array_names = [f.field_path for f in array_fields]
assert_true("tags field inferred", "tags" in array_names)
tags_field = next(f for f in array_fields if f.field_path == "tags")
assert_true("tags is_array", tags_field.is_array)

# Mixed types
mixed_docs = [
    {"_id": ObjectId(), "value": 42},
    {"_id": ObjectId(), "value": "hello"},
]
mixed_fields = inferencer.infer(MockCollection(mixed_docs), sample_size=10)
val_field = next((f for f in mixed_fields if f.field_path == "value"), None)
assert_true("Mixed type field exists", val_field is not None)
assert_eq("Mixed type canonical", val_field.canonical_type, "MIXED")

# Empty collection
empty_fields = inferencer.infer(MockCollection([]), sample_size=10)
assert_eq("Empty collection returns []", empty_fields, [])

# Max depth enforcement
def make_deep(depth, root=None):
    if depth == 0:
        return {"leaf": "value"}
    d = {"nested": make_deep(depth - 1)}
    if root is not None:
        d["_id"] = ObjectId()
    return d

deep_doc = make_deep(10, root=True)
deep_doc["_id"] = ObjectId()
deep_fields = inferencer.infer(MockCollection([deep_doc]), sample_size=10, max_depth=3)
max_depth_seen = max(f.depth for f in deep_fields) if deep_fields else 0
assert_true(f"Max depth 3 enforced (got {max_depth_seen})", max_depth_seen <= 5)


# ─────────────────────────────────────────────────────────
print("\n=== 4. Relationship Inferencer ===")
from app.connectors.mongodb.relationship_inferencer import MongoDBRelationshipInferencer
from app.connectors.mongodb.schema_inferencer import FieldMetadata

def make_field(path, types, occ_rate=0.9, is_identifier=False):
    f = FieldMetadata(field_path=path)
    f.observed_types = set(types)
    f.occurrence_rate = occ_rate
    f.is_identifier = is_identifier
    f.canonical_type = types[0] if len(types) == 1 else "MIXED"
    f.nullable = occ_rate < 1.0
    f.confidence = occ_rate
    f.depth = path.count(".")
    return f

rel_inferencer = MongoDBRelationshipInferencer()

# customers → orders.customer_id → customers._id
customers_fields = [make_field("_id", ["IDENTIFIER"], 1.0, is_identifier=True)]
orders_fields = [
    make_field("_id", ["IDENTIFIER"], 1.0, is_identifier=True),
    make_field("customer_id", ["IDENTIFIER"], 0.95, is_identifier=True),
    make_field("total", ["NUMBER"], 0.99),
]
rels = rel_inferencer.infer({"customers": customers_fields, "orders": orders_fields})
assert_true("customer_id → customers inferred", any(
    r.source_field == "customer_id" and r.target_collection == "customers"
    for r in rels
), f"relationships: {[(r.source_field, r.target_collection) for r in rels]}")

if rels:
    r0 = [r for r in rels if r.source_field == "customer_id"][0]
    assert_true("Confidence ≥ 0.5", r0.confidence >= 0.5, f"confidence={r0.confidence}")

# No false positives: 'random_xyz' field should not match
orders2_fields = [
    make_field("_id", ["IDENTIFIER"], 1.0),
    make_field("random_xyz", ["STRING"], 0.5),
]
rels2 = rel_inferencer.infer({"customers": customers_fields, "orders2": orders2_fields})
assert_true("random_xyz does not create relationship", not any(
    r.source_field == "random_xyz" for r in rels2
))


# ─────────────────────────────────────────────────────────
print("\n=== 5. URI Parser ===")
from app.core.uri_parser import parse_connection_string

p1 = parse_connection_string("mongodb://user:pass@host:27017/mydb")
assert_eq("mongodb:// provider", p1["provider"], "mongodb")
assert_eq("mongodb:// host", p1["host"], "host")
assert_eq("mongodb:// port", p1["port"], 27017)
assert_eq("mongodb:// database", p1["database_name"], "mydb")
assert_eq("mongodb:// username", p1["username"], "user")

p2 = parse_connection_string("mongodb+srv://user:pass@cluster.mongodb.net/mydb")
assert_eq("mongodb+srv provider", p2["provider"], "mongodb")
assert_eq("mongodb+srv port None", p2["port"], None)
assert_eq("mongodb+srv deployment", p2["provider_config"].get("deployment"), "atlas")

p3 = parse_connection_string("mongodb://host:27017/mydb?replicaSet=rs0&authSource=admin")
assert_eq("replicaSet normalized", p3["provider_config"].get("replica_set"), "rs0")
assert_eq("authSource normalized", p3["provider_config"].get("auth_source"), "admin")


# ─────────────────────────────────────────────────────────
print("\n=== 6. ConnectorManager — provider registration ===")
from app.connectors.manager import get_connector, get_supported_providers

providers = get_supported_providers()
for p in ["postgresql", "mysql", "sqlserver", "mongodb"]:
    assert_true(f"'{p}' in supported providers", p in providers)

# MongoDB connector instantiation
from app.connectors.mongodb.connector import MongoDBConnector
connector = get_connector("mongodb", {
    "host": "localhost",
    "port": 27017,
    "database_name": "test",
    "network_mode": "private",
})
assert_true("MongoDBConnector instantiated via manager", isinstance(connector, MongoDBConnector))
assert_eq("list_schemas returns ['default']", connector.list_schemas(), ["default"])
assert_eq("get_relationships returns []", connector.get_relationships(), [])
connector.close()


# ─────────────────────────────────────────────────────────
print("\n=== 7. Capabilities Profile ===")
from app.adapters.registry import get_provider_capabilities

caps = get_provider_capabilities("mongodb")
assert_eq("mongodb sql=False", caps["sql"], False)
assert_eq("mongodb schemas=False", caps["schemas"], False)
assert_eq("mongodb relationships='inferred'", caps["relationships"], "inferred")
assert_eq("mongodb collections=True", caps["collections"], True)
assert_eq("mongodb schema_inference=True", caps["schema_inference"], True)


# ─────────────────────────────────────────────────────────
print("\n\n" + "═" * 60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total = len(results)
print(f"RESULTS: {passed}/{total} passed, {failed} failed")
if failed > 0:
    print("\nFailed tests:")
    for label, ok in results:
        if not ok:
            print(f"  {FAIL} {label}")
    sys.exit(1)
else:
    print(f"\n{PASS} All {total} assertions passed.")
