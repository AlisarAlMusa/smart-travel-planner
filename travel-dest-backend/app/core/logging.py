"""Structured JSON logging with basic secret redaction."""

import json
import logging
from datetime import datetime, timezone
from typing import Any


SENSITIVE_KEYS = ("api_key", "authorization", "password", "secret", "token", "jwt")


def _redact_value(key: str, value: Any) -> Any:
    """Redact sensitive values before they reach logs."""
    if any(secret_key in key.lower() for secret_key in SENSITIVE_KEYS):
        return "***REDACTED***"
    return value


class JsonFormatter(logging.Formatter):
    """Format log records as JSON objects for easier debugging and tracing."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize one log record into a JSON log line."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "args",
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
                "thread",
                "threadName",
            }:
                continue
            payload[key] = _redact_value(key, value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger once for the whole backend."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        for handler in root_logger.handlers:
            handler.setFormatter(JsonFormatter())
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger after ensuring JSON formatting is active."""
    configure_logging()
    return logging.getLogger(name)

