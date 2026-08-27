"""
Query Executor.

Executes validated read-only queries through the existing Pivota connector
infrastructure. Applies row limits and timeouts.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.services.data_source_service import _build_adapter_config
from app.connectors.manager import get_connector
from app.ai.config import ai_settings

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a query execution."""
    success: bool
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: int = 0
    truncated: bool = False  # True if rows were limited
    error: Optional[str] = None
    query_type: str = "SQL_QUERY"


def execute_read_query(
    db: Session,
    data_source_id: str,
    organization_id: str,
    query: str,
    provider: str,
    max_rows: Optional[int] = None,
) -> QueryResult:
    """
    Execute a validated read-only SQL query through the existing connector layer.

    Args:
        db: Database session.
        data_source_id: Target data source ID.
        organization_id: User's organization ID.
        query: The validated SQL query.
        provider: Database provider type.
        max_rows: Maximum rows to return (default from config).

    Returns:
        QueryResult with columns, rows, and execution metadata.
    """
    if max_rows is None:
        max_rows = ai_settings.AI_MAX_ROWS

    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == data_source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        return QueryResult(success=False, error="Data source not found.")

    config = _build_adapter_config(db, ds)
    connector = get_connector(ds.provider, config)

    start_time = time.time()

    try:
        if ds.provider in ("postgresql", "supabase"):
            return _execute_postgresql(connector, query, max_rows, start_time)
        elif ds.provider == "mysql":
            return _execute_mysql(connector, query, max_rows, start_time)
        elif ds.provider == "sqlserver":
            return _execute_sqlserver(connector, query, max_rows, start_time)
        else:
            return QueryResult(
                success=False,
                error=f"SQL execution not supported for provider: {ds.provider}",
            )
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        logger.error(f"Query execution failed: {e}")
        return QueryResult(
            success=False,
            execution_time_ms=elapsed,
            error=f"Query execution failed: {str(e)}",
        )
    finally:
        try:
            connector.close()
        except Exception:
            pass


def execute_mongo_query(
    db: Session,
    data_source_id: str,
    organization_id: str,
    query: dict,
    max_rows: Optional[int] = None,
) -> QueryResult:
    """
    Execute a validated read-only MongoDB query.

    Args:
        db: Database session.
        data_source_id: Target data source ID.
        organization_id: User's organization ID.
        query: MongoDB query dict.
        max_rows: Maximum rows to return.

    Returns:
        QueryResult with results.
    """
    if max_rows is None:
        max_rows = ai_settings.AI_MAX_ROWS

    ds = (
        db.query(DataSource)
        .filter(
            DataSource.id == data_source_id,
            DataSource.organization_id == organization_id,
            DataSource.status != "deleted",
        )
        .first()
    )
    if not ds:
        return QueryResult(success=False, error="Data source not found.", query_type="MONGO_QUERY")

    config = _build_adapter_config(db, ds)
    connector = get_connector(ds.provider, config)
    start_time = time.time()

    try:
        client = connector._get_client()
        db_name = config.get("database_name", "")
        mongo_db = client[db_name]

        collection_name = query.get("collection", "")
        operation = query.get("operation", "find").lower()
        collection = mongo_db[collection_name]

        if operation == "find":
            filter_criteria = query.get("filter", {})
            projection = query.get("projection", None)
            sort = query.get("sort", None)
            limit = min(query.get("limit", max_rows), max_rows)

            cursor = collection.find(filter_criteria, projection)
            if sort:
                cursor = cursor.sort(sort)
            cursor = cursor.limit(limit)

            rows = []
            columns_set = set()
            for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                columns_set.update(doc.keys())
                rows.append(doc)

            elapsed = int((time.time() - start_time) * 1000)
            return QueryResult(
                success=True,
                columns=sorted(list(columns_set)),
                rows=rows,
                row_count=len(rows),
                execution_time_ms=elapsed,
                truncated=len(rows) >= limit,
                query_type="MONGO_QUERY",
            )

        elif operation == "aggregate":
            pipeline = query.get("pipeline", [])
            # Add $limit if not present
            has_limit = any("$limit" in stage for stage in pipeline if isinstance(stage, dict))
            if not has_limit:
                pipeline.append({"$limit": max_rows})

            cursor = collection.aggregate(pipeline)
            rows = []
            columns_set = set()
            for doc in cursor:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                columns_set.update(doc.keys())
                rows.append(doc)

            elapsed = int((time.time() - start_time) * 1000)
            return QueryResult(
                success=True,
                columns=sorted(list(columns_set)),
                rows=rows,
                row_count=len(rows),
                execution_time_ms=elapsed,
                query_type="MONGO_QUERY",
            )

        elif operation in ("count", "countdocuments"):
            filter_criteria = query.get("filter", {})
            count = collection.count_documents(filter_criteria)
            elapsed = int((time.time() - start_time) * 1000)
            return QueryResult(
                success=True,
                columns=["count"],
                rows=[{"count": count}],
                row_count=1,
                execution_time_ms=elapsed,
                query_type="MONGO_QUERY",
            )

        else:
            return QueryResult(
                success=False,
                error=f"Unsupported MongoDB operation: {operation}",
                query_type="MONGO_QUERY",
            )

    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        logger.error(f"MongoDB query execution failed: {e}")
        return QueryResult(
            success=False,
            execution_time_ms=elapsed,
            error=f"Query execution failed: {str(e)}",
            query_type="MONGO_QUERY",
        )
    finally:
        try:
            connector.close()
        except Exception:
            pass


def _execute_postgresql(connector, query: str, max_rows: int, start_time: float) -> QueryResult:
    """Execute a query on PostgreSQL/Supabase."""
    import psycopg2

    params = connector.pg_config.to_psycopg2_params()
    conn = psycopg2.connect(**params)
    conn.set_session(readonly=True, autocommit=True)

    cursor = conn.cursor()
    try:
        # Set statement timeout
        timeout_ms = ai_settings.AI_QUERY_TIMEOUT_MS
        cursor.execute(f"SET statement_timeout = {timeout_ms};")

        cursor.execute(query)
        desc_cols = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(max_rows + 1) if cursor.description else []

        truncated = len(rows) > max_rows
        if truncated:
            rows = rows[:max_rows]

        row_dicts = [dict(zip(desc_cols, row)) for row in rows]

        elapsed = int((time.time() - start_time) * 1000)
        return QueryResult(
            success=True,
            columns=desc_cols,
            rows=row_dicts,
            row_count=len(row_dicts),
            execution_time_ms=elapsed,
            truncated=truncated,
        )
    finally:
        cursor.close()
        conn.close()


def _execute_mysql(connector, query: str, max_rows: int, start_time: float) -> QueryResult:
    """Execute a query on MySQL."""
    import pymysql

    params = connector._get_connection_params()
    conn = pymysql.connect(**params)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute(query)
        rows = cursor.fetchmany(max_rows + 1)

        truncated = len(rows) > max_rows
        if truncated:
            rows = rows[:max_rows]

        desc_cols = list(rows[0].keys()) if rows else []

        elapsed = int((time.time() - start_time) * 1000)
        return QueryResult(
            success=True,
            columns=desc_cols,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=elapsed,
            truncated=truncated,
        )
    finally:
        cursor.close()
        conn.close()


def _execute_sqlserver(connector, query: str, max_rows: int, start_time: float) -> QueryResult:
    """Execute a query on SQL Server."""
    import pyodbc

    conn_str = connector.sql_config.to_odbc_connection_string()
    conn = pyodbc.connect(conn_str, timeout=connector.sql_config.connect_timeout)
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        desc_cols = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(max_rows + 1) if cursor.description else []

        truncated = len(rows) > max_rows
        if truncated:
            rows = rows[:max_rows]

        row_dicts = [dict(zip(desc_cols, list(row))) for row in rows]

        elapsed = int((time.time() - start_time) * 1000)
        return QueryResult(
            success=True,
            columns=desc_cols,
            rows=row_dicts,
            row_count=len(row_dicts),
            execution_time_ms=elapsed,
            truncated=truncated,
        )
    finally:
        cursor.close()
        conn.close()
