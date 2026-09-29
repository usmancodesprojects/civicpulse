import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
REQUEST_COUNT = Counter(
    "civicpulse_http_requests_total", "HTTP requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "civicpulse_http_request_duration_seconds", "HTTP request latency", ["path"]
)
TRIAGE_LATENCY = Histogram("civicpulse_triage_duration_seconds", "Triage latency", ["provider"])
TRIAGE_FALLBACKS = Counter("civicpulse_triage_fallback_total", "Triage fallbacks", ["provider"])


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        for key in ("complaint_id", "provider", "error_class"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_context.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - started
            REQUEST_COUNT.labels(request.method, request.url.path, 500).inc()
            REQUEST_LATENCY.labels(request.url.path).observe(elapsed)
            request_id_context.reset(token)
            raise
        elapsed = time.perf_counter() - started
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
        REQUEST_LATENCY.labels(path).observe(elapsed)
        response.headers["X-Request-ID"] = request_id
        request_id_context.reset(token)
        return response
