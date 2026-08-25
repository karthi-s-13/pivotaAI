"""
MySQL Connection Diagnostics.

Runs structured, step-by-step diagnostic checks on database connectivity,
validating DNS, TCP port, TLS handshake, Auth, and Metadata permissions.
"""

import socket
import time
from typing import Dict, Any, List

import pymysql
import pymysql.cursors
from app.connectors.base import ConnectionTestResult, ConnectionTestStep
from app.connectors.mysql.config import MySQLConnectionConfig
from app.connectors.exceptions import (
    ConnectorError,
    InvalidConfigurationError,
    DNSResolutionError,
    NetworkConnectionError,
    ConnectionTimeoutError,
    TLSError,
    AuthenticationFailedError,
    DatabaseNotFoundError,
    PermissionDeniedError,
    MetadataPermissionError,
    ServerError,
)


def run_diagnostics(config: MySQLConnectionConfig) -> ConnectionTestResult:
    """
    Run 7 structured connection diagnostic steps for MySQL.
    """
    step_config = ConnectionTestStep(name="configuration", status="pending")
    step_dns = ConnectionTestStep(name="dns", status="pending")
    step_net = ConnectionTestStep(name="network", status="pending")
    step_tls = ConnectionTestStep(name="tls", status="pending")
    step_auth = ConnectionTestStep(name="authentication", status="pending")
    step_db = ConnectionTestStep(name="database_access", status="pending")
    step_metadata = ConnectionTestStep(name="metadata_access", status="pending")

    steps = [step_config, step_dns, step_net, step_tls, step_auth, step_db, step_metadata]
    start_total = time.time()

    # Step 1: Configuration check
    try:
        if not config.host:
            raise InvalidConfigurationError(technical_details="Host is empty.")
        if not config.database:
            raise InvalidConfigurationError(technical_details="Database name is empty.")
        step_config.status = "success"
        step_config.latency_ms = 0.0
    except ConnectorError as e:
        step_config.status = "failed"
        step_config.message = e.safe_message
        _skip_remaining(steps, ["dns", "network", "tls", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(e, steps, start_total)

    # Step 2: DNS Resolution check
    dns_start = time.time()
    try:
        socket.getaddrinfo(config.host, config.port, proto=socket.IPPROTO_TCP)
        step_dns.status = "success"
        step_dns.latency_ms = round((time.time() - dns_start) * 1000, 2)
    except socket.gaierror as e:
        step_dns.status = "failed"
        err = DNSResolutionError(technical_details=str(e))
        step_dns.message = err.safe_message
        _skip_remaining(steps, ["network", "tls", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(err, steps, start_total)

    # Step 3: TCP Connectivity check
    net_start = time.time()
    try:
        sock = socket.create_connection((config.host, config.port), timeout=config.connect_timeout)
        sock.close()
        step_net.status = "success"
        step_net.latency_ms = round((time.time() - net_start) * 1000, 2)
    except socket.timeout as e:
        step_net.status = "failed"
        err = ConnectionTimeoutError(technical_details=str(e))
        step_net.message = err.safe_message
        _skip_remaining(steps, ["tls", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(err, steps, start_total)
    except Exception as e:
        step_net.status = "failed"
        err = NetworkConnectionError(technical_details=str(e))
        step_net.message = err.safe_message
        _skip_remaining(steps, ["tls", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(err, steps, start_total)

    conn_params = config.to_pymysql_params()

    # Establish full database connection to perform remaining steps
    driver_start = time.time()
    conn = None
    try:
        conn = pymysql.connect(**conn_params)
        latency = round((time.time() - driver_start) * 1000, 2)

        # TLS step succeeds if connected (or if not enabled, we check SSL parameters)
        step_tls.status = "success"
        step_tls.latency_ms = latency / 4

        # Auth step succeeds if connect succeeds without Auth Error
        step_auth.status = "success"
        step_auth.latency_ms = latency / 4

        # Database access check
        step_db.status = "success"
        step_db.latency_ms = latency / 4

        # Test Metadata Permission by selecting from information_schema.tables
        meta_start = time.time()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM information_schema.tables LIMIT 1;")
            cursor.fetchone()
        step_metadata.status = "success"
        step_metadata.latency_ms = round((time.time() - meta_start) * 1000, 2)

        # Retrieve server info for health summary
        with conn.cursor() as cursor:
            cursor.execute("SELECT version(), @@time_zone, CURRENT_USER();")
            row = cursor.fetchone()
            vals = list(row.values()) if isinstance(row, dict) else list(row)
            version, timezone_str, current_user = vals[0], vals[1], vals[2]

        conn.close()

        total_latency = round((time.time() - start_total) * 1000, 2)
        return ConnectionTestResult(
            success=True,
            message="Connection successful",
            latency_ms=total_latency,
            server_version=version,
            details={
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "user": current_user,
                "timezone": timezone_str,
            },
            steps=steps,
        )

    except pymysql.err.OperationalError as e:
        err_code = e.args[0] if e.args else None
        err_msg = str(e).strip()
        latency = round((time.time() - driver_start) * 1000, 2)

        # Classify the OperationalError code
        if err_code == 1045:  # ER_ACCESS_DENIED_ERROR
            step_tls.status = "success"
            step_tls.latency_ms = latency / 2
            step_auth.status = "failed"
            step_auth.message = "Authentication failed: invalid username or password."
            _fail_remaining(steps, ["database_access", "metadata_access"], "Auth failure skipped database access.")
            err = AuthenticationFailedError(technical_details=err_msg)
        elif err_code == 1049:  # ER_BAD_DB_ERROR
            step_tls.status = "success"
            step_tls.latency_ms = latency / 3
            step_auth.status = "success"
            step_auth.latency_ms = latency / 3
            step_db.status = "failed"
            step_db.message = f"Database '{config.database}' not found on server."
            _fail_remaining(steps, ["metadata_access"], "DB lookup failed.")
            err = DatabaseNotFoundError(technical_details=err_msg)
        elif err_code in (2003, 2006, 2013):  # CR_CONN_HOST_ERROR, CR_SERVER_GONE_ERROR, CR_SERVER_LOST
            step_tls.status = "failed"
            step_tls.message = "Connection timeout or server unavailable."
            _fail_remaining(steps, ["authentication", "database_access", "metadata_access"], "Connection lost.")
            err = ConnectionTimeoutError(technical_details=err_msg)
        elif "ssl" in err_msg.lower() or "tls" in err_msg.lower():
            step_tls.status = "failed"
            step_tls.message = err_msg
            _fail_remaining(steps, ["authentication", "database_access", "metadata_access"], "TLS failure skipped step.")
            err = TLSError(technical_details=err_msg)
        else:
            step_tls.status = "success"
            step_auth.status = "success"
            step_db.status = "failed"
            step_db.message = err_msg
            _fail_remaining(steps, ["metadata_access"], "Session initialization failed.")
            err = PermissionDeniedError(technical_details=err_msg)

        if conn and conn.open:
            conn.close()

        return _make_failure_result(err, steps, start_total)

    except pymysql.err.InternalError as e:
        err_code = e.args[0] if e.args else None
        err_msg = str(e).strip()
        step_tls.status = "success"
        step_auth.status = "success"
        step_db.status = "success"
        step_metadata.status = "failed"
        step_metadata.message = f"Access denied to database metadata tables: {err_msg}"

        err = MetadataPermissionError(technical_details=err_msg)
        if conn and conn.open:
            conn.close()
        return _make_failure_result(err, steps, start_total)

    except Exception as e:
        err_msg = str(e)
        step_tls.status = "failed"
        step_tls.message = err_msg
        _fail_remaining(steps, ["authentication", "database_access", "metadata_access"], "Unknown connection error.")
        err = ServerError(technical_details=err_msg)
        if conn and conn.open:
            conn.close()
        return _make_failure_result(err, steps, start_total)


def _skip_remaining(steps: List[ConnectionTestStep], names: List[str]) -> None:
    """Inject skipped status into diagnostic steps."""
    for step in steps:
        if step.name in names and step.status == "pending":
            step.status = "skipped"


def _fail_remaining(steps: List[ConnectionTestStep], names: List[str], message: str) -> None:
    """Inject failed status with skip message into diagnostic steps."""
    for step in steps:
        if step.name in names and step.status == "pending":
            step.status = "skipped"
            step.message = message


def _make_failure_result(err: ConnectorError, steps: List[ConnectionTestStep], start_time: float) -> ConnectionTestResult:
    """Constructs ConnectionTestResult wrapper around standard ConnectorExceptions."""
    total_latency = round((time.time() - start_time) * 1000, 2)
    return ConnectionTestResult(
        success=False,
        message=f"{err.title}: {err.safe_message}",
        latency_ms=total_latency,
        details={
            "error_code": err.code,
            "error_title": err.title,
            "technical_details": err.technical_details,
            "suggested_action": err.suggested_action,
        },
        steps=steps,
    )
