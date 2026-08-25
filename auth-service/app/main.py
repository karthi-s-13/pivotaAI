"""
Auth Pivota — Main Application Entry Point.

Separate authentication microservice for Pivota 2FA.
Runs on port 8001.
"""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.models import User, OTPRecord  # noqa: F401 — register models
from app.routes.auth import router as auth_router
from app.routes.totp import router as totp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Create OTP records table (User table already exists from Pivota backend)
    Base.metadata.create_all(bind=engine)

    # Auto-migrate: add is_2fa_verified column if not present
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            cols = conn.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name='users';")
            ).fetchall()
            col_names = [c[0] for c in cols]
            if "is_2fa_verified" not in col_names:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN is_2fa_verified BOOLEAN DEFAULT FALSE NOT NULL;")
                )
                conn.commit()
                print("Added is_2fa_verified column to users table")
    except Exception as e:
        print(f"Auto-migration note: {e}")

    print(f"Auth Pivota service running on port 8001")
    yield
    print("Auth Pivota service shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="Pivota Two-Factor Authentication Service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS Middleware ---
try:
    origins = json.loads(settings.CORS_ORIGINS)
except (json.JSONDecodeError, TypeError):
    origins = ["http://localhost:3001", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routes ---
app.include_router(auth_router)
app.include_router(totp_router)


# --- Health Check ---
@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": "0.1.0"}
