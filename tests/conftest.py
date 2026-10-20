from __future__ import annotations

import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set test environment before any imports
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["LITELLM_BASE_URL"] = "http://localhost:4000"
# Settings() refuses empty/default secrets at import time (src/config.py); CI has no .env.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-not-for-production")
os.environ.setdefault("API_SECRET_KEY", "test-only-api-secret-not-for-production")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    from src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
