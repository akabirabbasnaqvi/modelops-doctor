import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings


STANDARD_LOG_RECORD_ATTRIBUTES = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
}


class JsonFormatter(logging.Formatter):
    """Format application logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in STANDARD_LOG_RECORD_ATTRIBUTES and not key.startswith("_"):
                log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            log_data,
            default=str,
            ensure_ascii=False,
        )


def configure_logging() -> None:
    """Configure root application logging."""

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True
