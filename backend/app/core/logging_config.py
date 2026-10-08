import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

# Context variables for correlation IDs across async task contexts
ctx_request_id: ContextVar[Optional[str]] = ContextVar("ctx_request_id", default=None)
ctx_tenant_id: ContextVar[Optional[str]] = ContextVar("ctx_tenant_id", default=None)


def set_request_context(request_id: Optional[str] = None, tenant_id: Optional[str] = None):
    """Sets request correlation context."""
    if request_id:
        ctx_request_id.set(request_id)
    if tenant_id:
        ctx_tenant_id.set(tenant_id)


def clear_request_context():
    """Clears request correlation context."""
    ctx_request_id.set(None)
    ctx_tenant_id.set(None)


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured JSON lines with correlation IDs and telemetry."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }

        # Inject context variables
        req_id = ctx_request_id.get()
        if req_id:
            log_obj["request_id"] = req_id

        tenant = ctx_tenant_id.get()
        if tenant:
            log_obj["tenant_id"] = tenant

        # Inject extra attributes passed in log calls
        for attr in ["path", "method", "status_code", "duration_ms", "client_ip", "user_agent", "error_code"]:
            if hasattr(record, attr):
                log_obj[attr] = getattr(record, attr)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


class StandardConsoleFormatter(logging.Formatter):
    """Human-readable console formatter for local interactive development."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = ctx_request_id.get()
        req_prefix = f"[{req_id[:8]}] " if req_id else ""
        base = f"{datetime.fromtimestamp(record.created).strftime('%H:%M:%S')} | {record.levelname:<7} | {req_prefix}{record.name}: {record.getMessage()}"
        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"
        return base


def setup_logging(log_level: str = "INFO", structured: bool = True):
    """Initializes root and application logging handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if structured:
        handler.setFormatter(StructuredJSONFormatter())
    else:
        handler.setFormatter(StandardConsoleFormatter())

    root_logger.addHandler(handler)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Returns a named logger instance."""
    return logging.getLogger(name)
