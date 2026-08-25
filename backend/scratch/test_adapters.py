"""
Verification Script for Pivota Foundational Abstraction Layer Refinements.

Tests connection string parsing, capabilities, config validation, CRUD, Secret Manager rotation, and staged connection test diagnostics.
"""

import os
import sys

# Add backend directory to python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.adapters.registry import (
    get_adapter,
    get_provider_capabilities,
    get_supported_providers,
)
from app.db.base import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.secret import Secret
from app.models.data_source import DataSource
from app.schemas.data_source import (
    ConnectionTestRequest,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
)
from app.services import data_source_service, secret_manager


def test_uri_parser():
    print("\n--- Testing Connection String URI Parser ---")
    from app.core.uri_parser import parse_connection_string

    pg_uri = "postgresql://myuser:mypassword@db.host.name:5432/my_database?sslmode=require&connect_timeout=15"
    parsed = parse_connection_string(pg_uri)
    print(f"Parsed PostgreSQL URI: {parsed}")
    assert parsed["provider"] == "postgresql"
    assert parsed["username"] == "myuser"
    assert parsed["password"] == "mypassword"
    assert parsed["host"] == "db.host.name"
    assert parsed["port"] == 5432
    assert parsed["database_name"] == "my_database"
    assert parsed["provider_config"] == {"sslmode": "require", "connect_timeout": "15"}

    mongo_uri = "mongodb+srv://atlas_user:atlas_pass@cluster.mongodb.net/test_db?replicaSet=myReplica&authSource=admin"
    parsed_mongo = parse_connection_string(mongo_uri)
    print(f"Parsed MongoDB URI: {parsed_mongo}")
    assert parsed_mongo["provider"] == "mongodb"
    assert parsed_mongo["username"] == "atlas_user"
    assert parsed_mongo["password"] == "atlas_pass"
    assert parsed_mongo["host"] == "cluster.mongodb.net"
    assert parsed_mongo["port"] is None
    assert parsed_mongo["database_name"] == "test_db"
    assert parsed_mongo["provider_config"] == {"replica_set": "myReplica", "auth_source": "admin", "deployment": "atlas"}

    # Test allowed driver-specific schemes (nested/composite schemes)
    pg_driver_uri = "postgresql+psycopg2://myuser:mypass@localhost:5432/db"
    parsed_pg_driver = parse_connection_string(pg_driver_uri)
    assert parsed_pg_driver["provider"] == "postgresql"

    mysql_driver_uri = "mysql+pymysql://myuser:mypass@localhost:3306/db"
    parsed_mysql_driver = parse_connection_string(mysql_driver_uri)
    assert parsed_mysql_driver["provider"] == "mysql"

    # Test blocked protocols
    blocked_uris = [
        "file:///etc/passwd",
        "ftp://example.com/db",
        "gopher://example.com",
        "http://example.com/db",
        "https://example.com/db",
        "sqlite:///local.db",
        "oracle://example.com",
        "http+postgres://example.com/db",
    ]

    for uri in blocked_uris:
        try:
            parse_connection_string(uri)
            assert False, f"Expected ValueError for blocked URI: {uri}"
        except ValueError as e:
            print(f"Correctly rejected blocked URI '{uri}': {e}")

    print("Connection string URI parser verified successfully!")


def test_capabilities_registry():
    print("\n--- Testing Capability Registry ---")
    providers = get_supported_providers()
    print(f"Supported providers: {providers}")
    assert "postgresql" in providers
    assert "mysql" in providers
    assert "mongodb" in providers

    pg_caps = get_provider_capabilities("postgresql")
    assert pg_caps["sql"] is True
    assert pg_caps["schemas"] is True
    assert pg_caps["relationships"] == "full"

    mongo_caps = get_provider_capabilities("mongodb")
    assert mongo_caps["sql"] is False
    assert mongo_caps["schemas"] is False
    assert mongo_caps["relationships"] == "inferred"
    print("Capability registry verified successfully!")


def test_adapter_validation():
    print("\n--- Testing Adapter Config Validation ---")
    try:
        get_adapter("postgresql", {"host": ""})
        assert False, "Should have failed validation for PostgreSQL"
    except ValueError as e:
        print(f"Expected validation failure caught (PG): {e}")

    try:
        get_adapter("mysql", {"host": ""})
        assert False, "Should have failed validation for MySQL"
    except ValueError as e:
        print(f"Expected validation failure caught (MySQL): {e}")

    try:
        get_adapter("mongodb", {"host": "", "connection_string": ""})
        assert False, "Should have failed validation for MongoDB"
    except ValueError as e:
        print(f"Expected validation failure caught (MongoDB): {e}")

    print("Adapter config validation verified successfully!")


def test_staged_diagnostics():
    print("\n--- Testing Staged Connection Diagnostics ---")
    # Test connection test with deliberate wrong port to trigger failure at specific stage
    request = ConnectionTestRequest(
        provider="postgresql",
        host="localhost",
        port=9999,  # Non-existent port
        database_name="pivota",
        username="postgres",
        password="password",
        ssl_enabled=False,
    )
    result = data_source_service.test_connection_unsaved(request)
    print(f"Test Connection Result Success: {result.success}")
    print("Connection Test Steps Output:")
    for step in result.steps:
        print(f" - Step: {step.name} | Status: {step.status} | Msg: {step.message}")

    assert len(result.steps) == 7
    assert result.steps[0].name == "configuration"
    assert result.steps[0].status == "success"
    assert result.steps[1].name == "dns"
    assert result.steps[1].status == "success"
    assert result.steps[2].name == "network"
    assert result.steps[2].status == "failed"
    assert result.steps[3].name == "tls"
    assert result.steps[3].status == "skipped"
    print("Staged connection diagnostics verified successfully!")


def test_crud_and_secret_rotation():
    print("\n--- Testing CRUD, Connection URI Creation & Secret Rotation ---")
    db = SessionLocal()
    try:
        # Create a test organization
        org = db.query(Organization).filter(Organization.slug == "test-org-refinement").first()
        if not org:
            org = Organization(name="Test Org", slug="test-org-refinement")
            db.add(org)
            db.commit()
            db.refresh(org)

        # Create a test user
        user = db.query(User).filter(User.email == "test-refine@pivota.ai").first()
        if not user:
            user = User(
                email="test-refine@pivota.ai",
                hashed_password="mockhashedpassword",
                full_name="Test User Refined",
                role="admin",
                organization_id=org.id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Register a DataSource using raw connection URI string
        create_payload = DataSourceCreate(
            identity={
                "name": "Local PostgreSQL DS via URI",
                "provider": "postgresql",
                "environment": "development",
            },
            connectivity={
                "connection_mode": "direct",
                "network_mode": "public",
            },
            security={
                "auth_method": "password",
                "tls": False,
            },
            connection_string="postgresql://postgres:karthikeyan%4013@localhost:5432/pivota",
            description="PostgreSQL DataSource parsed from URI",
        )

        response = data_source_service.create_data_source(db, create_payload, user)
        print(f"DataSource successfully created with ID: {response.identity.id}")
        assert response.identity.name == "Local PostgreSQL DS via URI"
        assert response.identity.provider == "postgresql"
        # Connection string should be parsed and raw credentials not stored
        db_record = db.query(DataSource).filter(DataSource.id == response.identity.id).first()
        assert db_record is not None
        assert db_record.host == "localhost"
        assert db_record.port == 5432
        assert db_record.provider_config["database_name"] == "pivota"
        assert db_record.secret_reference is not None
        assert db_record.secret_reference.startswith("secret:")
        print("URI connection string registration and database parsing verified!")

        # Verify password resolved correctly
        resolved_pw = secret_manager.retrieve_secret(db, db_record.secret_reference)
        assert resolved_pw == "karthikeyan@13"
        print("Password extraction from connection string verified!")

        # Test Secret Manager key rotation
        print("Rotating credentials...")
        rot_res = secret_manager.rotate_secrets(db)
        print(f"Rotation result: {rot_res}")
        assert rot_res["status"] == "success"
        assert rot_res["rotated_count"] >= 1
        assert rot_res["failed_count"] == 0

        # Verify credential still accessible post-rotation
        resolved_pw_post = secret_manager.retrieve_secret(db, db_record.secret_reference)
        assert resolved_pw_post == "karthikeyan@13"
        print("Credential rotation verified successfully!")

        # Update datasource using a connection string update
        update_payload = DataSourceUpdate(
            connection_string="postgresql://postgres:karthikeyan%4013@localhost:5433/pivota_updated",
        )
        updated = data_source_service.update_data_source(
            db, response.identity.id, update_payload, org.id
        )
        try:
            assert updated.connectivity.port == 5433
            assert updated.connectivity.provider_config["database_name"] == "pivota_updated"
        except AssertionError as e:
            print(f"DEBUG: updated.connectivity.port={updated.connectivity.port}")
            print(f"DEBUG: updated.connectivity.provider_config={updated.connectivity.provider_config}")
            raise e
        print("Connection string update verified successfully!")

        # Clean up
        secret_ref_to_delete = db_record.secret_reference
        data_source_service.delete_data_source(db, response.identity.id, org.id)

        # Check secret was purged
        purged_secret = db.query(Secret).filter(Secret.id == secret_ref_to_delete.split(":")[1]).first()
        assert purged_secret is None
        print("DataSource deletion and secret store purge verified successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    try:
        test_uri_parser()
        test_capabilities_registry()
        test_adapter_validation()
        test_staged_diagnostics()
        test_crud_and_secret_rotation()
        print("\n==============================================")
        print("ALL REFINEMENT VERIFICATION TESTS PASSED!")
        print("==============================================")
    except AssertionError as e:
        print(f"\nAssertion error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error occurred: {e}")
        sys.exit(1)
