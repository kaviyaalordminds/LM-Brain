"""
Tests for AgentLifecycle state machine.

Covers:
  - Valid transitions
  - Invalid transitions (must raise InvalidTransitionError)
  - Terminal state detection
  - Active state detection
  - History tracking
  - Observer callback invocation
"""

from __future__ import annotations

import pytest

from specialist_agent.core.errors import InvalidTransitionError
from specialist_agent.core.lifecycle import AgentLifecycle, AgentState


class TestAgentLifecycle:
    """Tests for the AgentLifecycle state machine."""

    def test_initial_state_is_ready(self):
        lc = AgentLifecycle(agent_id="test-agent")
        assert lc.state == AgentState.READY

    def test_history_starts_with_ready(self):
        lc = AgentLifecycle(agent_id="test-agent")
        assert lc.history == [AgentState.READY]

    # ──────────────────────────────────────────────────────────────────
    # Valid transitions
    # ──────────────────────────────────────────────────────────────────

    def test_ready_to_spawned(self):
        lc = AgentLifecycle(agent_id="a")
        lc.transition(AgentState.SPAWNED)
        assert lc.state == AgentState.SPAWNED

    def test_spawned_to_assigned(self):
        lc = AgentLifecycle(agent_id="a")
        lc.transition(AgentState.SPAWNED)
        lc.transition(AgentState.ASSIGNED)
        assert lc.state == AgentState.ASSIGNED

    def test_full_happy_path(self):
        lc = AgentLifecycle(agent_id="a")
        for state in [
            AgentState.SPAWNED,
            AgentState.ASSIGNED,
            AgentState.RUNNING,
            AgentState.VERIFYING,
            AgentState.COMPLETED,
            AgentState.TERMINATED,
        ]:
            lc.transition(state)
        assert lc.state == AgentState.TERMINATED

    def test_failure_path(self):
        lc = AgentLifecycle(agent_id="a")
        for state in [
            AgentState.SPAWNED,
            AgentState.ASSIGNED,
            AgentState.RUNNING,
            AgentState.VERIFYING,
            AgentState.FAILED,
            AgentState.REFLECTING,
            AgentState.RETRYING,
            AgentState.RUNNING,   # Retry loop back to RUNNING
        ]:
            lc.transition(state)
        assert lc.state == AgentState.RUNNING

    def test_cancel_path(self):
        lc = AgentLifecycle(agent_id="a")
        lc.transition(AgentState.SPAWNED)
        lc.transition(AgentState.CANCELLED)
        lc.transition(AgentState.TERMINATED)
        assert lc.state == AgentState.TERMINATED

    # ──────────────────────────────────────────────────────────────────
    # Invalid transitions
    # ──────────────────────────────────────────────────────────────────

    def test_ready_to_complete_is_invalid(self):
        lc = AgentLifecycle(agent_id="a")
        with pytest.raises(InvalidTransitionError) as exc_info:
            lc.transition(AgentState.COMPLETED)
        assert "READY" in str(exc_info.value)
        assert "COMPLETED" in str(exc_info.value)

    def test_ready_to_running_is_invalid(self):
        lc = AgentLifecycle(agent_id="a")
        with pytest.raises(InvalidTransitionError):
            lc.transition(AgentState.RUNNING)

    def test_running_to_terminated_is_invalid(self):
        lc = AgentLifecycle(agent_id="a")
        lc.transition(AgentState.SPAWNED)
        lc.transition(AgentState.ASSIGNED)
        lc.transition(AgentState.RUNNING)
        with pytest.raises(InvalidTransitionError):
            lc.transition(AgentState.TERMINATED)

    def test_terminated_has_no_valid_transitions(self):
        lc = AgentLifecycle(agent_id="a")
        for state in [AgentState.SPAWNED, AgentState.ASSIGNED, AgentState.RUNNING,
                      AgentState.VERIFYING, AgentState.COMPLETED, AgentState.TERMINATED]:
            lc.transition(state)
        with pytest.raises(InvalidTransitionError):
            lc.transition(AgentState.READY)

    def test_completed_to_running_is_invalid(self):
        lc = AgentLifecycle(agent_id="a")
        for state in [AgentState.SPAWNED, AgentState.ASSIGNED, AgentState.RUNNING,
                      AgentState.VERIFYING, AgentState.COMPLETED]:
            lc.transition(state)
        with pytest.raises(InvalidTransitionError):
            lc.transition(AgentState.RUNNING)

    # ──────────────────────────────────────────────────────────────────
    # can_transition
    # ──────────────────────────────────────────────────────────────────

    def test_can_transition_returns_true_for_valid(self):
        lc = AgentLifecycle(agent_id="a")
        assert lc.can_transition(AgentState.SPAWNED) is True

    def test_can_transition_returns_false_for_invalid(self):
        lc = AgentLifecycle(agent_id="a")
        assert lc.can_transition(AgentState.COMPLETED) is False

    # ──────────────────────────────────────────────────────────────────
    # Terminal / active
    # ──────────────────────────────────────────────────────────────────

    def test_terminated_is_terminal(self):
        lc = AgentLifecycle(agent_id="a")
        for state in [AgentState.SPAWNED, AgentState.ASSIGNED, AgentState.RUNNING,
                      AgentState.VERIFYING, AgentState.COMPLETED, AgentState.TERMINATED]:
            lc.transition(state)
        assert lc.is_terminal() is True

    def test_ready_is_not_terminal(self):
        lc = AgentLifecycle(agent_id="a")
        assert lc.is_terminal() is False

    def test_running_is_active(self):
        lc = AgentLifecycle(agent_id="a")
        lc.transition(AgentState.SPAWNED)
        lc.transition(AgentState.ASSIGNED)
        lc.transition(AgentState.RUNNING)
        assert lc.is_active() is True

    def test_ready_is_not_active(self):
        lc = AgentLifecycle(agent_id="a")
        assert lc.is_active() is False

    # ──────────────────────────────────────────────────────────────────
    # History
    # ──────────────────────────────────────────────────────────────────

    def test_history_tracks_all_states(self):
        lc = AgentLifecycle(agent_id="a")
        lc.transition(AgentState.SPAWNED)
        lc.transition(AgentState.ASSIGNED)
        assert lc.history == [AgentState.READY, AgentState.SPAWNED, AgentState.ASSIGNED]

    # ──────────────────────────────────────────────────────────────────
    # Observer callback
    # ──────────────────────────────────────────────────────────────────

    def test_observer_called_on_transition(self):
        transitions = []

        def observer(agent_id, from_state, to_state):
            transitions.append((agent_id, from_state, to_state))

        lc = AgentLifecycle(agent_id="obs-agent", on_transition=observer)
        lc.transition(AgentState.SPAWNED)

        assert len(transitions) == 1
        assert transitions[0] == ("obs-agent", AgentState.READY, AgentState.SPAWNED)

    def test_observer_not_called_on_invalid_transition(self):
        transitions = []

        def observer(agent_id, from_state, to_state):
            transitions.append((from_state, to_state))

        lc = AgentLifecycle(agent_id="a", on_transition=observer)
        with pytest.raises(InvalidTransitionError):
            lc.transition(AgentState.COMPLETED)

        assert transitions == []
