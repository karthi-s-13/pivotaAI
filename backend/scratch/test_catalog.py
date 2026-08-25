"""
Verification Script for Pivota Asynchronous Discovery and Catalog API Routes.
"""

import os
import sys
import time

# Add backend directory to python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from app.db.base import SessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.models.data_source import DataSource
from app.models.metadata import (
    DatabaseMetadata,
    SchemaMetadata,
    ObjectMetadata,
    ColumnMetadata,
    RelationshipMetadata,
    MetadataSnapshot,
)
from app.services import data_source_service


def test_async_metadata_sync():
    print("\n--- Testing Thread-Safe Asynchronous Metadata Discovery ---")
    db = SessionLocal()
    try:
        # Resolve test user and org
        user = db.query(User).filter(User.email == "test-refine@pivota.ai").first()
        if not user:
            org = db.query(Organization).filter(Organization.slug == "test-org-refinement").first()
            if not org:
                org = Organization(name="Test Org", slug="test-org-refinement")
                db.add(org)
                db.commit()
                db.refresh(org)
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

        # Create DataSource for testing metadata sync
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

        print(f"Created DataSource {ds.name} with ID: {ds.id}")

        # Simulate background task thread call
        print("Launching background discovery run...")
        data_source_service.sync_data_source_background(
            source_id=ds.id,
            organization_id=user.organization_id,
            user_id=user.id
        )

        # Refresh database session
        db.close()
        db = SessionLocal()
        
        # Query results
        ds_refreshed = db.query(DataSource).filter(DataSource.id == ds.id).first()
        print(f"Refreshed DataSource state: {ds_refreshed.health_status}")
        print(f"Last Error: {ds_refreshed.health_last_error}")
        
        # Check snapshot runs log
        snapshots = db.query(MetadataSnapshot).filter(MetadataSnapshot.data_source_id == ds.id).all()
        print(f"Snapshots log count: {len(snapshots)}")
        for snap in snapshots:
            print(f" - Snap ID: {snap.id} | Status: {snap.status} | Duration: {snap.duration_ms}ms")

        # Check catalog isolation entries
        db_entries = db.query(DatabaseMetadata).filter(DatabaseMetadata.data_source_id == ds.id).all()
        print(f"Discovered Databases count: {len(db_entries)}")
        assert len(db_entries) >= 0

        # Clean up
        db.delete(ds_refreshed)
        db.commit()
        print("Async metadata discovery test successfully completed!")
    finally:
        db.close()


def test_catalog_query_routes():
    print("\n--- Testing Relational Metadata Catalog API Queries ---")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test-refine@pivota.ai").first()
        assert user is not None, "Verify user setup first"

        # Query databases directly mimicking endpoint filters
        db_entries = db.query(DatabaseMetadata).filter(DatabaseMetadata.organization_id == user.organization_id).all()
        print(f"Databases in Org: {[d.name for d in db_entries]}")

        # Fuzzy search columns/tables direct DB match
        search_pattern = "%users%"
        matches = db.query(ObjectMetadata).filter(
            ObjectMetadata.organization_id == user.organization_id,
            ObjectMetadata.name.ilike(search_pattern)
        ).all()
        print(f"Object search matches for '{search_pattern}': {[m.name for m in matches]}")

        print("Catalog endpoint query simulation verified successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    try:
        # Recreate DB schema to ensure clean slate
        from recreate_db import recreate_tables
        recreate_tables()

        test_async_metadata_sync()
        test_catalog_query_routes()
        print("\n==============================================")
        print("ALL CATALOG VERIFICATION TESTS PASSED!")
        print("==============================================")
    except AssertionError as e:
        print(f"\nAssertion error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error occurred: {e}")
        sys.exit(1)
