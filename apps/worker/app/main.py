"""
ParlayGalaxy Worker - FastAPI Application
Main entry point for the background worker and internal API.
"""

from contextlib import asynccontextmanager
from typing import Optional

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routes import galaxy_api, jobs, test_player_props
from app.scheduler_v2 import start_scheduler, stop_scheduler

# Rate limiter — keyed by client IP
limiter = Limiter(key_func=get_remote_address)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup/shutdown events"""
    logger.info("worker_starting", version=settings.APP_VERSION)

    # Start background scheduler (loads fixtures every 12h, predictions every 6h)
    logger.info("starting_background_scheduler")
    start_scheduler()
    logger.info("scheduler_ready")

    # Run initial data load on startup to populate fresh fixtures
    import asyncio

    from app.scheduler_v2 import job_generate_predictions_sync, job_load_fixtures_sync

    logger.info("running_startup_data_load")
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, job_load_fixtures_sync)

    yield

    # Shutdown logic
    logger.info("worker_shutting_down")
    stop_scheduler()


# Initialize FastAPI app
app = FastAPI(
    title="ParlayGalaxy Worker",
    description="Background jobs and ML prediction service",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(jobs.router)
app.include_router(galaxy_api.router)
app.include_router(test_player_props.router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "service": "ParlayGalaxy Worker",
        "status": "operational",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "checks": {
            "database": "pending",
            "cache": "pending",
            "api_football": "pending",
        },
    }


@app.get("/test-db")
def test_db():
    """Test database connection"""
    try:
        from app.services.database import db_service

        leagues = db_service.get_active_leagues()
        return {"status": "ok", "leagues_count": len(leagues), "leagues": leagues}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# Authentication dependency
async def verify_worker_secret(x_worker_secret: Optional[str] = Header(None)):
    """Verify worker secret for protected endpoints"""
    if x_worker_secret != settings.WORKER_SECRET:
        logger.warning("unauthorized_worker_access_attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "ParlayGalaxy Worker",
        "status": "operational",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    # TODO: Check Redis, Supabase, API-Football connections
    return {
        "status": "healthy",
        "checks": {
            "database": "ok",
            "cache": "ok",
            "api_football": "ok",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
