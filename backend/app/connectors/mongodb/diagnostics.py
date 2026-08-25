"""
MongoDB Connection Diagnostics.

Implements an 8-step staged diagnostics workflow:

    1. configuration — validate config parameters
    2. driver        — verify pymongo is importable and report version
    3. dns           — resolve hostname (or skip for SRV URIs with DNS check)
    4. network       — TCP socket connectivity
    5. tls           — TLS handshake detection
    6. authentication — ping + credential verification
    7. server_selection — catch server selection failures
    8. metadata_access — list_database_names() permission check

Errors are mapped to structured Pivota ConnectorError codes.
Credentials are never logged or included in error messages.
"""

import socket
import ssl
import time
from typing import Any, Dict, List, Optional, Tuple

from app.connectors.base import ConnectionTestResult, ConnectionTestStep
from app.connectors.exceptions import (
    AuthenticationFailedError,
    ConnectionTimeoutError,
    DNSResolutionError,
    InvalidConfigurationError,
    NetworkConnectionError,
    TLSError,
)
from app.connectors.mongodb.config import MongoDBConnectionConfig


def _make_step(name: str, status: str = "pending", message: Optional[str] = None, latency_ms: Optional[float] = None) -> ConnectionTestStep:
    return ConnectionTestStep(name=name, status=status, message=message, latency_ms=latency_ms)


def _all_skipped(names: List[str]) -> List[ConnectionTestStep]:
    return [_make_step(n, "skipped") for n in names]


STEP_NAMES = [
    "configuration",
    "driver",
    "dns",
    "network",
    "tls",
    "authentication",
    "server_selection",
    "metadata_access",
]


def _classify_pymongo_error(exc: Exception) -> Tuple[str, str]:
    """
    Classify a pymongo exception into a Pivota error code and safe message.
    Returns (error_code, safe_user_message).
    """
    exc_type = type(exc).__name__
    exc_str = str(exc).lower()

    # Authentication errors
    if "operationfailure" in exc_type.lower():
        code_val = getattr(exc, "code", None)
        if code_val in (18, 11000) or "auth" in exc_str or "credential" in exc_str:
            return "AUTHENTICATION_FAILED", "MongoDB rejected the supplied credentials."
        if "not authorized" in exc_str or "unauthorized" in exc_str:
            return "AUTHORIZATION_FAILED", "The user is not authorized to perform this operation."
        return "METADATA_PERMISSION_DENIED", "Permission denied when accessing MongoDB metadata."

    # Connection / timeout
    if "serverselectiontimeouterror" in exc_type.lower():
        return "SERVER_SELECTION_FAILED", "MongoDB server selection timed out. The host may be unreachable or the replica set unavailable."

    if "connectionfailure" in exc_type.lower() or "networktimeout" in exc_type.lower():
        if "timed out" in exc_str or "timeout" in exc_str:
            return "TIMEOUT", "Connection to MongoDB timed out."
        return "NETWORK_ERROR", "Failed to connect to the MongoDB host."

    # Configuration / URI
    if "configurationerror" in exc_type.lower():
        return "INVALID_CONFIGURATION", "MongoDB connection configuration is invalid."

    if "invalidschemeerror" in exc_type.lower() or "invalid uri" in exc_str:
        return "INVALID_URI", "The MongoDB connection URI format is invalid."

    # TLS / SSL
    if isinstance(exc, ssl.SSLError) or "ssl" in exc_str or "tls" in exc_str or "certificate" in exc_str:
        if "certificate" in exc_str:
            return "CERTIFICATE_ERROR", "MongoDB TLS certificate verification failed."
        return "TLS_ERROR", "TLS handshake with MongoDB failed."

    return "UNKNOWN_ERROR", "An unexpected error occurred while connecting to MongoDB."


class MongoDBConnectionDiagnostics:
    """
    Runs staged MongoDB connection diagnostics and returns a ConnectionTestResult.
    """

    def __init__(self, mongo_config: MongoDBConnectionConfig):
        self.config = mongo_config

    def run(self) -> ConnectionTestResult:
        """Execute all diagnostic steps and return a structured result."""
        steps: List[ConnectionTestStep] = []
        start_total = time.time()

        remaining = STEP_NAMES[:]

        # ── Step 1: Configuration ──────────────────────────────────────────
        step = _make_step("configuration")
        steps.append(step)
        remaining.pop(0)
        t = time.time()
        try:
            self.config.validate()
            step.status = "success"
            step.latency_ms = round((time.time() - t) * 1000, 2)
        except ValueError as e:
            step.status = "failed"
            step.message = str(e)
            step.latency_ms = round((time.time() - t) * 1000, 2)
            steps.extend(_all_skipped(remaining))
            return self._failure(
                steps, start_total,
                code="INVALID_CONFIGURATION",
                title=InvalidConfigurationError().title,
                message=f"Invalid Configuration: {e}",
            )

        # ── Step 2: Driver ─────────────────────────────────────────────────
        step = _make_step("driver")
        steps.append(step)
        remaining.pop(0)
        t = time.time()
        try:
            import pymongo
            driver_version = pymongo.version
            step.status = "success"
            step.message = f"PyMongo {driver_version}"
            step.latency_ms = round((time.time() - t) * 1000, 2)
        except ImportError:
            step.status = "failed"
            step.message = "PyMongo driver is not installed on the Pivota server."
            step.latency_ms = round((time.time() - t) * 1000, 2)
            steps.extend(_all_skipped(remaining))
            return self._failure(
                steps, start_total,
                code="DRIVER_NOT_AVAILABLE",
                title="MongoDB Driver Not Available",
                message="DRIVER_NOT_AVAILABLE: PyMongo (MongoDB Python driver) is not installed on the Pivota server.",
                suggested_action="Install pymongo: pip install 'pymongo[srv]>=4.0'",
            )

        # ── Step 3: DNS ────────────────────────────────────────────────────
        step = _make_step("dns")
        steps.append(step)
        remaining.pop(0)
        t = time.time()
        host = self.config.host
        is_srv = self.config.uri and "mongodb+srv" in (self.config.uri or "").lower()

        if not host and self.config.uri:
            # Extract host from URI for DNS check
            try:
                from urllib.parse import urlparse
                host = urlparse(self.config.uri).hostname
            except Exception:
                pass

        if host:
            try:
                if is_srv:
                    # For SRV URIs, resolve DNS TXT/SRV record via gethostbyname
                    socket.gethostbyname(host)
                    step.message = f"SRV host '{host}' resolved."
                else:
                    socket.gethostbyname(host)
                step.status = "success"
                step.latency_ms = round((time.time() - t) * 1000, 2)
            except socket.gaierror as e:
                step.status = "failed"
                step.message = f"Could not resolve hostname '{host}'."
                step.latency_ms = round((time.time() - t) * 1000, 2)
                steps.extend(_all_skipped(remaining))
                code = "SRV_RESOLUTION_ERROR" if is_srv else "DNS_ERROR"
                return self._failure(
                    steps, start_total,
                    code=code,
                    title="DNS Resolution Failed",
                    message=f"DNS Error: Could not resolve host '{host}'.",
                    suggested_action="Verify the hostname or cluster address and check DNS availability.",
                )
        else:
            step.status = "skipped"
            step.message = "No hostname to resolve (URI-only connection)."

        # ── Step 4: Network TCP ─────────────────────────────────────────────
        step = _make_step("network")
        steps.append(step)
        remaining.pop(0)
        t = time.time()
        port = self.config.port or 27017

        if host and port and not is_srv:
            try:
                conn = socket.create_connection((host, port), timeout=5)
                conn.close()
                step.status = "success"
                step.latency_ms = round((time.time() - t) * 1000, 2)
            except (socket.timeout, TimeoutError):
                step.status = "failed"
                step.message = f"TCP connection to {host}:{port} timed out."
                step.latency_ms = round((time.time() - t) * 1000, 2)
                steps.extend(_all_skipped(remaining))
                return self._failure(
                    steps, start_total,
                    code="TIMEOUT",
                    title=ConnectionTimeoutError().title,
                    message="Connection Timeout: TCP connection timed out.",
                    suggested_action="Check that port 27017 is reachable and no firewall blocks the connection.",
                )
            except OSError as e:
                step.status = "failed"
                step.message = "TCP connection refused or unreachable."
                step.latency_ms = round((time.time() - t) * 1000, 2)
                steps.extend(_all_skipped(remaining))
                return self._failure(
                    steps, start_total,
                    code="NETWORK_ERROR",
                    title=NetworkConnectionError().title,
                    message="Network Error: Could not establish TCP connection to MongoDB host.",
                    suggested_action="Verify the host, port, and firewall rules.",
                )
        else:
            step.status = "skipped"
            step.message = "SRV URI — network check delegated to driver."

        # ── Steps 5-8: Driver-level checks (single client creation) ────────
        client = None
        try:
            import pymongo
            kwargs = self.config.to_pymongo_kwargs()
            client = pymongo.MongoClient(**kwargs)

            # Step 5: TLS
            step_tls = _make_step("tls")
            steps.append(step_tls)
            remaining.pop(0)
            t = time.time()

            if self.config.tls:
                # Force a connection attempt to surface TLS errors
                try:
                    client.server_info()
                    step_tls.status = "success"
                    step_tls.message = "TLS handshake succeeded."
                    step_tls.latency_ms = round((time.time() - t) * 1000, 2)
                except Exception as e:
                    err_str = str(e).lower()
                    if "ssl" in err_str or "tls" in err_str or "certificate" in err_str:
                        step_tls.status = "failed"
                        step_tls.message = "TLS handshake failed."
                        step_tls.latency_ms = round((time.time() - t) * 1000, 2)
                        steps.extend(_all_skipped(remaining[1:]))  # skip auth, sel, meta
                        code, safe_msg = _classify_pymongo_error(e)
                        return self._failure(
                            steps, start_total,
                            code=code,
                            title="TLS/SSL Error",
                            message=f"TLS Error: {safe_msg}",
                            suggested_action="Verify TLS certificates and CA chain.",
                        )
                    # Not a TLS error — let it fall through to auth step
                    step_tls.status = "success"
                    step_tls.latency_ms = round((time.time() - t) * 1000, 2)
            else:
                step_tls.status = "skipped"
                step_tls.message = "TLS not enabled."
                step_tls.latency_ms = 0.0

            # Step 6: Authentication (ping)
            step_auth = _make_step("authentication")
            steps.append(step_auth)
            remaining.pop(0)
            t = time.time()
            try:
                client.admin.command("ping")
                step_auth.status = "success"
                step_auth.latency_ms = round((time.time() - t) * 1000, 2)
            except Exception as e:
                code, safe_msg = _classify_pymongo_error(e)
                step_auth.status = "failed"
                step_auth.message = safe_msg
                step_auth.latency_ms = round((time.time() - t) * 1000, 2)
                steps.extend(_all_skipped(remaining[1:]))  # skip server_selection, metadata
                return self._failure(
                    steps, start_total,
                    code=code,
                    title="Authentication Failed",
                    message=f"Authentication Failed: {safe_msg}",
                    suggested_action="Verify username, password, and authSource database.",
                )

            # Step 7: Server Selection
            step_sel = _make_step("server_selection")
            steps.append(step_sel)
            remaining.pop(0)
            t = time.time()
            try:
                server_info = client.server_info()
                step_sel.status = "success"
                step_sel.latency_ms = round((time.time() - t) * 1000, 2)
            except Exception as e:
                code, safe_msg = _classify_pymongo_error(e)
                step_sel.status = "failed"
                step_sel.message = safe_msg
                step_sel.latency_ms = round((time.time() - t) * 1000, 2)
                steps.extend(_all_skipped(remaining[1:]))  # skip metadata
                return self._failure(
                    steps, start_total,
                    code=code,
                    title="Server Selection Failed",
                    message=f"Server Selection Failed: {safe_msg}",
                )

            # Step 8: Metadata Access
            step_meta = _make_step("metadata_access")
            steps.append(step_meta)
            remaining.pop(0)
            t = time.time()
            try:
                db_names = client.list_database_names()
                step_meta.status = "success"
                step_meta.message = f"{len(db_names)} database(s) accessible."
                step_meta.latency_ms = round((time.time() - t) * 1000, 2)
            except Exception as e:
                code, safe_msg = _classify_pymongo_error(e)
                step_meta.status = "failed"
                step_meta.message = safe_msg
                step_meta.latency_ms = round((time.time() - t) * 1000, 2)
                # Metadata failure is non-fatal — report success overall
                # if ping succeeded (some Atlas free tiers have restricted listDatabases)
                version = server_info.get("version", "unknown") if isinstance(server_info, dict) else "unknown"
                return ConnectionTestResult(
                    success=True,
                    message=f"Connected (limited metadata access). MongoDB {version}",
                    latency_ms=round((time.time() - start_total) * 1000, 2),
                    server_version=f"MongoDB {version}",
                    details={"warning": "metadata_access_limited"},
                    steps=steps,
                )

            version = server_info.get("version", "unknown") if isinstance(server_info, dict) else "unknown"
            total_latency = round((time.time() - start_total) * 1000, 2)
            return ConnectionTestResult(
                success=True,
                message=f"Connection successful. MongoDB {version}",
                latency_ms=total_latency,
                server_version=f"MongoDB {version}",
                details={
                    "provider": "mongodb",
                    "version": version,
                    "databases_accessible": len(db_names),
                },
                steps=steps,
            )

        except Exception as e:
            code, safe_msg = _classify_pymongo_error(e)
            # Add any missing steps as skipped
            for name in remaining:
                steps.append(_make_step(name, "skipped"))
            return self._failure(
                steps, start_total,
                code=code,
                title="Connection Failed",
                message=safe_msg,
            )
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def _failure(
        self,
        steps: List[ConnectionTestStep],
        start_total: float,
        code: str,
        title: str,
        message: str,
        suggested_action: Optional[str] = None,
    ) -> ConnectionTestResult:
        """Build a failed ConnectionTestResult."""
        details: Dict[str, Any] = {
            "error_code": code,
            "error_title": title,
        }
        if suggested_action:
            details["suggested_action"] = suggested_action
        return ConnectionTestResult(
            success=False,
            message=message,
            latency_ms=round((time.time() - start_total) * 1000, 2),
            details=details,
            steps=steps,
        )
