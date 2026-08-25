from sqlalchemy import text
from app.db.base import Base, engine
import app.models  # noqa: F401  — registers all models with SQLAlchemy


def recreate_tables():
    """Drop and recreate all database tables."""
    print("Dropping all existing database tables with CASCADE...")
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # Query all user tables in public schema
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
            ))
            tables = [row[0] for row in result]
            for table in tables:
                print(f"Dropping table {table} CASCADE...")
                conn.execute(text(f"DROP TABLE IF EXISTS \"{table}\" CASCADE;"))
            trans.commit()
            print("All tables dropped successfully.")
        except Exception as e:
            trans.rollback()
            print(f"Error during dropping tables: {e}")
            raise e

    print("Recreating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables recreated successfully!")


if __name__ == "__main__":
    recreate_tables()

