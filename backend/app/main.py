"""
Pivota Data Navigator — Main Application Entry Point.

Initializes FastAPI, configures CORS, registers routes,
and creates database tables on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.base import Base, engine
from app.api.router import api_router

# Import all models so SQLAlchemy sees them
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    
    # Safely auto-migrate database schema (adding extra provider fields if not present)
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # 1. Migrate metadata_snapshots
            cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='metadata_snapshots';")).fetchall()
            col_names = [c[0] for c in cols]
            if "provider" not in col_names:
                conn.execute(text("ALTER TABLE metadata_snapshots ADD COLUMN provider VARCHAR(50);"))
            if "function_count" not in col_names:
                conn.execute(text("ALTER TABLE metadata_snapshots ADD COLUMN function_count INTEGER DEFAULT 0 NOT NULL;"))
            if "trigger_count" not in col_names:
                conn.execute(text("ALTER TABLE metadata_snapshots ADD COLUMN trigger_count INTEGER DEFAULT 0 NOT NULL;"))
            if "extension_count" not in col_names:
                conn.execute(text("ALTER TABLE metadata_snapshots ADD COLUMN extension_count INTEGER DEFAULT 0 NOT NULL;"))
                
            # 2. Migrate schema_metadata & object_metadata
            for tbl in ["schema_metadata", "object_metadata"]:
                cols = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{tbl}';")).fetchall()
                col_names = [c[0] for c in cols]
                if "provider_metadata" not in col_names:
                    conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN provider_metadata JSONB;"))
            conn.commit()
            print("Database schemas auto-migrated successfully")
    except Exception as emigrate:
        print(f"Auto-migration skipped or failed: {str(emigrate)}")

    print(f"Pivota Backend running in {settings.APP_ENV} mode")
    yield
    # Cleanup on shutdown
    print("Pivota Backend shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered metadata navigation platform — Find where your data lives",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register API Routes ---
app.include_router(api_router)


# --- Request Validation Exception Handler ---
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print("--- VALIDATION ERROR DETECTED ---")
    print("URL:", request.url)
    print("Body:", body.decode("utf-8", errors="ignore"))
    print("Errors:", exc.errors())
    print("---------------------------------")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


# --- Global Exception Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a clean JSON error."""
    # In development, include the error message for debugging
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                }
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


# --- Health Check ---
@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": "0.1.0"}
