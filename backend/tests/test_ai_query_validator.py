"""
Unit Tests for the AI Query Safety Validator.
"""

import json
import pytest
from app.ai.query.query_validator import validate_sql_query, validate_mongo_query


def test_validate_safe_sql():
    """Verify that normal read-only SELECT queries are allowed."""
    queries = [
        "SELECT * FROM customers;",
        "SELECT id, name, email FROM users WHERE is_active = true LIMIT 10",
        "SELECT c.name, SUM(o.total) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name",
        "WITH active_users AS (SELECT * FROM users WHERE status = 'active') SELECT count(*) FROM active_users;",
        "select name from products -- get products list",
        "/* get products */ select name from products;",
    ]
    for q in queries:
        res = validate_sql_query(q)
        assert res.is_safe is True
        assert res.query_type == "SQL_QUERY"


def test_validate_destructive_sql_blocked():
    """Verify that destructive operations are strictly blocked."""
    destructive = [
        "INSERT INTO customers (name) VALUES ('Hacker');",
        "UPDATE users SET is_active = false;",
        "DELETE FROM orders WHERE total < 10;",
        "DROP TABLE users;",
        "ALTER TABLE customers ADD COLUMN balance decimal;",
        "TRUNCATE TABLE transactions;",
        "CREATE TABLE backdoor (id int);",
        "GRANT ALL PRIVILEGES ON users TO public;",
        "REVOKE SELECT ON payments FROM analyst;",
    ]
    for q in destructive:
        res = validate_sql_query(q)
        assert res.is_safe is False
        assert any(term in res.message.lower() for term in ["only select queries", "forbidden", "dangerous", "pattern detected"])


def test_validate_multiple_statements_blocked():
    """Verify that semicolon injection of multiple statements is blocked."""
    injection = [
        "SELECT * FROM customers; DROP TABLE orders;",
        "SELECT name FROM products; UPDATE users SET role = 'admin';",
    ]
    for q in injection:
        res = validate_sql_query(q)
        assert res.is_safe is False
        assert "multiple sql statements" in res.message.lower()


def test_validate_sql_obfuscation_blocked():
    """Verify that obfuscated dangerous attempts are caught."""
    attempts = [
        "SELECT * FROM customers --; DROP TABLE orders",
        "SELECT * FROM customers /* update users set role = 'admin' */",
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity;",
        "SELECT * INTO new_table FROM old_table;",
    ]
    for q in attempts:
        res = validate_sql_query(q)
        assert res.is_safe is False
        assert any(term in res.message.lower() for term in ["dangerous", "forbidden", "select queries", "only select"])


def test_validate_mongo_safe_queries():
    """Verify that read-only MongoDB queries are allowed."""
    queries = [
        {"operation": "find", "collection": "customers", "filter": {"status": "active"}},
        {"operation": "aggregate", "collection": "orders", "pipeline": [{"$match": {"total": {"$gt": 100}}}, {"$group": {"_id": "$customer", "sum": {"$sum": "$total"}}}]},
        {"operation": "count", "collection": "users", "filter": {}},
    ]
    for q in queries:
        res = validate_mongo_query(q)
        assert res.is_safe is True
        assert res.query_type == "MONGO_QUERY"


def test_validate_mongo_destructive_queries_blocked():
    """Verify that write MongoDB operations are blocked."""
    blocked = [
        {"operation": "insertOne", "collection": "users", "document": {"name": "hacker"}},
        {"operation": "updateMany", "collection": "users", "filter": {}, "update": {"$set": {"role": "admin"}}},
        {"operation": "delete", "collection": "orders", "filter": {}},
        {"operation": "drop", "collection": "users"},
        {"operation": "dropDatabase"},
    ]
    for q in blocked:
        res = validate_mongo_query(q)
        assert res.is_safe is False
        assert "write" in res.message.lower() or "forbidden" in res.message.lower() or "supported" in res.message.lower()


def test_validate_mongo_aggregate_write_stages_blocked():
    """Verify that aggregation write stages like $out or $merge are blocked."""
    stage_queries = [
        {"operation": "aggregate", "collection": "orders", "pipeline": [{"$match": {}}, {"$out": "backup_orders"}]},
        {"operation": "aggregate", "collection": "orders", "pipeline": [{"$match": {}}, {"$merge": {"into": "existing"}}]},
    ]
    for q in stage_queries:
        res = validate_mongo_query(q)
        assert res.is_safe is False
        assert "write" in res.message.lower() or "not allowed" in res.message.lower()
