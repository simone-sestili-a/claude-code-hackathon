"""Centralized logging configuration for DocumentAI.

Call configure_logging() once at application startup (in api.py or __main__).
Emits to:
  logs/document_ai.log  — all levels, rotating at 10 MB, 7 backups
  logs/errors.log       — ERROR and above only, rotating at 5 MB, 7 backups
  stderr                — INFO and above (console)

Every log record is annotated with a request_id set by the API middleware.
Use set_request_id() from the request middleware to inject it; parallel asyncio
tasks inherit it automatically (Python copies ContextVar values on task spawn).

Log level is controlled by the LOG_LEVEL env var (default: INFO).
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from contextvars import ContextVar
from pathlib import Path

LOG_DIR = Path("logs")

_LOG_FORMAT = "%(asctime)s [%(levelname)-8s] [%(request_id)-8s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Per-request correlation ID — "-" when outside a request context.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    """Injects the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get()  # type: ignore[attr-defined]
        return True


def set_request_id(rid: str) -> None:
    """Set the request ID for the current async task (call from middleware)."""
    _request_id_var.set(rid)


def get_request_id() -> str:
    return _request_id_var.get()


_configured = False


def configure_logging() -> None:
    """Set up file + console handlers on the root logger.

    Idempotent — safe to call multiple times (no-op after the first call).
    """
    global _configured
    if _configured:
        return
    _configured = True

    LOG_DIR.mkdir(exist_ok=True)

    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    req_filter = _RequestIdFilter()

    # Main rotating log — DEBUG and above
    main_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "document_ai.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    main_handler.setFormatter(fmt)
    main_handler.setLevel(logging.DEBUG)
    main_handler.addFilter(req_filter)

    # Dedicated error log — ERROR and above only
    error_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    error_handler.setFormatter(fmt)
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(req_filter)

    # Console — INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(req_filter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(main_handler)
    root.addHandler(error_handler)
    root.addHandler(console_handler)

    # Suppress noisy third-party loggers at file level too
    for noisy in ("httpx", "httpcore", "uvicorn.access", "anthropic", "fitz"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configured: level=%s, dir=%s", level_name, LOG_DIR.resolve()
    )
