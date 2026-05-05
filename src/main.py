from __future__ import annotations

import time
from contextlib import asynccontextmanager

import structlog
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from src.config import get_settings
from src.db.session import engine
from src.api.middleware.audit import AuditMiddleware
from src.api.routes import applications, documents, hitl, reports, webhooks
from src.api.routes import offers, config, audit, notifications
from src.api.routes.auth import router as auth_router
from src.api.routes.chat import router as chat_router
from src.api.routes.status import router as status_router
from src.api.routes.admin import router as admin_router
from src.api.models.schemas import HealthResponse, ComponentHealth

logger = structlog.get_logger()
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_loan_underwriting_system", environment=settings.environment)

    # Initialize LangGraph PostgreSQL checkpointer
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from src.graph.checkpointer import set_checkpointer
    db_uri = settings.sync_database_url
    checkpointer_ctx = AsyncPostgresSaver.from_conn_string(db_uri)
    checkpointer = await checkpointer_ctx.__aenter__()
    await checkpointer.setup()
    set_checkpointer(checkpointer)
    logger.info("langgraph_checkpointer_ready")

    # Initialize Redis pool on app.state
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    yield

    # Shutdown
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.aclose()
    set_checkpointer(None)
    await checkpointer_ctx.__aexit__(None, None, None)
    await engine.dispose()
    logger.info("shutdown_complete")


app = FastAPI(
    title="Personal Loan Underwriting API",
    description="AI-powered loan underwriting with LangGraph agent pipeline",
    version="4.0.0",
    lifespan=lifespan,
)

# CORS — must come before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware
app.add_middleware(AuditMiddleware)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Routes
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(applications.router)
app.include_router(documents.router)
app.include_router(hitl.router)
app.include_router(reports.router)
app.include_router(webhooks.router)
app.include_router(offers.router)
app.include_router(config.router)
app.include_router(audit.router)
app.include_router(notifications.router)
app.include_router(status_router)
app.include_router(admin_router)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """System health check with component status."""
    components = {}

    # PostgreSQL
    try:
        start = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        components["db"] = ComponentHealth(status="healthy", latency_ms=round((time.time() - start) * 1000, 2))
    except Exception as e:
        components["db"] = ComponentHealth(status=f"unhealthy: {e}")

    # Redis
    try:
        start = time.time()
        redis_pool = getattr(app.state, "redis", None)
        if redis_pool:
            await redis_pool.ping()
            components["redis"] = ComponentHealth(status="healthy", latency_ms=round((time.time() - start) * 1000, 2))
        else:
            components["redis"] = ComponentHealth(status="unhealthy: pool not initialized")
    except Exception as e:
        components["redis"] = ComponentHealth(status=f"unhealthy: {e}")


    overall = "healthy" if all(c.status == "healthy" for c in components.values()) else "degraded"

    return HealthResponse(status=overall, components=components)
