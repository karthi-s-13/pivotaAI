"""
Integration tests for Data Source CRUD, connection string parsing,
and Secret Manager credential rotation.

These tests require a running PostgreSQL database.
"""

from app.db.base import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.secret import Secret
from app.models.data_source import DataSource
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceUpdate,
)
from app.services import data_source_service, secret_manager


class TestDataSourceCRUD:
    """Integration tests for data source lifecycle operations."""

    def _get_or_create_test_user(self, db):
        """Ensure a test org and user exist, return the user."""
        org = db.query(Organization).filter(Organization.slug == "test-org-refinement").first()
        if not org:
            org = Organization(name="Test Org", slug="test-org-refinement")
            db.add(org)
            db.commit()
            db.refresh(org)

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

        return user, org

    def test_create_datasource_from_connection_uri(self):
        """Creating a data source from a URI should parse host, port, db, and store credentials securely."""
        db = SessionLocal()
        try:
            user, org = self._get_or_create_test_user(db)

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

            assert response.identity.name == "Local PostgreSQL DS via URI"
            assert response.identity.provider == "postgresql"

            db_record = db.query(DataSource).filter(DataSource.id == response.identity.id).first()
            assert db_record is not None
            assert db_record.host == "localhost"
            assert db_record.port == 5432
            assert db_record.provider_config["database_name"] == "pivota"
            assert db_record.secret_reference is not None
            assert db_record.secret_reference.startswith("secret:")

            # Verify password resolved correctly
            resolved_pw = secret_manager.retrieve_secret(db, db_record.secret_reference)
            assert resolved_pw == "karthikeyan@13"

            # Clean up
            data_source_service.delete_data_source(db, response.identity.id, org.id)
        finally:
            db.close()

    def test_secret_rotation_preserves_credentials(self):
        """After key rotation, previously stored credentials must still be retrievable."""
        db = SessionLocal()
        try:
            user, org = self._get_or_create_test_user(db)

            create_payload = DataSourceCreate(
                identity={
                    "name": "Rotation Test DS",
                    "provider": "postgresql",
                    "environment": "development",
                },
                connectivity={"connection_mode": "direct", "network_mode": "public"},
                security={"auth_method": "password", "tls": False},
                connection_string="postgresql://postgres:karthikeyan%4013@localhost:5432/pivota",
            )

            response = data_source_service.create_data_source(db, create_payload, user)
            db_record = db.query(DataSource).filter(DataSource.id == response.identity.id).first()

            # Rotate
            rot_res = secret_manager.rotate_secrets(db)
            assert rot_res["status"] == "success"
            assert rot_res["rotated_count"] >= 1
            assert rot_res["failed_count"] == 0

            # Verify credential still accessible after rotation
            resolved_pw = secret_manager.retrieve_secret(db, db_record.secret_reference)
            assert resolved_pw == "karthikeyan@13"

            # Clean up
            data_source_service.delete_data_source(db, response.identity.id, org.id)
        finally:
            db.close()

    def test_update_datasource_via_connection_string(self):
        """Updating a data source with a new connection string should update host/port/db."""
        db = SessionLocal()
        try:
            user, org = self._get_or_create_test_user(db)

            create_payload = DataSourceCreate(
                identity={
                    "name": "Update Test DS",
                    "provider": "postgresql",
                    "environment": "development",
                },
                connectivity={"connection_mode": "direct", "network_mode": "public"},
                security={"auth_method": "password", "tls": False},
                connection_string="postgresql://postgres:karthikeyan%4013@localhost:5432/pivota",
            )

            response = data_source_service.create_data_source(db, create_payload, user)

            update_payload = DataSourceUpdate(
                connection_string="postgresql://postgres:karthikeyan%4013@localhost:5433/pivota_updated",
            )
            updated = data_source_service.update_data_source(
                db, response.identity.id, update_payload, org.id
            )

            assert updated.connectivity.port == 5433
            assert updated.connectivity.provider_config["database_name"] == "pivota_updated"

            # Clean up
            data_source_service.delete_data_source(db, response.identity.id, org.id)
        finally:
            db.close()

    def test_delete_datasource_purges_secret(self):
        """Deleting a data source should also purge the associated secret."""
        db = SessionLocal()
        try:
            user, org = self._get_or_create_test_user(db)

            create_payload = DataSourceCreate(
                identity={
                    "name": "Delete Test DS",
                    "provider": "postgresql",
                    "environment": "development",
                },
                connectivity={"connection_mode": "direct", "network_mode": "public"},
                security={"auth_method": "password", "tls": False},
                connection_string="postgresql://postgres:karthikeyan%4013@localhost:5432/pivota",
            )

            response = data_source_service.create_data_source(db, create_payload, user)
            db_record = db.query(DataSource).filter(DataSource.id == response.identity.id).first()
            secret_ref = db_record.secret_reference

            data_source_service.delete_data_source(db, response.identity.id, org.id)

            purged = db.query(Secret).filter(Secret.id == secret_ref.split(":")[1]).first()
            assert purged is None
        finally:
            db.close()
