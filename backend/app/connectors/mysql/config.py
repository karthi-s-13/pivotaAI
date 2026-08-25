"""
MySQL Connection Configuration.

Parses and normalizes individual parameters and connection URIs
into a single internal canonical configuration object, protecting secrets.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, SecretStr
from app.core.uri_parser import parse_connection_string


class MySQLConnectionConfig(BaseModel):
    """Canonical configuration representation for MySQL connector."""

    host: str = "localhost"
    port: int = 3306
    database: str = ""
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    ssl_mode: str = "disabled"  # disabled, required, verify_ca, verify_identity
    connect_timeout: int = 10
    charset: str = "utf8mb4"

    # Enterprise TLS Certifications
    ssl_ca: Optional[str] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MySQLConnectionConfig":
        """
        Build and normalize config from a raw dictionary.
        Supports Individual Parameters and connection URI parsing.
        """
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

            # Merge query options (e.g., ssl_mode, connect_timeout)
            p_config = parsed.get("provider_config") or {}
            if "ssl_mode" in p_config:
                normalized["ssl_mode"] = p_config["ssl_mode"]
            elif "sslmode" in p_config:
                normalized["ssl_mode"] = p_config["sslmode"]
            if "connect_timeout" in p_config:
                try:
                    normalized["connect_timeout"] = int(p_config["connect_timeout"])
                except ValueError:
                    pass
            if "charset" in p_config:
                normalized["charset"] = p_config["charset"]

        # Support mapping from DB model properties (database_name / ssl_enabled)
        if "database_name" in normalized and "database" not in normalized:
            normalized["database"] = normalized["database_name"]

        if normalized.get("ssl_enabled") is True and normalized.get("ssl_mode") == "disabled":
            normalized["ssl_mode"] = "required"

        # Safe defaults
        if not normalized.get("port"):
            normalized["port"] = 3306

        # Convert password to SecretStr if string
        pw = normalized.get("password")
        if pw is not None and not isinstance(pw, SecretStr):
            # If empty string, keep as None
            if str(pw).strip() == "":
                normalized["password"] = None
            else:
                normalized["password"] = SecretStr(str(pw))

        # Re-map key names for ssl
        if "sslmode" in normalized:
            normalized["ssl_mode"] = normalized.pop("sslmode")
        if "sslca" in normalized:
            normalized["ssl_ca"] = normalized.pop("sslca")
        if "sslrootcert" in normalized:
            normalized["ssl_ca"] = normalized.pop("sslrootcert")
        if "sslcert" in normalized:
            normalized["ssl_cert"] = normalized.pop("sslcert")
        if "sslkey" in normalized:
            normalized["ssl_key"] = normalized.pop("sslkey")

        # Select only valid class fields
        class_fields = cls.__fields__.keys()
        init_data = {k: v for k, v in normalized.items() if k in class_fields}

        return cls(**init_data)

    def to_pymysql_params(self) -> Dict[str, Any]:
        """Convert config into pymysql-compatible connect options."""
        params = {
            "host": self.host,
            "port": self.port,
            "database": self.database if self.database else None,
            "connect_timeout": self.connect_timeout,
            "charset": self.charset,
        }

        if self.username:
            params["user"] = self.username
        if self.password:
            params["password"] = self.password.get_secret_value()

        # Handle SSL params for pymysql
        if self.ssl_mode != "disabled":
            ssl_config = {}
            if self.ssl_ca:
                ssl_config["ca"] = self.ssl_ca
            if self.ssl_cert:
                ssl_config["cert"] = self.ssl_cert
            if self.ssl_key:
                ssl_config["key"] = self.ssl_key

            # If no certificates configured, pass True to enable SSL
            params["ssl"] = ssl_config if ssl_config else True

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
            "charset": self.charset,
            "ssl_ca": self.ssl_ca,
            "ssl_cert": self.ssl_cert,
            "ssl_key": self.ssl_key,
        }
