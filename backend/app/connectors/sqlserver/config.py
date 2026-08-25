"""
SQL Server Connection Configuration.

Parses and normalizes individual parameters and connection URIs
into a single internal canonical configuration object, protecting secrets.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, SecretStr
from app.core.uri_parser import parse_connection_string


class SQLServerConnectionConfig(BaseModel):
    """Canonical configuration representation for SQL Server connector."""

    host: str = "localhost"
    port: int = 1433
    database: str = ""
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    authentication_method: str = "sql_server"  # sql_server, integrated
    encrypt: bool = True
    trust_server_certificate: bool = False
    connect_timeout: int = 15
    driver: str = "SQL Server"
    instance_name: Optional[str] = None
    application_name: Optional[str] = "pivota"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SQLServerConnectionConfig":
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

            # Merge query options (e.g., driver, encrypt, trust_server_certificate)
            p_config = parsed.get("provider_config") or {}
            if "driver" in p_config:
                normalized["driver"] = p_config["driver"]
            if "encrypt" in p_config:
                normalized["encrypt"] = p_config["encrypt"].lower() in ("true", "1", "yes")
            if "trustservercertificate" in p_config:
                normalized["trust_server_certificate"] = p_config["trustservercertificate"].lower() in ("true", "1", "yes")
            if "authentication" in p_config:
                auth = p_config["authentication"].lower()
                if "integrated" in auth or "windows" in auth:
                    normalized["authentication_method"] = "integrated"
            if "connect_timeout" in p_config:
                try:
                    normalized["connect_timeout"] = int(p_config["connect_timeout"])
                except ValueError:
                    pass
            if "appname" in p_config or "application_name" in p_config:
                normalized["application_name"] = p_config.get("appname") or p_config.get("application_name")

        # Map from DB model fields
        if "database_name" in normalized and "database" not in normalized:
            normalized["database"] = normalized["database_name"]

        # If user explicitly chose integrated auth from UI
        if normalized.get("auth_method") == "integrated" or normalized.get("authentication_method") == "integrated":
            normalized["authentication_method"] = "integrated"

        # Map ssl_enabled to encrypt
        if "ssl_enabled" in normalized:
            normalized["encrypt"] = bool(normalized["ssl_enabled"])

        # Safe defaults
        if not normalized.get("port"):
            normalized["port"] = 1433
        if not normalized.get("driver"):
            normalized["driver"] = "SQL Server"

        # Convert password to SecretStr if string
        pw = normalized.get("password")
        if pw is not None and not isinstance(pw, SecretStr):
            if str(pw).strip() == "":
                normalized["password"] = None
            else:
                normalized["password"] = SecretStr(str(pw))

        # Filter fields
        class_fields = cls.__fields__.keys()
        init_data = {k: v for k, v in normalized.items() if k in class_fields}

        return cls(**init_data)

    def to_odbc_connection_string(self) -> str:
        """Convert config into pyodbc connection string."""
        server = self.host
        if self.instance_name:
            server = f"{self.host}\\{self.instance_name}"
        else:
            server = f"{self.host},{self.port}"

        params = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={server}",
        ]

        if self.database:
            params.append(f"DATABASE={self.database}")

        params.append(f"Timeout={self.connect_timeout}")

        # Authentication Method
        if self.authentication_method == "integrated":
            params.append("Trusted_Connection=yes")
        else:
            if self.username:
                params.append(f"UID={self.username}")
            if self.password:
                params.append(f"PWD={self.password.get_secret_value()}")

        # Encryption and TLS Settings
        if self.encrypt:
            params.append("Encrypt=yes")
        else:
            params.append("Encrypt=no")

        if self.trust_server_certificate:
            params.append("TrustServerCertificate=yes")
        else:
            params.append("TrustServerCertificate=no")

        if self.application_name:
            params.append(f"APP={self.application_name}")

        return ";".join(params)

    def get_masked_config(self) -> Dict[str, Any]:
        """Return config with password masked for safe logging or rendering."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": "••••••••" if self.password else None,
            "authentication_method": self.authentication_method,
            "driver": self.driver,
            "encrypt": self.encrypt,
            "trust_server_certificate": self.trust_server_certificate,
            "connect_timeout": self.connect_timeout,
            "instance_name": self.instance_name,
            "application_name": self.application_name,
        }
