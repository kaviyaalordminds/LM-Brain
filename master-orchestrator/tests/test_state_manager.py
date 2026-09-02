"""
Tests for StateManager — legal/illegal transitions, concurrency safety, multi-execution isolation.
"""
from __future__ import annotations

import threading

import pytest

from app.core.state_manager import IllegalTransitionError, StateManager
from app.models.state import LEGAL_TRANSITIONS, StepLifecycle


class TestLegalTransitions:
    def test_pending_to_ready(self):
        sm = StateManager()
        rec = sm.transition("exec-1", "step-1", StepLifecycle.READY)
        assert rec.old_state == StepLifecycle.PENDING
        assert rec.new_state == StepLifecycle.READY

    def test_pending_to_blocked(self):
        sm = StateManager()
        rec = sm.transition("exec-1", "step-1", StepLifecycle.BLOCKED)
        assert rec.new_state == StepLifecycle.BLOCKED

    def test_ready_to_queued(self):
        sm = StateManager()
        sm.transition("exec-1", "step-1", StepLifecycle.READY)
        rec = sm.transition("exec-1", "step-1", StepLifecycle.QUEUED)
        assert rec.new_state == StepLifecycle.QUEUED

    def test_full_happy_path(self):
        """PENDING → READY → QUEUED → DISPATCHED → RUNNING → VERIFYING → COMPLETED"""
        sm = StateManager()
        path = [
            StepLifecycle.READY,
            StepLifecycle.QUEUED,
            StepLifecycle.DISPATCHED,
            StepLifecycle.RUNNING,
            StepLifecycle.VERIFYING,
            StepLifecycle.COMPLETED,
        ]
        for state in path:
            rec = sm.transition("exec-1", "step-1", state)
            assert rec.new_state == state

    def test_failed_to_ready_for_retry(self):
        """FAILED → READY is legal (retry)"""
        sm = StateManager()
        sm.transition("exec-1", "step-1", StepLifecycle.READY)
        sm.transition("exec-1", "step-1", StepLifecycle.QUEUED)
        sm.transition("exec-1", "step-1", StepLifecycle.DISPATCHED)
        sm.transition("exec-1", "step-1", StepLifecycle.RUNNING)
        sm.transition("exec-1", "step-1", StepLifecycle.FAILED)
        rec = sm.transition("exec-1", "step-1", StepLifecycle.READY)
        assert rec.new_state == StepLifecycle.READY

    def test_blocked_to_ready_for_unblock(self):
        sm = StateManager()
        sm.transition("exec-1", "step-1", StepLifecycle.BLOCKED)
        rec = sm.transition("exec-1", "step-1", StepLifecycle.READY)
        assert rec.new_state == StepLifecycle.READY


class TestIllegalTransitions:
    def test_completed_is_terminal(self):
        sm = StateManager()
        sm.transition("exec-1", "step-1", StepLifecycle.READY)
        sm.transition("exec-1", "step-1", StepLifecycle.QUEUED)
        sm.transition("exec-1", "step-1", StepLifecycle.DISPATCHED)
        sm.transition("exec-1", "step-1", StepLifecycle.RUNNING)
        sm.transition("exec-1", "step-1", StepLifecycle.VERIFYING)
        sm.transition("exec-1", "step-1", StepLifecycle.COMPLETED)
        with pytest.raises(IllegalTransitionError):
            sm.transition("exec-1", "step-1", StepLifecycle.RUNNING)

    def test_skipped_is_terminal(self):
        sm = StateManager()
        sm.transition("exec-1", "step-1", StepLifecycle.READY)
        sm.transition("exec-1", "step-1", StepLifecycle.SKIPPED)
        with pytest.raises(IllegalTransitionError):
            sm.transition("exec-1", "step-1", StepLifecycle.RUNNING)

    def test_pending_directly_to_running_rejected(self):
        sm = StateManager()
        with pytest.raises(IllegalTransitionError):
            sm.transition("exec-1", "step-1", StepLifecycle.RUNNING)

    def test_pending_directly_to_completed_rejected(self):
        sm = StateManager()
        with pytest.raises(IllegalTransitionError):
            sm.transition("exec-1", "step-1", StepLifecycle.COMPLETED)

    def test_running_to_queued_rejected(self):
        sm = StateManager()
        sm.transition("exec-1", "step-1", StepLifecycle.READY)
        sm.transition("exec-1", "step-1", StepLifecycle.QUEUED)
        sm.transition("exec-1", "step-1", StepLifecycle.DISPATCHED)
        sm.transition("exec-1", "step-1", StepLifecycle.RUNNING)
        with pytest.raises(IllegalTransitionError):
            sm.transition("exec-1", "step-1", StepLifecycle.QUEUED)


class TestMultiExecutionIsolation:
    def test_different_executions_independent(self):
        """State for exec-1:step-1 must not affect exec-2:step-1."""
        sm = StateManager()
        sm.transition("exec-1", "step-1", StepLifecycle.READY)
        sm.transition("exec-2", "step-1", StepLifecycle.BLOCKED)
        # exec-1 step-1 should be READY
        assert sm.states.get("exec-1:step-1") == StepLifecycle.READY
        # exec-2 step-1 should be BLOCKED
        assert sm.states.get("exec-2:step-1") == StepLifecycle.BLOCKED

    def test_different_steps_same_execution_independent(self):
        sm = StateManager()
        sm.transition("exec-1", "step-A", StepLifecycle.READY)
        sm.transition("exec-1", "step-B", StepLifecycle.BLOCKED)
        assert sm.states.get("exec-1:step-A") == StepLifecycle.READY
        assert sm.states.get("exec-1:step-B") == StepLifecycle.BLOCKED


class TestConcurrencySafety:
    def test_concurrent_transitions_no_race(self):
        """Multiple threads transitioning different steps must not corrupt shared state."""
        sm = StateManager()
        errors = []

        def transition_step(step_id: str):
            try:
                sm.transition("exec-1", step_id, StepLifecycle.READY)
                sm.transition("exec-1", step_id, StepLifecycle.QUEUED)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=transition_step, args=(f"step-{i}",)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent transitions produced errors: {errors}"
        # Verify all 20 steps are QUEUED
        for i in range(20):
            assert sm.states.get(f"exec-1:step-{i}") == StepLifecycle.QUEUED


class TestLegalTransitionsCompleteness:
    def test_all_states_have_transition_entry(self):
        """Every StepLifecycle value must have an entry in LEGAL_TRANSITIONS."""
        for state in StepLifecycle:
            assert state in LEGAL_TRANSITIONS, f"{state} missing from LEGAL_TRANSITIONS"

