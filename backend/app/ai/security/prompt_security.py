"""
Prompt Security Service.

Sanitizes database content before sending to the LLM to prevent
prompt injection attacks from database records.
"""

import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Patterns that indicate potential prompt injection in database content
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+|the\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+|the\s+)?previous", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"override\s+instructions?", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+)?prompt", re.IGNORECASE),
    re.compile(r"output\s+(your\s+)?(system\s+)?instructions?", re.IGNORECASE),
]

# Sensitive column name patterns to mask
_SENSITIVE_COLUMN_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api_?key", re.IGNORECASE),
    re.compile(r"access_?key", re.IGNORECASE),
    re.compile(r"private_?key", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"ssn", re.IGNORECASE),
    re.compile(r"credit_?card", re.IGNORECASE),
    re.compile(r"cvv", re.IGNORECASE),
]


def sanitize_query_results(
    columns: List[str],
    rows: List[Dict[str, Any]],
    max_value_length: int = 500,
) -> List[Dict[str, Any]]:
    """
    Sanitize query results before sending to the LLM.

    - Masks sensitive columns
    - Truncates long values
    - Flags potential injection attempts in data

    Args:
        columns: Column names.
        rows: Query result rows.
        max_value_length: Maximum string value length.

    Returns:
        Sanitized rows.
    """
    sensitive_cols = _identify_sensitive_columns(columns)
    sanitized_rows = []

    for row in rows:
        sanitized_row = {}
        for col, value in row.items():
            if col in sensitive_cols:
                sanitized_row[col] = "***MASKED***"
            elif isinstance(value, str):
                # Truncate long values
                if len(value) > max_value_length:
                    value = value[:max_value_length] + "...[truncated]"
                sanitized_row[col] = value
            else:
                sanitized_row[col] = value
        sanitized_rows.append(sanitized_row)

    return sanitized_rows


def sanitize_for_llm_context(text: str) -> str:
    """
    Sanitize text content that comes from database records
    before including it in the LLM context.

    Wraps the content in clear delimiters that the system prompt
    references as untrusted data boundaries.
    """
    return f"[DATABASE_CONTENT_START]\n{text}\n[DATABASE_CONTENT_END]"


def check_for_injection(text: str) -> bool:
    """
    Check if a text string contains potential prompt injection patterns.

    Returns True if injection is suspected.
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            logger.warning(f"Potential prompt injection detected in data: {text[:100]}")
            return True
    return False


def _identify_sensitive_columns(columns: List[str]) -> set:
    """Identify columns that might contain sensitive data."""
    sensitive = set()
    for col in columns:
        for pattern in _SENSITIVE_COLUMN_PATTERNS:
            if pattern.search(col):
                sensitive.add(col)
                break
    return sensitive
