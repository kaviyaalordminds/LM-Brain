from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

logger = logging.getLogger("ExecutiveTwinsAudit")
logger.setLevel(logging.INFO)


class AuditEvent(BaseModel):
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)


class AuditLogger:
    """
    Structured Audit Logger.
    Logs lifecycle events for full auditability while scrubbing sensitive keys/tokens.
    """

    _events: List[AuditEvent] = []

    @classmethod
    def log_event(cls, event_type: str, payload: Dict[str, Any]) -> AuditEvent:
        # Scrub potential secret keys
        scrubbed = cls._scrub_sensitive_data(payload)
        event = AuditEvent(event_type=event_type, payload=scrubbed)
        cls._events.append(event)
        logger.info(f"[AUDIT] {event_type}: {json.dumps(scrubbed, default=str)}")
        return event

    @classmethod
    def get_events(cls) -> List[AuditEvent]:
        return list(cls._events)

    @classmethod
    def clear_events(cls) -> None:
        cls._events.clear()

    @classmethod
    def _scrub_sensitive_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        scrubbed = {}
        sensitive_keywords = ["key", "secret", "token", "password", "auth", "credential"]
        for k, v in data.items():
            if any(kw in k.lower() for kw in sensitive_keywords):
                scrubbed[k] = "[REDACTED]"
            elif isinstance(v, dict):
                scrubbed[k] = cls._scrub_sensitive_data(v)
            else:
                scrubbed[k] = v
        return scrubbed
