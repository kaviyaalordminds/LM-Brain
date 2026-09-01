"""
Specialist Agent — Custom Error Hierarchy

All errors are specific, structured, and catchable independently.
No generic Exception is ever raised directly from the runtime.
"""

from __future__ import annotations


class AgentError(Exception):
    """Base class for all Specialist Agent errors."""

    def __init__(self, message: str, agent_id: str | None = None, task_id: str | None = None) -> None:
        super().__init__(message)
        self.agent_id = agent_id
        self.task_id = task_id

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.agent_id:
            parts.append(f"agent_id={self.agent_id}")
        if self.task_id:
            parts.append(f"task_id={self.task_id}")
        return " | ".join(parts)


class InvalidTransitionError(AgentError):
    """Raised when a lifecycle state transition is not permitted."""

    def __init__(self, from_state: str, to_state: str, agent_id: str | None = None) -> None:
        super().__init__(
            f"Invalid lifecycle transition: {from_state} → {to_state}",
            agent_id=agent_id,
        )
        self.from_state = from_state
        self.to_state = to_state


class TaskValidationError(AgentError):
    """Raised when a TaskRequest fails validation."""

    def __init__(self, message: str, field: str | None = None, agent_id: str | None = None) -> None:
        super().__init__(message, agent_id=agent_id)
        self.field = field


class ModelUnavailableError(AgentError):
    """Raised when no model provider is configured for the required capability."""

    ERROR_CODE = "MODEL_UNAVAILABLE"

    def __init__(
        self,
        capability: str,
        agent_id: str | None = None,
        task_id: str | None = None,
    ) -> None:
        super().__init__(
            f"No model provider configured for capability: {capability}",
            agent_id=agent_id,
            task_id=task_id,
        )
        self.capability = capability
        self.error_code = self.ERROR_CODE


class ToolNotFoundError(AgentError):
    """Raised when a requested tool is not registered."""

    def __init__(self, tool_name: str, agent_id: str | None = None) -> None:
        super().__init__(
            f"Tool not found in registry: {tool_name}",
            agent_id=agent_id,
        )
        self.tool_name = tool_name


class PermissionDeniedError(AgentError):
    """Raised when an agent lacks permission to use a tool or resource."""

    def __init__(
        self,
        agent_id: str,
        permission: str,
        resource: str | None = None,
    ) -> None:
        resource_str = f" on '{resource}'" if resource else ""
        super().__init__(
            f"Agent '{agent_id}' lacks permission '{permission}'{resource_str}",
            agent_id=agent_id,
        )
        self.permission = permission
        self.resource = resource


class VerificationError(AgentError):
    """Raised when verification itself encounters an internal error (not a FAIL verdict)."""


class RetryLimitExceededError(AgentError):
    """Raised when the maximum retry count is reached."""

    def __init__(self, max_retries: int, agent_id: str | None = None, task_id: str | None = None) -> None:
        super().__init__(
            f"Retry limit of {max_retries} exceeded",
            agent_id=agent_id,
            task_id=task_id,
        )
        self.max_retries = max_retries


class MemoryClientError(AgentError):
    """Raised when the Memory Agent client encounters an error."""
