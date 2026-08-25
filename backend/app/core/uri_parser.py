"""
URI Parser for Database Connection Strings.

Parses database connection URIs (e.g. postgresql://, mysql://, mongodb://) into structured fields.
"""

from typing import Any, Dict
from urllib.parse import parse_qs, unquote, urlparse


def parse_connection_string(uri: str) -> Dict[str, Any]:
    """
    Parse a connection string URI into a structured dict.
    Supports postgresql, mysql, mongodb, and mongodb+srv.

    Args:
        uri: Connection string.

    Returns:
        dict containing:
            provider: "postgresql" | "mysql" | "mongodb"
            host: host string
            port: int port
            database_name: string database name
            username: optional string
            password: optional string
            provider_config: dict of query parameter options
    """
    if not uri:
        raise ValueError("Connection string URI cannot be empty")

    parsed = urlparse(uri)
    scheme = parsed.scheme.lower()
    if not scheme:
        raise ValueError("URI is missing a scheme protocol")

    base_scheme = scheme.split("+")[0]
    ALLOWED_SCHEMES = {
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "mongodb+srv",
        "mssql",
        "sqlserver",
    }

    if base_scheme not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Unsupported database scheme: '{scheme}'. "
            f"Only the following database protocols are allowed: "
            f"{', '.join(sorted(list(ALLOWED_SCHEMES)))}"
        )

    if "postgres" in base_scheme:
        provider = "postgresql"
        default_port = 5432
    elif "mysql" in base_scheme:
        provider = "mysql"
        default_port = 3306
    elif "mongo" in base_scheme:
        provider = "mongodb"
        default_port = 27017
    elif "mssql" in base_scheme or "sqlserver" in base_scheme:
        provider = "sqlserver"
        default_port = 1433
    else:
        raise ValueError(f"Unsupported database scheme: '{scheme}'")

    # Extract auth
    username = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None

    # Extract host and port
    host = parsed.hostname
    port = parsed.port or default_port

    # For mongodb+srv, standard port is not needed, but default is 27017 if none
    if scheme == "mongodb+srv":
        port = None

    # Extract path / database
    database_name = parsed.path.lstrip("/")

    # Extract extra options from query parameters
    query_params = parse_qs(parsed.query)
    provider_config = {}
    for k, v in query_params.items():
        provider_config[k] = v[0] if len(v) == 1 else v

    # Clean up standard MongoDB Atlas options
    if provider == "mongodb":
        # Normalize query params to snake_case connector config keys
        param_map = {
            "replicaSet": "replica_set",
            "authSource": "auth_source",
            "connectTimeoutMS": "connect_timeout_ms",
            "serverSelectionTimeoutMS": "server_selection_timeout_ms",
            "tlsAllowInvalidCertificates": "tls_allow_invalid_certificates",
        }
        for raw_key, normalized_key in param_map.items():
            if raw_key in provider_config:
                provider_config[normalized_key] = provider_config.pop(raw_key)

        # Normalize tls/ssl flags
        if "tls" in provider_config:
            val = provider_config["tls"]
            provider_config["tls"] = val in ("true", True, "1")
        if "ssl" in provider_config:
            val = provider_config.pop("ssl")
            provider_config.setdefault("tls", val in ("true", True, "1"))

        # directConnection flag
        if "directConnection" in provider_config:
            val = provider_config.pop("directConnection")
            provider_config["direct_connection"] = val in ("true", True, "1")

        # Atlas SRV — mark deployment
        if scheme == "mongodb+srv":
            provider_config["deployment"] = "atlas"

    return {
        "provider": provider,
        "host": host,
        "port": port,
        "database_name": database_name,
        "username": username,
        "password": password,
        "provider_config": provider_config,
    }
