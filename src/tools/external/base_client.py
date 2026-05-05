from __future__ import annotations

import time
import hashlib
import enum
from datetime import datetime, timedelta

import httpx
import structlog
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class CircuitState(str, enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CreditDataResponse(BaseModel):
    """Standardized response from any external API client."""
    success: bool
    provider: str
    data: dict
    raw_response: dict | None = None
    latency_ms: int = 0
    error: str | None = None


class CircuitBreaker:
    """Circuit breaker: opens after 5 failures in 5 min, resets after 60s."""

    def __init__(self, failure_threshold: int = 5, window_seconds: int = 300, reset_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.reset_seconds = reset_seconds
        self.state = CircuitState.CLOSED
        self.failures: list[datetime] = []
        self.opened_at: datetime | None = None

    def record_failure(self):
        now = datetime.utcnow()
        self.failures = [f for f in self.failures if f > now - timedelta(seconds=self.window_seconds)]
        self.failures.append(now)
        if len(self.failures) >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = now
            logger.warning("circuit_breaker_opened", failures=len(self.failures))

    def record_success(self):
        self.state = CircuitState.CLOSED
        self.failures.clear()
        self.opened_at = None

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.opened_at and datetime.utcnow() > self.opened_at + timedelta(seconds=self.reset_seconds):
                self.state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker_half_open")
                return True
            return False
        # HALF_OPEN: allow one test request
        return True


class BaseExternalClient:
    """Base class for all external API clients with circuit breaker and retry."""

    provider_name: str = "unknown"

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
    ) -> httpx.Response:
        if not self.circuit_breaker.can_execute():
            raise ConnectionError(f"Circuit breaker OPEN for {self.provider_name}")

        try:
            response = await self.client.request(method, url, headers=headers, json=json, data=data)
            response.raise_for_status()
            self.circuit_breaker.record_success()
            return response
        except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code < 500:
                raise  # Don't circuit-break on client errors
            self.circuit_breaker.record_failure()
            raise

    async def execute(self, **kwargs) -> CreditDataResponse:
        """Override in subclasses. Wraps the API call with timing and audit logging."""
        start = time.time()
        try:
            result = await self._call_api(**kwargs)
            latency = int((time.time() - start) * 1000)
            result.latency_ms = latency
            self._audit_log(kwargs, result, latency)
            return result
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            logger.error("api_call_failed", provider=self.provider_name, error=str(e), latency_ms=latency)
            return CreditDataResponse(
                success=False,
                provider=self.provider_name,
                data={},
                error=str(e),
                latency_ms=latency,
            )

    async def _call_api(self, **kwargs) -> CreditDataResponse:
        raise NotImplementedError

    def _audit_log(self, request_data: dict, response: CreditDataResponse, latency_ms: int):
        request_hash = hashlib.sha256(str(request_data).encode()).hexdigest()[:16]
        logger.info(
            "external_api_call",
            provider=self.provider_name,
            request_hash=request_hash,
            success=response.success,
            latency_ms=latency_ms,
        )

    def _load_mock(self, fixture_name: str) -> dict:
        """Load mock response from fixtures when in development mode."""
        import json
        from pathlib import Path

        fixture_path = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / f"{fixture_name}.json"
        if fixture_path.exists():
            return json.loads(fixture_path.read_text())
        return {"mock": True, "message": f"No fixture found: {fixture_name}"}

    async def close(self):
        await self.client.aclose()
