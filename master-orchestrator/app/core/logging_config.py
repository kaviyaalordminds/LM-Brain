import json
import logging
import datetime
from typing import Any, Dict

REDACT_KEYS = {"api_key", "authorization", "password", "token", "secret", "bearer"}

class StructuredJsonFormatter(logging.Formatter):
    """Formats logs as JSON with secret redaction and execution context."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom context attributes if present
        for attr in ("execution_id", "step_id", "task_id", "attempt_id", "correlation_id", "specialist_id"):
            val = getattr(record, attr, None)
            if val:
                log_obj[attr] = val

        # Secret redaction
        for k in list(log_obj.keys()):
            if any(red in k.lower() for red in REDACT_KEYS):
                log_obj[k] = "[REDACTED]"

        return json.dumps(log_obj)

def configure_structured_logging(level: str = "INFO"):
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Replace existing handlers
    root_logger.handlers = [handler]
