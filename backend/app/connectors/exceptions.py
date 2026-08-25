"""
Connector Custom Exceptions.

Standardized exceptions representing enterprise connectivity, security, and extraction errors.
"""

class ConnectorError(Exception):
    """Base class for all connector exceptions."""

    def __init__(
        self,
        code: str,
        title: str,
        safe_message: str,
        technical_details: str = "",
        suggested_action: str = "",
    ):
        super().__init__(safe_message)
        self.code = code
        self.title = title
        self.safe_message = safe_message
        self.technical_details = technical_details
        self.suggested_action = suggested_action


class InvalidConfigurationError(ConnectorError):
    """Raised when connection arguments are invalid or missing."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="INVALID_CONFIGURATION",
            title="Invalid Configuration",
            safe_message="Connection configuration is invalid or missing required fields.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify host, port, database name, and other connectivity inputs.",
        )


class DNSResolutionError(ConnectorError):
    """Raised when the database host cannot be resolved."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="DNS_ERROR",
            title="DNS Resolution Failed",
            safe_message="Could not resolve database host IP address.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify the hostname spelling and confirm DNS availability.",
        )


class NetworkConnectionError(ConnectorError):
    """Raised when TCP socket connectivity cannot be established."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="NETWORK_ERROR",
            title="Network Connection Failed",
            safe_message="Failed to connect to database host network port.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify that the database port is open and no firewall blocks incoming traffic.",
        )


class ConnectionTimeoutError(ConnectorError):
    """Raised when a socket connect or operation times out."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="TIMEOUT",
            title="Connection Timeout",
            safe_message="Connection attempt timed out.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Increase network connect timeout settings or check network latency/congestion.",
        )


class TLSError(ConnectorError):
    """Raised when SSL/TLS handshakes or certifications fail."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="TLS_ERROR",
            title="SSL/TLS Handshake Failed",
            safe_message="Could not establish secure TLS session with the server.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify SSL configurations, root certificates, and client keys/certificates.",
        )


class AuthenticationFailedError(ConnectorError):
    """Raised when login credentials are rejected by the server."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            title="Authentication Failed",
            safe_message="Database rejected the supplied credentials.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify the username and password and confirm that the user has permission to connect.",
        )


class DatabaseNotFoundError(ConnectorError):
    """Raised when the specified target database does not exist."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="DATABASE_NOT_FOUND",
            title="Database Not Found",
            safe_message="Target database does not exist on this server.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Check spelling of the database name or confirm that the database has been created.",
        )


class PermissionDeniedError(ConnectorError):
    """Raised when general connection permissions are denied."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="PERMISSION_DENIED",
            title="Permission Denied",
            safe_message="User lacks permission to establish a session.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify that the database user has CONNECT privileges on the target database.",
        )


class MetadataPermissionError(ConnectorError):
    """Raised when catalog schema metadata permissions are denied."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="METADATA_PERMISSION_DENIED",
            title="Metadata Access Denied",
            safe_message="User lacks permission to read metadata schemas (e.g. information_schema).",
            technical_details=technical_details,
            suggested_action=suggested_action or "Grant SELECT permissions to the user on pg_catalog, information_schema, and user tables.",
        )


class UnsupportedConfigurationError(ConnectorError):
    """Raised when configuration option is not supported."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="UNSUPPORTED_CONFIGURATION",
            title="Unsupported Configuration",
            safe_message="Connection configuration option is not supported by the provider.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify that configuration options match database version/provider requirements.",
        )


class DriverError(ConnectorError):
    """Raised when database driver itself crashes or reports driver failure."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="DRIVER_ERROR",
            title="Database Driver Error",
            safe_message="Database driver failed to initialize or execute connection.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Check that driver library (e.g. psycopg2) is installed and compatible with runtime OS.",
        )


class ServerError(ConnectorError):
    """Raised when server responds with internal errors."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="SERVER_ERROR",
            title="Internal Database Server Error",
            safe_message="Database server encountered an internal error.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify server status or consult system administrator logs.",
        )


class DriverNotAvailableError(ConnectorError):
    """Raised when the required database driver is not installed."""

    def __init__(self, driver_name: str = "database", technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="DRIVER_NOT_AVAILABLE",
            title="Database Driver Not Available",
            safe_message=f"{driver_name} driver is not installed on the Pivota server.",
            technical_details=technical_details,
            suggested_action=suggested_action or f"Install the required {driver_name} driver package.",
        )


class SRVResolutionError(ConnectorError):
    """Raised when a MongoDB SRV DNS record cannot be resolved."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="SRV_RESOLUTION_ERROR",
            title="SRV DNS Resolution Failed",
            safe_message="Could not resolve MongoDB Atlas SRV DNS record.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify the Atlas cluster hostname and ensure DNS resolution is available.",
        )


class ServerSelectionError(ConnectorError):
    """Raised when PyMongo server selection times out."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="SERVER_SELECTION_FAILED",
            title="Server Selection Failed",
            safe_message="MongoDB server selection timed out. The replica set or cluster may be unavailable.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify server availability, replica set configuration, and network access.",
        )


class CertificateError(ConnectorError):
    """Raised when TLS certificate validation fails."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="CERTIFICATE_ERROR",
            title="TLS Certificate Error",
            safe_message="TLS certificate verification failed. The server certificate could not be validated.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify that the correct CA certificate is installed or configure tlsAllowInvalidCertificates for development.",
        )


class AuthorizationFailedError(ConnectorError):
    """Raised when a user is authenticated but not authorized for an operation."""

    def __init__(self, technical_details: str = "", suggested_action: str = ""):
        super().__init__(
            code="AUTHORIZATION_FAILED",
            title="Authorization Failed",
            safe_message="User is authenticated but not authorized to perform this operation.",
            technical_details=technical_details,
            suggested_action=suggested_action or "Verify that the database user has the required roles and permissions.",
        )
