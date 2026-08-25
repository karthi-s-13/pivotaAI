"""
Supabase Connection Configuration.

Handles parameter normalization, URI parsing, automatic hostname derivation,
SSL defaults, and TCP/IP SSRF protection checks.
"""

import socket
import ipaddress
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, SecretStr
from app.core.uri_parser import parse_connection_string

# Private/reserved IP prefixes to block in public deployment mode
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),     # loopback
    ipaddress.ip_network("10.0.0.0/8"),      # private Class A
    ipaddress.ip_network("172.16.0.0/12"),   # private Class B
    ipaddress.ip_network("192.168.0.0/16"),  # private Class C
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("::1/128"),         # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),        # IPv6 private
]

# Block cloud metadata service addresses and local hostnames
_BLOCKED_HOSTNAMES = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata",
    "localhost",
}


class SupabaseConnectionConfig(BaseModel):
    """Canonical connection configuration representation for Supabase database connector."""

    project_url: Optional[str] = None
    project_ref: Optional[str] = None

    host: Optional[str] = None
    port: int = 5432
    database: str = "postgres"

    username: Optional[str] = None
    password: Optional[SecretStr] = None

    ssl_mode: str = "require"  # disable, prefer, require, verify-ca, verify-full
    connect_timeout: int = 10
    connection_method: str = "project"  # project or uri
    pooler_enabled: bool = False
    network_mode: str = "public"
    provider_config: Dict[str, Any] = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SupabaseConnectionConfig":
        """Build and normalize config from input dictionary, resolving derived values."""
        normalized = data.copy()

        # Handle URI connection string/URI
        conn_string = normalized.get("connection_string") or normalized.get("connection_uri")
        if conn_string:
            normalized["connection_method"] = "uri"
            parsed = parse_connection_string(conn_string)

            if parsed.get("host"):
                normalized["host"] = parsed["host"]
            if parsed.get("port"):
                normalized["port"] = int(parsed["port"])
            if parsed.get("database_name"):
                normalized["database"] = parsed["database_name"]
            if parsed.get("username"):
                normalized["username"] = parsed["username"]
            if parsed.get("password"):
                normalized["password"] = parsed["password"]

            p_config = parsed.get("provider_config") or {}
            normalized["provider_config"] = p_config
            if "sslmode" in p_config:
                normalized["ssl_mode"] = p_config["sslmode"]
            if "pooler" in p_config:
                normalized["pooler_enabled"] = str(p_config["pooler"]).lower() == "true"

        # Align database mapping keys
        if "database_name" in normalized and "database" not in normalized:
            normalized["database"] = normalized["database_name"]

        # Parse project_url to extract project_ref if missing
        project_url = normalized.get("project_url")
        if project_url and not normalized.get("project_ref"):
            match = re.search(r"https?://([^./]+)\.supabase\.(?:co|net|com)", project_url)
            if match:
                normalized["project_ref"] = match.group(1)

        # Derive host if not provided but project_ref is available
        project_ref = normalized.get("project_ref")
        if project_ref and not normalized.get("host"):
            # Supabase default direct database host
            normalized["host"] = f"db.{project_ref}.supabase.co"

        # Connection pooler default port settings
        if normalized.get("pooler_enabled") is True and not normalized.get("port"):
            normalized["port"] = 6543
        elif not normalized.get("port"):
            normalized["port"] = 5432

        # Convert password string to SecretStr
        pw = normalized.get("password")
        if pw is not None and not isinstance(pw, SecretStr):
            if str(pw).strip() == "":
                normalized["password"] = None
            else:
                normalized["password"] = SecretStr(str(pw))

        # Filter properties matching class
        class_fields = cls.__fields__.keys()
        init_data = {k: v for k, v in normalized.items() if k in class_fields}

        # Handle provider_config override
        if "provider_config" not in init_data:
            init_data["provider_config"] = normalized.get("provider_config") or {}

        config_obj = cls(**init_data)
        config_obj.validate()
        return config_obj

    def validate(self) -> None:
        """Validate connection details and verify against SSRF/outbound IP policies."""
        # 1. Project URL validation
        if self.project_url:
            if not self.project_url.startswith("https://"):
                raise ValueError("Project URL must use HTTPS scheme")
            from urllib.parse import urlparse
            try:
                parsed_url = urlparse(self.project_url)
                if not parsed_url.netloc or not any(
                    parsed_url.netloc.endswith(suffix)
                    for suffix in [".supabase.co", ".supabase.net", ".supabase.com", "supabase.co"]
                ):
                    raise ValueError("Project URL must be a valid Supabase project domain")
            except Exception:
                raise ValueError("Invalid Project URL format")

        # 2. Required host
        if not self.host:
            raise ValueError("Host is required (could not be derived or provided)")

        # 3. Port check
        if self.port is not None and not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port: {self.port}. Must be 1-65535.")

        # 4. Outbound SSRF Protection
        if self.network_mode == "public" and self.host:
            self._check_ssrf(self.host)

    def _check_ssrf(self, hostname: str) -> None:
        """Verify host IP target is public and not local/private ranges to block SSRF."""
        if hostname in _BLOCKED_HOSTNAMES:
            raise ValueError(
                f"Connection to host '{hostname}' is blocked by network security policy. "
                "Reserved hostnames or cloud metadata endpoints are not permitted."
            )
        try:
            resolved = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(resolved)
            for net in _PRIVATE_NETWORKS:
                if ip in net:
                    raise ValueError(
                        f"Connection to private/reserved IP '{resolved}' is blocked. "
                        "Set network_mode='private' to allow internal connections."
                    )
        except ValueError:
            raise
        except Exception:
            pass  # Handled during DNS diagnostics step

    def to_psycopg2_params(self) -> Dict[str, Any]:
        """Format parameters for psycopg2 driver connection."""
        params = {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "connect_timeout": self.connect_timeout,
        }
        if self.username:
            params["user"] = self.username
        if self.password:
            params["password"] = self.password.get_secret_value()
        if self.ssl_mode:
            params["sslmode"] = self.ssl_mode
        return params
