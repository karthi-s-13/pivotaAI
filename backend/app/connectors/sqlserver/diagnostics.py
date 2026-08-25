"""
SQL Server Connection Diagnostics.

Runs structured, step-by-step diagnostic checks on database connectivity,
validating DNS, TCP port, TLS handshake, Auth, and Metadata permissions.
"""

import socket
import time
from typing import Dict, Any, List

from app.connectors.base import ConnectionTestResult, ConnectionTestStep
from app.connectors.sqlserver.config import SQLServerConnectionConfig
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


class DriverNotAvailableError(ConnectorError):
    """Raised when pyodbc or the requested SQL Server ODBC driver is missing."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="DRIVER_NOT_AVAILABLE",
            title="ODBC Driver Not Available",
            safe_message="Microsoft SQL Server ODBC driver is not installed on the Pivota server.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Install the supported Microsoft ODBC Driver for SQL Server and restart the backend.",
        )


def run_diagnostics(config: SQLServerConnectionConfig) -> ConnectionTestResult:
    """Run 7 structured connection diagnostic steps for SQL Server."""
    step_config = ConnectionTestStep(name="configuration", status="pending")
    step_driver = ConnectionTestStep(name="driver", status="pending")
    step_net = ConnectionTestStep(name="network", status="pending")
    step_tls = ConnectionTestStep(name="encryption", status="pending")
    step_auth = ConnectionTestStep(name="authentication", status="pending")
    step_db = ConnectionTestStep(name="database_access", status="pending")
    step_metadata = ConnectionTestStep(name="metadata_access", status="pending")

    steps = [step_config, step_driver, step_net, step_tls, step_auth, step_db, step_metadata]
    start_total = time.time()

    # Step 1: Configuration check
    try:
        if not config.host:
            raise InvalidConfigurationError(technical_details="Host is empty.")
        if not config.database:
            raise InvalidConfigurationError(technical_details="Database name is empty.")
        if config.authentication_method == "sql_server" and not config.username:
            raise InvalidConfigurationError(technical_details="Username is empty for SQL Authentication.")
        step_config.status = "success"
        step_config.latency_ms = 0.0
    except ConnectorError as e:
        step_config.status = "failed"
        step_config.message = e.safe_message
        _skip_remaining(steps, ["driver", "network", "encryption", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(e, steps, start_total)

    # Step 2: Driver Availability check
    try:
        import pyodbc
        available_drivers = pyodbc.drivers()
        if config.driver not in available_drivers:
            # Fallback check: if default 'SQL Server' is not in drivers but another 'ODBC Driver *' is present
            matching = [d for d in available_drivers if "SQL Server" in d or "ODBC Driver" in d]
            if matching:
                config.driver = matching[0]
            else:
                raise DriverNotAvailableError(
                    technical_details=f"Configured driver '{config.driver}' not found in installed drivers: {available_drivers}"
                )
        step_driver.status = "success"
        step_driver.latency_ms = 0.0
    except (ImportError, ConnectorError) as e:
        step_driver.status = "failed"
        err = e if isinstance(e, ConnectorError) else DriverNotAvailableError(technical_details=str(e))
        step_driver.message = err.safe_message
        _skip_remaining(steps, ["network", "encryption", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(err, steps, start_total)

    # Step 3: DNS & TCP Connectivity check
    dns_start = time.time()
    try:
        socket.getaddrinfo(config.host, config.port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        step_net.status = "failed"
        err = DNSResolutionError(technical_details=str(e))
        step_net.message = err.safe_message
        _skip_remaining(steps, ["encryption", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(err, steps, start_total)

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
        _skip_remaining(steps, ["encryption", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(err, steps, start_total)
    except Exception as e:
        step_net.status = "failed"
        err = NetworkConnectionError(technical_details=str(e))
        step_net.message = err.safe_message
        _skip_remaining(steps, ["encryption", "authentication", "database_access", "metadata_access"])
        return _make_failure_result(err, steps, start_total)

    # Establish full ODBC connection
    driver_start = time.time()
    conn = None
    try:
        import pyodbc
        conn_str = config.to_odbc_connection_string()
        conn = pyodbc.connect(conn_str, timeout=config.connect_timeout)
        latency = round((time.time() - driver_start) * 1000, 2)

        # TLS step succeeds if connection succeeds
        step_tls.status = "success"
        step_tls.latency_ms = latency / 4

        # Auth step succeeds
        step_auth.status = "success"
        step_auth.latency_ms = latency / 4

        # Database access check
        step_db.status = "success"
        step_db.latency_ms = latency / 4

        # Test Metadata Permission by selecting from sys.tables
        meta_start = time.time()
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 name FROM sys.tables;")
        cursor.fetchone()
        cursor.close()
        step_metadata.status = "success"
        step_metadata.latency_ms = round((time.time() - meta_start) * 1000, 2)

        # Retrieve server info for health summary
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION, @@SERVICENAME, ORIGINAL_LOGIN();")
        row = cursor.fetchone()
        version, service_name, current_user = row[0], row[1], row[2]
        cursor.close()

        conn.close()

        total_latency = round((time.time() - start_total) * 1000, 2)
        return ConnectionTestResult(
            success=True,
            message="Connection successful",
            latency_ms=total_latency,
            server_version=version.split("\n")[0] if version else "SQL Server",
            details={
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "user": current_user,
                "service": service_name,
            },
            steps=steps,
        )

    except pyodbc.Error as e:
        err_msg = str(e).strip()
        latency = round((time.time() - driver_start) * 1000, 2)

        # Classify the pyodbc ODBC error codes and SQLState
        sqlstate = e.args[0] if len(e.args) > 0 else ""
        
        # Check SQL Server specific error codes inside message (e.g. 18456, 4060)
        if "18456" in err_msg or "Login failed" in err_msg:
            step_tls.status = "success"
            step_tls.latency_ms = latency / 2
            step_auth.status = "failed"
            step_auth.message = "Authentication failed: invalid username or password."
            _fail_remaining(steps, ["database_access", "metadata_access"], "Auth failure skipped database access.")
            err = AuthenticationFailedError(technical_details=err_msg)
        elif "4060" in err_msg or "Cannot open database" in err_msg:
            step_tls.status = "success"
            step_tls.latency_ms = latency / 3
            step_auth.status = "success"
            step_auth.latency_ms = latency / 3
            step_db.status = "failed"
            step_db.message = f"Database '{config.database}' not found on server."
            _fail_remaining(steps, ["metadata_access"], "DB lookup failed.")
            err = DatabaseNotFoundError(technical_details=err_msg)
        elif "HYT00" in sqlstate or "timeout" in err_msg.lower():
            step_tls.status = "failed"
            step_tls.message = "Connection timeout during database connection attempt."
            _fail_remaining(steps, ["authentication", "database_access", "metadata_access"], "Connection timed out.")
            err = ConnectionTimeoutError(technical_details=err_msg)
        elif "08S01" in sqlstate or "ssl" in err_msg.lower() or "certificate" in err_msg.lower() or "encryption" in err_msg.lower():
            step_tls.status = "failed"
            step_tls.message = f"Encryption/TLS negotiation failed: {err_msg}"
            _fail_remaining(steps, ["authentication", "database_access", "metadata_access"], "TLS failure skipped step.")
            err = TLSError(technical_details=err_msg)
        elif "229" in err_msg or "permission denied" in err_msg.lower() or "sys.tables" in err_msg:
            step_tls.status = "success"
            step_auth.status = "success"
            step_db.status = "success"
            step_metadata.status = "failed"
            step_metadata.message = f"Access denied to database metadata: {err_msg}"
            err = MetadataPermissionError(technical_details=err_msg)
        else:
            step_tls.status = "success"
            step_auth.status = "success"
            step_db.status = "failed"
            step_db.message = err_msg
            _fail_remaining(steps, ["metadata_access"], "Session initialization failed.")
            err = PermissionDeniedError(technical_details=err_msg)

        if conn:
            try:
                conn.close()
            except Exception:
                pass

        return _make_failure_result(err, steps, start_total)

    except Exception as e:
        err_msg = str(e)
        step_tls.status = "failed"
        step_tls.message = err_msg
        _fail_remaining(steps, ["authentication", "database_access", "metadata_access"], "Unknown connection error.")
        err = ServerError(technical_details=err_msg)
        if conn:
            try:
                conn.close()
            except Exception:
                pass
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
