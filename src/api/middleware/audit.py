from __future__ import annotations

import time
import hashlib

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs every API call with timing and request metadata (no PII)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()

        # Hash the path + query to avoid logging PII
        request_hash = hashlib.sha256(
            f"{request.method}{request.url.path}{request.url.query}".encode()
        ).hexdigest()[:16]

        response = await call_next(request)

        latency_ms = int((time.time() - start) * 1000)

        logger.info(
            "api_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=latency_ms,
            request_hash=request_hash,
        )

        return response
