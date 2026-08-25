"""
MongoDB Connection Configuration.

Canonical configuration model for MongoDB connections, supporting:
  - Individual host/port/credentials parameters
  - Full connection URI (mongodb:// and mongodb+srv://)
  - Atlas cloud deployments
  - TLS/SSL options
  - Authentication database (authSource)
  - Replica sets and read preferences

Never logs or exposes credentials. SSRF protection for private IP ranges.
"""

import ipaddress
import socket
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, SecretStr


# Private/reserved IP prefixes to block in public deployment mode
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),     # loopback
    ipaddress.ip_network("10.0.0.0/8"),      # private Class A
    ipaddress.ip_network("172.16.0.0/12"),   # private Class B
    ipaddress.ip_network("192.168.0.0/16"),  # private Class C
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("::1/128"),         # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),        # IPv6 private
    ipaddress.ip_network("169.254.0.0/16"),  # cloud metadata APIPA
]

# Block known cloud metadata endpoints
_BLOCKED_HOSTNAMES = {
    "169.254.169.254",   # AWS/GCP/Azure IMDS
    "metadata.google.internal",
    "metadata",
}


class MongoDBConnectionConfig(BaseModel):
    """
    Canonical MongoDB connection configuration.

    Parsed from individual parameters or URI string.
    Credentials are kept as SecretStr and never included in __repr__ or logs.
    """

    # Core connection
    uri: Optional[str] = None          # Raw URI (stored temporarily, never logged)
    host: Optional[str] = None
    port: Optional[int] = 27017
    database: Optional[str] = None

    # Authentication
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    auth_source: str = "admin"

    # TLS
    tls: bool = False
    tls_allow_invalid_certificates: bool = False

    # MongoDB topology options
    replica_set: Optional[str] = None
    direct_connection: Optional[bool] = None

    # Timeouts (ms)
    server_selection_timeout_ms: int = 10000
    connect_timeout_ms: int = 10000

    # Deployment
    deployment: str = "self_hosted"   # "self_hosted" | "atlas"

    # Network mode for SSRF policy
    network_mode: str = "public"      # "public" | "private"

    # Sample size for schema inference
    sample_size: int = 500

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "MongoDBConnectionConfig":
        """Build config from a flat dict (typically from the service layer)."""
        conn_str = config.get("connection_string") or config.get("uri")
        if conn_str:
            return cls._from_uri(conn_str, config)

        # Extract password — support plain string or SecretStr
        raw_password = config.get("password")
        if isinstance(raw_password, SecretStr):
            secret = raw_password
        elif raw_password:
            secret = SecretStr(raw_password)
        else:
            secret = None

        provider_config = config.get("provider_config") or {}

        return cls(
            host=config.get("host"),
            port=int(config.get("port", 27017) or 27017),
            database=config.get("database_name") or provider_config.get("database_name"),
            username=config.get("username") or provider_config.get("username"),
            password=secret,
            auth_source=config.get("auth_source") or provider_config.get("auth_source") or "admin",
            tls=bool(config.get("ssl_enabled") or config.get("tls") or provider_config.get("tls", False)),
            tls_allow_invalid_certificates=bool(
                config.get("tls_allow_invalid_certificates") or
                provider_config.get("tls_allow_invalid_certificates", False)
            ),
            replica_set=config.get("replica_set") or provider_config.get("replica_set"),
            direct_connection=config.get("direct_connection") or provider_config.get("direct_connection"),
            server_selection_timeout_ms=int(
                config.get("server_selection_timeout_ms") or
                provider_config.get("server_selection_timeout_ms") or 10000
            ),
            connect_timeout_ms=int(
                config.get("connect_timeout_ms") or
                provider_config.get("connect_timeout_ms") or 10000
            ),
            deployment=config.get("deployment") or provider_config.get("deployment") or "self_hosted",
            network_mode=config.get("network_mode") or "public",
            sample_size=int(config.get("sample_size") or provider_config.get("sample_size") or 500),
        )

    @classmethod
    def _from_uri(cls, uri: str, config: Dict[str, Any]) -> "MongoDBConnectionConfig":
        """Parse a MongoDB URI and merge with any extra config values."""
        from app.core.uri_parser import parse_connection_string

        parsed = parse_connection_string(uri)
        pc = parsed.get("provider_config", {})

        # Detect atlas deployment from mongodb+srv scheme
        deployment = "atlas" if "mongodb+srv" in uri.lower() else config.get("deployment", "self_hosted")

        raw_password = parsed.get("password")
        secret = SecretStr(raw_password) if raw_password else None

        # Merge: URI values take precedence, config provides extras
        return cls(
            uri=uri,
            host=parsed.get("host") or config.get("host"),
            port=parsed.get("port") if parsed.get("port") is not None else (
                None if "mongodb+srv" in uri.lower() else int(config.get("port", 27017) or 27017)
            ),
            database=(
                parsed.get("database_name") or
                config.get("database_name") or
                (config.get("provider_config") or {}).get("database_name")
            ),
            username=parsed.get("username") or config.get("username"),
            password=secret,
            auth_source=pc.get("auth_source") or config.get("auth_source") or "admin",
            tls=(
                pc.get("tls") in ("true", True) or
                pc.get("ssl") in ("true", True) or
                config.get("ssl_enabled", False) or
                "mongodb+srv" in uri.lower()  # Atlas always uses TLS
            ),
            tls_allow_invalid_certificates=pc.get("tlsAllowInvalidCertificates") in ("true", True),
            replica_set=pc.get("replica_set") or pc.get("replicaSet") or config.get("replica_set"),
            direct_connection=pc.get("direct_connection") in ("true", True),
            server_selection_timeout_ms=int(pc.get("serverSelectionTimeoutMS") or 10000),
            connect_timeout_ms=int(pc.get("connectTimeoutMS") or 10000),
            deployment=deployment,
            network_mode=config.get("network_mode") or "public",
            sample_size=int(config.get("sample_size") or 500),
        )

    def validate(self) -> None:
        """Validate configuration; raises ValueError for invalid settings."""
        if not self.uri and not self.host:
            raise ValueError("Host or connection_string URI is required for MongoDB connection.")
        if not self.uri and not self.database:
            raise ValueError("Database name is required for MongoDB connection.")
        if self.port is not None and not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port: {self.port}. Must be between 1 and 65535.")
        if self.sample_size < 1 or self.sample_size > 10000:
            raise ValueError("Sample size must be between 1 and 10000.")

        # SSRF protection: block private IPs unless network_mode = "private"
        if self.network_mode == "public" and self.host:
            self._check_ssrf(self.host)

    def _check_ssrf(self, hostname: str) -> None:
        """Block private/reserved IP addresses to prevent SSRF attacks."""
        if hostname in _BLOCKED_HOSTNAMES:
            raise ValueError(
                f"Connection to '{hostname}' is blocked by the network security policy. "
                "Cloud metadata endpoints and reserved addresses are not permitted."
            )
        # Attempt to resolve hostname to check for private IP
        try:
            resolved = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(resolved)
            for net in _PRIVATE_NETWORKS:
                if ip in net:
                    raise ValueError(
                        f"Connection to private/reserved address '{resolved}' is blocked. "
                        "Set network_mode='private' to allow internal connections."
                    )
        except ValueError:
            raise  # Re-raise our own ValueError
        except Exception:
            pass  # DNS failure handled later in diagnostics

    def to_pymongo_kwargs(self) -> Dict[str, Any]:
        """Build a clean kwargs dict for MongoClient creation."""
        # If full URI is present, use it directly
        if self.uri:
            kwargs: Dict[str, Any] = {
                "host": self.uri,
                "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
                "connectTimeoutMS": self.connect_timeout_ms,
                "socketTimeoutMS": self.connect_timeout_ms,
                "appname": "pivota",
            }
            return kwargs

        kwargs = {
            "host": self.host,
            "port": self.port or 27017,
            "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
            "connectTimeoutMS": self.connect_timeout_ms,
            "socketTimeoutMS": self.connect_timeout_ms,
            "appname": "pivota",
        }

        if self.username:
            kwargs["username"] = self.username

        if self.password:
            kwargs["password"] = self.password.get_secret_value()

        if self.username or self.password:
            kwargs["authSource"] = self.auth_source

        if self.replica_set:
            kwargs["replicaSet"] = self.replica_set

        if self.direct_connection is not None:
            kwargs["directConnection"] = self.direct_connection

        if self.tls:
            kwargs["tls"] = True
            if self.tls_allow_invalid_certificates:
                kwargs["tlsAllowInvalidCertificates"] = True

        return kwargs

    def __repr__(self) -> str:
        """Safe repr — never exposes credentials."""
        host_repr = "atlas_uri" if self.deployment == "atlas" else f"{self.host}:{self.port}"
        return f"MongoDBConnectionConfig(host={host_repr!r}, database={self.database!r}, tls={self.tls})"
