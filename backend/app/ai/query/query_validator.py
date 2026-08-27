"""
SQL / MongoDB Query Validator.

Multi-layer safety validation to ensure only read-only operations are executed.
Uses sqlparse for AST-level validation with regex as an additional safety net.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of query validation."""
    is_safe: bool
    query_type: str  # SQL_QUERY, MONGO_QUERY
    message: str = ""
    sanitized_query: Optional[str] = None


# SQL keywords that indicate destructive/modifying operations
_FORBIDDEN_SQL_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "MERGE", "CALL", "EXEC",
    "EXECUTE", "REPLACE", "RENAME", "COMMENT", "LOCK",
    "UNLOCK", "LOAD", "COPY",
}

# Regex patterns for detecting dangerous SQL constructs
_DANGEROUS_PATTERNS = [
    # Direct destructive statements (case-insensitive)
    re.compile(r"\b(INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|FUNCTION|TRIGGER|SEQUENCE))\b", re.IGNORECASE),
    re.compile(r"\b(ALTER\s+(TABLE|DATABASE|SCHEMA|INDEX))\b", re.IGNORECASE),
    re.compile(r"\b(TRUNCATE\s+TABLE?)\b", re.IGNORECASE),
    re.compile(r"\b(CREATE\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|FUNCTION|TRIGGER|PROCEDURE|ROLE|USER))\b", re.IGNORECASE),
    re.compile(r"\b(GRANT|REVOKE)\s+", re.IGNORECASE),
    re.compile(r"\b(EXEC|EXECUTE)\s+", re.IGNORECASE),
    re.compile(r"\b(CALL)\s+", re.IGNORECASE),
    # pg_* system function calls that could be dangerous
    re.compile(r"\bpg_(terminate_backend|cancel_backend|reload_conf)\b", re.IGNORECASE),
    # INTO clause (e.g., SELECT INTO)
    re.compile(r"\bSELECT\b.*\bINTO\b\s+(?!TEMP\b|TEMPORARY\b)(\w+)", re.IGNORECASE | re.DOTALL),
]

# MongoDB write operations to reject
_FORBIDDEN_MONGO_OPERATIONS = {
    "insert", "insertone", "insertmany",
    "update", "updateone", "updatemany",
    "delete", "deleteone", "deletemany",
    "drop", "remove", "rename",
    "createindex", "dropindex",
    "createcollection", "dropcollection",
    "dropdatabase",
    "bulkwrite",
    "findoneandupdate", "findoneandreplace", "findoneanddelete",
    "replaceone",
}


def validate_sql_query(sql: str) -> ValidationResult:
    """
    Validate a SQL query for safety.

    Uses a multi-layer approach:
    1. sqlparse AST-level statement type checking
    2. Multiple-statement detection
    3. Regex pattern matching as a safety net

    Args:
        sql: The SQL query to validate.

    Returns:
        ValidationResult with safety assessment.
    """
    if not sql or not sql.strip():
        return ValidationResult(
            is_safe=False,
            query_type="SQL_QUERY",
            message="Empty query.",
        )

    stripped = sql.strip()

    # Layer 1: Check for multiple statements (semicolons)
    # Remove semicolons at the end of the query
    if stripped.endswith(";"):
        stripped = stripped[:-1].strip()

    # Parse and check for multiple statements
    parsed_statements = sqlparse.parse(stripped)
    non_empty = [s for s in parsed_statements if s.tokens and str(s).strip()]
    if len(non_empty) > 1:
        return ValidationResult(
            is_safe=False,
            query_type="SQL_QUERY",
            message="Multiple SQL statements are not allowed. Only single queries are permitted.",
        )

    if not non_empty:
        return ValidationResult(
            is_safe=False,
            query_type="SQL_QUERY",
            message="No valid SQL statement found.",
        )

    # Layer 2: AST-level statement type checking
    stmt = non_empty[0]
    stmt_type = stmt.get_type()

    # Allow SELECT, unknown (CTEs sometimes parse as unknown)
    allowed_types = {"SELECT", None, "UNKNOWN"}
    if stmt_type and stmt_type.upper() not in {t.upper() if t else t for t in allowed_types}:
        return ValidationResult(
            is_safe=False,
            query_type="SQL_QUERY",
            message=f"Only SELECT queries are allowed. Detected: {stmt_type}",
        )

    # Layer 3: Token-level keyword scanning
    for token in _flatten_tokens(stmt):
        if token.ttype is DML and token.value.upper() in _FORBIDDEN_SQL_KEYWORDS:
            return ValidationResult(
                is_safe=False,
                query_type="SQL_QUERY",
                message=f"Forbidden operation detected: {token.value.upper()}",
            )
        if token.ttype is Keyword and token.value.upper() in _FORBIDDEN_SQL_KEYWORDS:
            return ValidationResult(
                is_safe=False,
                query_type="SQL_QUERY",
                message=f"Forbidden keyword detected: {token.value.upper()}",
            )

    # Layer 4: Regex safety net (catches obfuscated attempts)
    # Strip SQL comments first for regex checking
    comment_stripped = _strip_sql_comments(stripped)
    for pattern in _DANGEROUS_PATTERNS:
        match = pattern.search(comment_stripped)
        if match:
            return ValidationResult(
                is_safe=False,
                query_type="SQL_QUERY",
                message=f"Potentially dangerous SQL pattern detected: {match.group(0)}",
            )

    # Also check the original (with comments) to detect injection in comments
    for pattern in _DANGEROUS_PATTERNS:
        match = pattern.search(stripped)
        if match:
            return ValidationResult(
                is_safe=False,
                query_type="SQL_QUERY",
                message=f"Dangerous SQL detected (possibly in comment): {match.group(0)}",
            )

    return ValidationResult(
        is_safe=True,
        query_type="SQL_QUERY",
        message="Query validated as safe read-only operation.",
        sanitized_query=stripped,
    )


def validate_mongo_query(query: dict) -> ValidationResult:
    """
    Validate a MongoDB query for safety.

    Only allows read-only operations: find, aggregate, count, distinct.

    Args:
        query: MongoDB query dict with 'operation', 'collection', etc.

    Returns:
        ValidationResult with safety assessment.
    """
    if not query:
        return ValidationResult(
            is_safe=False,
            query_type="MONGO_QUERY",
            message="Empty query.",
        )

    operation = str(query.get("operation", "")).lower().strip()

    if not operation:
        return ValidationResult(
            is_safe=False,
            query_type="MONGO_QUERY",
            message="No operation specified.",
        )

    # Check for forbidden operations
    if operation in _FORBIDDEN_MONGO_OPERATIONS:
        return ValidationResult(
            is_safe=False,
            query_type="MONGO_QUERY",
            message=f"Write operation '{operation}' is not allowed. Only read operations are permitted.",
        )

    # Whitelist allowed operations
    allowed_operations = {"find", "aggregate", "count", "countdocuments", "distinct", "estimateddocumentcount"}
    if operation not in allowed_operations:
        return ValidationResult(
            is_safe=False,
            query_type="MONGO_QUERY",
            message=f"Operation '{operation}' is not supported. Allowed: {', '.join(sorted(allowed_operations))}",
        )

    # For aggregate pipelines, check for write stages
    if operation == "aggregate":
        pipeline = query.get("pipeline", [])
        forbidden_stages = {"$out", "$merge"}
        for stage in pipeline:
            if isinstance(stage, dict):
                for key in stage:
                    if key.lower() in forbidden_stages:
                        return ValidationResult(
                            is_safe=False,
                            query_type="MONGO_QUERY",
                            message=f"Aggregate stage '{key}' is not allowed (writes data).",
                        )

    collection = query.get("collection", "")
    if not collection:
        return ValidationResult(
            is_safe=False,
            query_type="MONGO_QUERY",
            message="No collection specified.",
        )

    return ValidationResult(
        is_safe=True,
        query_type="MONGO_QUERY",
        message="Query validated as safe read-only operation.",
    )


def _flatten_tokens(stmt: Statement):
    """Recursively flatten all tokens in a parsed SQL statement."""
    for token in stmt.tokens:
        if token.is_group:
            yield from _flatten_tokens(token)
        else:
            yield token


def _strip_sql_comments(sql: str) -> str:
    """Remove SQL comments (both -- and /* */ styles)."""
    # Remove single-line comments
    result = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    # Remove multi-line comments
    result = re.sub(r"/\*.*?\*/", "", result, flags=re.DOTALL)
    return result
