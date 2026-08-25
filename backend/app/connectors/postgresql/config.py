"""
PostgreSQL Connection Configuration.

Parses and normalizes individual parameters and connection URIs
into a single internal canonical configuration object, protecting secrets.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, SecretStr
from app.core.uri_parser import parse_connection_string


class PostgreSQLConnectionConfig(BaseModel):
    """Canonical configuration representation for PostgreSQL connector."""

    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    ssl_mode: str = "disable"  # disable, prefer, require, verify-ca, verify-full
    connect_timeout: int = 10
    application_name: Optional[str] = "pivota"

    # Enterprise TLS Certifications
    ssl_root_cert: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None

    # Schema Scoping
    schema_name: Optional[str] = "public"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostgreSQLConnectionConfig":
        """
        Build and normalize config from a raw dictionary.
        Supports Individual Parameters and connection URI parsing.
        """
        # Copy to avoid mutating input
        normalized = data.copy()

        # Parse URI connection string if provided
        conn_string = normalized.get("connection_string") or normalized.get("connection_uri")
        if conn_string:
            parsed = parse_connection_string(conn_string)

            # Map parsed keys to expected parameters
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

            # Merge query options (e.g., sslmode, connect_timeout)
            p_config = parsed.get("provider_config") or {}
            if "sslmode" in p_config:
                normalized["ssl_mode"] = p_config["sslmode"]
            if "connect_timeout" in p_config:
                try:
                    normalized["connect_timeout"] = int(p_config["connect_timeout"])
                except ValueError:
                    pass
            if "application_name" in p_config:
                normalized["application_name"] = p_config["application_name"]

        # Support mapping from DB model properties (database_name / ssl_enabled)
        if "database_name" in normalized and "database" not in normalized:
            normalized["database"] = normalized["database_name"]

        if normalized.get("ssl_enabled") is True and normalized.get("ssl_mode") == "disable":
            normalized["ssl_mode"] = "require"

        # Safe defaults
        if not normalized.get("port"):
            normalized["port"] = 5432

        # Convert password to SecretStr if string
        pw = normalized.get("password")
        if pw is not None and not isinstance(pw, SecretStr):
            # If empty string, keep as None
            if str(pw).strip() == "":
                normalized["password"] = None
            else:
                normalized["password"] = SecretStr(str(pw))

        # Re-map key names for ssl mode
        if "sslmode" in normalized:
            normalized["ssl_mode"] = normalized.pop("sslmode")
        if "sslrootcert" in normalized:
            normalized["ssl_root_cert"] = normalized.pop("sslrootcert")
        if "sslcert" in normalized:
            normalized["ssl_cert"] = normalized.pop("sslcert")
        if "sslkey" in normalized:
            normalized["ssl_key"] = normalized.pop("sslkey")
        if "schema" in normalized:
            normalized["schema_name"] = normalized.pop("schema")

        # Select only valid class fields
        class_fields = cls.__fields__.keys()
        init_data = {k: v for k, v in normalized.items() if k in class_fields}

        return cls(**init_data)

    def to_psycopg2_params(self) -> Dict[str, Any]:
        """Convert config into psycopg2-compatible connect options."""
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
        if self.application_name:
            params["application_name"] = self.application_name

        # Enterprise TLS File Mapping
        if self.ssl_root_cert:
            params["sslrootcert"] = self.ssl_root_cert
        if self.ssl_cert:
            params["sslcert"] = self.ssl_cert
        if self.ssl_key:
            params["sslkey"] = self.ssl_key

        return params

    def get_masked_config(self) -> Dict[str, Any]:
        """Return config with password masked for safe logging or rendering."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": "••••••••" if self.password else None,
            "ssl_mode": self.ssl_mode,
            "connect_timeout": self.connect_timeout,
            "application_name": self.application_name,
            "ssl_root_cert": self.ssl_root_cert,
            "ssl_cert": self.ssl_cert,
            "ssl_key": self.ssl_key,
            "schema_name": self.schema_name,
        }
