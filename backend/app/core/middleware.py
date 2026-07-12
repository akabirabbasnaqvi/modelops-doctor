import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


request_logger = logging.getLogger("modelops.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add request IDs, timing, and structured request logs."""

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid4()),
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000

            request_logger.exception(
                "Unhandled request exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = f"{duration_ms:.2f}"

        request_logger.info(
            "HTTP request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return response
