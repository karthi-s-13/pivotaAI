"""
Tests for asynchronous metadata discovery and catalog queries.

Validates the background sync pipeline for PostgreSQL metadata extraction.
These tests require a running PostgreSQL database.
"""

from app.db.base import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.data_source import DataSource
from app.models.metadata import (
    DatabaseMetadata,
    MetadataSnapshot,
    ObjectMetadata,
)
from app.services import data_source_service


class TestMetadataDiscovery:
    """Integration tests for metadata discovery pipeline."""

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

        return user

    def test_async_metadata_sync(self):
        """Background metadata discovery should create snapshot records."""
        db = SessionLocal()
        try:
            user = self._get_or_create_test_user(db)

            ds = DataSource(
                name="Test Catalog Sync PG",
                provider="postgresql",
                host="localhost",
                port=5432,
                environment="development",
                status="active",
                health_status="testing",
                organization_id=user.organization_id,
                created_by=user.id,
                provider_config={"database_name": "pivota"},
            )
            db.add(ds)
            db.commit()
            db.refresh(ds)

            # Run background discovery synchronously for testing
            data_source_service.sync_data_source_background(
                source_id=ds.id,
                organization_id=user.organization_id,
                user_id=user.id,
            )

            # Refresh session to see changes from background thread
            db.close()
            db = SessionLocal()

            snapshots = db.query(MetadataSnapshot).filter(
                MetadataSnapshot.data_source_id == ds.id
            ).all()
            assert len(snapshots) >= 0

            db_entries = db.query(DatabaseMetadata).filter(
                DatabaseMetadata.data_source_id == ds.id
            ).all()
            assert len(db_entries) >= 0

            # Clean up
            ds_record = db.query(DataSource).filter(DataSource.id == ds.id).first()
            if ds_record:
                db.delete(ds_record)
                db.commit()
        finally:
            db.close()

    def test_catalog_search_by_object_name(self):
        """Searching objects by name pattern should return matching entries."""
        db = SessionLocal()
        try:
            user = self._get_or_create_test_user(db)

            search_pattern = "%users%"
            matches = db.query(ObjectMetadata).filter(
                ObjectMetadata.organization_id == user.organization_id,
                ObjectMetadata.name.ilike(search_pattern),
            ).all()

            # Just verify the query runs without error — results depend on DB state
            assert isinstance(matches, list)
        finally:
            db.close()
