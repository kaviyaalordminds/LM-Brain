"""
Specialist Agent — Event Contract

Every important lifecycle event produces a typed AgentEvent.
Events are observable and will later connect to the global Activity feed.

Consumers (e.g. future Master Orchestrator, monitoring dashboard)
can subscribe to an event stream without knowing agent internals.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All observable lifecycle events."""

    # Lifecycle
    AGENT_SPAWNED = "AGENT_SPAWNED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    AGENT_RUNNING = "AGENT_RUNNING"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    REFLECTION_STARTED = "REFLECTION_STARTED"
    RETRY_STARTED = "RETRY_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    AGENT_TERMINATED = "AGENT_TERMINATED"
    AGENT_CANCELLED = "AGENT_CANCELLED"
    AGENT_ERROR = "AGENT_ERROR"

    # Tool events
    TOOL_REQUESTED = "TOOL_REQUESTED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    TOOL_DENIED = "TOOL_DENIED"
    TOOL_ERROR = "TOOL_ERROR"

    # Memory events
    MEMORY_REQUESTED = "MEMORY_REQUESTED"
    MEMORY_RETURNED = "MEMORY_RETURNED"
    MEMORY_NOT_FOUND = "MEMORY_NOT_FOUND"
    MEMORY_UNVERIFIED = "MEMORY_UNVERIFIED"

    # Model events
    MODEL_RESOLVED = "MODEL_RESOLVED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"

    # Permission events
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # Context trust events
    CONTEXT_TRUST_ESCALATION_BLOCKED = "CONTEXT_TRUST_ESCALATION_BLOCKED"


class AgentEvent(BaseModel):
    """
    Immutable event produced at each significant lifecycle moment.

    Fields
    ------
    event_id   : Unique event identifier.
    event_type : Enum value identifying the event category.
    agent_id   : Agent that produced the event.
    task_id    : Correlated task (if applicable).
    timestamp  : UTC event time.
    message    : Human-readable description.
    metadata   : Arbitrary key/value pairs for detailed context.
    """

    model_config = {"populate_by_name": True}

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    agent_id: str
    task_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: EventType,
        agent_id: str,
        task_id: str | None = None,
        message: str = "",
        **metadata: Any,
    ) -> "AgentEvent":
        """Factory for concise event creation."""
        return cls(
            event_type=event_type,
            agent_id=agent_id,
            task_id=task_id,
            message=message,
            metadata=metadata,
        )
