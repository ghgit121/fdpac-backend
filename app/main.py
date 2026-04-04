import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.role import Role
from app.routes.auth_routes import router as auth_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.record_routes import router as record_router
from app.routes.user_routes import router as user_router

logger = logging.getLogger(__name__)
APP_STARTED_AT = datetime.now(timezone.utc)
APP_STARTED_PERF = time.perf_counter()


async def seed_roles() -> None:
    """Ensure the three default roles exist. Safe to call multiple times."""
    async with AsyncSessionLocal() as db:
        defaults = {
            "viewer": "Can only view dashboard data",
            "analyst": "Can view records and dashboard insights",
            "admin": "Can manage users and full record CRUD",
        }
        for role_name, description in defaults.items():
            exists_result = await db.execute(select(Role).where(Role.name == role_name))
            if not exists_result.scalar_one_or_none():
                db.add(Role(name=role_name, description=description))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    try:
        await seed_roles()
        logger.info("Default roles seeded successfully.")
    except Exception as exc:
        # Log but don't crash — migrations may have already created them.
        logger.warning("Role seeding skipped (non-fatal): %s", exc)
    yield


async def _database_health_snapshot() -> dict:
    started = time.perf_counter()
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
            roles_result = await db.execute(
                select(func.count(Role.id)).where(Role.name.in_(["viewer", "analyst", "admin"]))
            )
            roles_count = int(roles_result.scalar_one() or 0)

        return {
            "status": "up",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "default_roles_ready": roles_count == 3,
        }
    except Exception as exc:
        logger.warning("Database health probe failed: %s", exc)
        return {
            "status": "down",
            "latency_ms": None,
            "default_roles_ready": False,
            "error": exc.__class__.__name__,
        }


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Normalize CORS origins — auto-prepend https:// if no scheme is present
    def _normalize_origin(o: str) -> str:
        o = o.strip()
        if o and not o.startswith(("http://", "https://", "*")):
            o = f"https://{o}"
        return o

    origins = [_normalize_origin(o) for o in settings.cors_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": str(exc.detail)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": "Invalid input", "errors": exc.errors()},
        )

    @app.exception_handler(SQLAlchemyError)
    async def db_exception_handler(_: Request, exc: SQLAlchemyError):
        logger.exception("Database operation failed", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Database operation failed"},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception):
        logger.exception("Unhandled error", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "Internal server error"},
        )

    # ── Root endpoint ─────────────────────────────────────────────────
    @app.get("/")
    async def root():
        return {
            "success": True,
            "message": "FDPAC Backend API is running",
            "data": {
                "name": settings.app_name,
                "version": "1.0.0",
                "docs": "/docs",
                "health": "/health",
                "api_prefix": settings.api_prefix,
            },
        }

    # ── Health endpoints ──────────────────────────────────────────────
    @app.get("/health")
    async def health_check():
        check_started = time.perf_counter()
        db_health = await _database_health_snapshot()
        success = db_health["status"] == "up"
        return {
            "success": success,
            "message": "ok" if success else "degraded",
            "data": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "app": {
                    "status": "up",
                    "uptime_seconds": round(time.perf_counter() - APP_STARTED_PERF, 2),
                    "started_at": APP_STARTED_AT.isoformat(),
                },
                "database": db_health,
                "healthcheck_latency_ms": round((time.perf_counter() - check_started) * 1000, 2),
            },
        }

    @app.get("/health/liveness")
    async def liveness_check():
        return {
            "success": True,
            "message": "alive",
            "data": {
                "uptime_seconds": round(time.perf_counter() - APP_STARTED_PERF, 2),
            },
        }

    @app.get("/health/readiness")
    async def readiness_check():
        db_health = await _database_health_snapshot()
        ready = db_health["status"] == "up"
        return JSONResponse(
            status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": ready,
                "message": "ready" if ready else "database unavailable",
                "data": {
                    "database": db_health,
                },
            },
        )

    # ── API routers ───────────────────────────────────────────────────
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(user_router, prefix=settings.api_prefix)
    app.include_router(record_router, prefix=settings.api_prefix)
    app.include_router(dashboard_router, prefix=settings.api_prefix)

    return app


app = create_app()
