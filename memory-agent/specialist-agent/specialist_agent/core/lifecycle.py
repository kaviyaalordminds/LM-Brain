"""
Specialist Agent — Lifecycle State Machine

Defines all valid lifecycle states and the permitted transitions between them.

Valid lifecycle:

  READY → SPAWNED → ASSIGNED → RUNNING → VERIFYING → COMPLETED → TERMINATED

Failure path:

  RUNNING → VERIFYING → FAILED → REFLECTING → RETRYING → RUNNING
                                    ↓ (after max retries)
                                  TERMINATED

The state machine rejects any transition not in the allowed set.
Every transition emits a lifecycle event.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Callable

from specialist_agent.core.errors import InvalidTransitionError

logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """All valid lifecycle states for a Specialist Agent."""

    READY = "READY"
    SPAWNED = "SPAWNED"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"
    REFLECTING = "REFLECTING"
    RETRYING = "RETRYING"
    CANCELLED = "CANCELLED"


# ─────────────────────────────────────────────────────────────────────────────
# Permitted transitions
# ─────────────────────────────────────────────────────────────────────────────

_ALLOWED_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.READY: {AgentState.SPAWNED},
    AgentState.SPAWNED: {AgentState.ASSIGNED, AgentState.CANCELLED},
    AgentState.ASSIGNED: {AgentState.RUNNING, AgentState.CANCELLED},
    AgentState.RUNNING: {AgentState.VERIFYING, AgentState.FAILED, AgentState.CANCELLED},
    AgentState.VERIFYING: {AgentState.COMPLETED, AgentState.FAILED},
    AgentState.COMPLETED: {AgentState.TERMINATED},
    AgentState.FAILED: {AgentState.REFLECTING, AgentState.TERMINATED},
    AgentState.REFLECTING: {AgentState.RETRYING, AgentState.TERMINATED},
    AgentState.RETRYING: {AgentState.RUNNING},
    AgentState.TERMINATED: set(),   # Terminal state — no exits
    AgentState.CANCELLED: {AgentState.TERMINATED},
}


class AgentLifecycle:
    """
    Manages state transitions for a single agent instance.

    - Validates every transition before applying it.
    - Invokes observer callbacks so callers can track state changes.
    - Never exposes mutable internal state directly.
    """

    def __init__(
        self,
        agent_id: str,
        on_transition: Callable[[str, AgentState, AgentState], None] | None = None,
    ) -> None:
        self._agent_id = agent_id
        self._state = AgentState.READY
        self._history: list[AgentState] = [AgentState.READY]
        self._on_transition = on_transition

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> AgentState:
        """Current lifecycle state (read-only)."""
        return self._state

    @property
    def history(self) -> list[AgentState]:
        """Ordered list of all states the agent has passed through."""
        return list(self._history)

    def can_transition(self, to_state: AgentState) -> bool:
        """Return True if moving to *to_state* from the current state is allowed."""
        return to_state in _ALLOWED_TRANSITIONS.get(self._state, set())

    def transition(self, to_state: AgentState) -> None:
        """
        Move to *to_state*.

        Raises InvalidTransitionError if the transition is not permitted.
        Calls the observer callback (if provided) after the transition.
        """
        if not self.can_transition(to_state):
            raise InvalidTransitionError(
                from_state=self._state.value,
                to_state=to_state.value,
                agent_id=self._agent_id,
            )

        previous = self._state
        self._state = to_state
        self._history.append(to_state)

        logger.debug(
            "agent.lifecycle.transition",
            extra={
                "agent_id": self._agent_id,
                "from": previous.value,
                "to": to_state.value,
            },
        )

        if self._on_transition:
            try:
                self._on_transition(self._agent_id, previous, to_state)
            except Exception:  # noqa: BLE001
                logger.warning(
                    "agent.lifecycle.observer_error",
                    extra={"agent_id": self._agent_id},
                    exc_info=True,
                )

    def is_terminal(self) -> bool:
        """Return True if the agent is in a terminal state."""
        return self._state in {AgentState.TERMINATED, AgentState.CANCELLED}

    def is_active(self) -> bool:
        """Return True if the agent is capable of doing work."""
        return self._state in {
            AgentState.SPAWNED,
            AgentState.ASSIGNED,
            AgentState.RUNNING,
            AgentState.VERIFYING,
            AgentState.REFLECTING,
            AgentState.RETRYING,
        }

    def __repr__(self) -> str:
        return f"AgentLifecycle(agent_id={self._agent_id!r}, state={self._state.value})"
