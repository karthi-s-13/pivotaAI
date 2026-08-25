"""
Tests for URI connection string parser and protocol restriction.

Validates parsing of supported database URIs (PostgreSQL, MySQL, MongoDB,
SQL Server) and rejection of blocked protocols (file, http, ftp, etc.).
"""

import pytest

from app.core.uri_parser import parse_connection_string


class TestURIParser:
    """Tests for parse_connection_string()."""

    def test_postgresql_uri(self):
        uri = "postgresql://myuser:mypassword@db.host.name:5432/my_database?sslmode=require&connect_timeout=15"
        parsed = parse_connection_string(uri)

        assert parsed["provider"] == "postgresql"
        assert parsed["username"] == "myuser"
        assert parsed["password"] == "mypassword"
        assert parsed["host"] == "db.host.name"
        assert parsed["port"] == 5432
        assert parsed["database_name"] == "my_database"
        assert parsed["provider_config"] == {"sslmode": "require", "connect_timeout": "15"}

    def test_mongodb_srv_uri(self):
        uri = "mongodb+srv://atlas_user:atlas_pass@cluster.mongodb.net/test_db?replicaSet=myReplica&authSource=admin"
        parsed = parse_connection_string(uri)

        assert parsed["provider"] == "mongodb"
        assert parsed["username"] == "atlas_user"
        assert parsed["password"] == "atlas_pass"
        assert parsed["host"] == "cluster.mongodb.net"
        assert parsed["port"] is None
        assert parsed["database_name"] == "test_db"
        assert parsed["provider_config"] == {
            "replica_set": "myReplica",
            "auth_source": "admin",
            "deployment": "atlas",
        }

    def test_driver_specific_schemes_allowed(self):
        """Composite schemes like postgresql+psycopg2 should be accepted."""
        parsed = parse_connection_string("postgresql+psycopg2://user:pass@localhost:5432/db")
        assert parsed["provider"] == "postgresql"

        parsed = parse_connection_string("mysql+pymysql://user:pass@localhost:3306/db")
        assert parsed["provider"] == "mysql"

    def test_empty_uri_rejected(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            parse_connection_string("")

    @pytest.mark.parametrize("uri", [
        "file:///etc/passwd",
        "ftp://example.com/db",
        "gopher://example.com",
        "http://example.com/db",
        "https://example.com/db",
        "sqlite:///local.db",
        "oracle://example.com",
        "http+postgres://example.com/db",
    ])
    def test_blocked_protocols_rejected(self, uri):
        """Non-database protocols must be rejected with ValueError."""
        with pytest.raises(ValueError, match="Unsupported database scheme"):
            parse_connection_string(uri)


class TestCapabilitiesRegistry:
    """Tests for provider capabilities registry."""

    def test_supported_providers_include_core_dbs(self):
        from app.adapters.registry import get_supported_providers

        providers = get_supported_providers()
        assert "postgresql" in providers
        assert "mysql" in providers
        assert "mongodb" in providers

    def test_postgresql_capabilities(self):
        from app.adapters.registry import get_provider_capabilities

        caps = get_provider_capabilities("postgresql")
        assert caps["sql"] is True
        assert caps["schemas"] is True
        assert caps["relationships"] == "full"

    def test_mongodb_capabilities(self):
        from app.adapters.registry import get_provider_capabilities

        caps = get_provider_capabilities("mongodb")
        assert caps["sql"] is False
        assert caps["schemas"] is False
        assert caps["relationships"] == "inferred"


class TestAdapterValidation:
    """Tests for adapter config validation error handling."""

    def test_postgresql_empty_host_rejected(self):
        from app.adapters.registry import get_adapter

        with pytest.raises(ValueError):
            get_adapter("postgresql", {"host": ""})

    def test_mysql_empty_host_rejected(self):
        from app.adapters.registry import get_adapter

        with pytest.raises(ValueError):
            get_adapter("mysql", {"host": ""})

    def test_mongodb_empty_host_and_string_rejected(self):
        from app.adapters.registry import get_adapter

        with pytest.raises(ValueError):
            get_adapter("mongodb", {"host": "", "connection_string": ""})
