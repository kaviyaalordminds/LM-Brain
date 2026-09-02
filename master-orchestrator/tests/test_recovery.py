"""
Tests for RecoveryManager — decision matrix, downstream BFS, recovery context.
"""
from __future__ import annotations

import pytest

from app.core.recovery_manager import RecoveryDecision, RecoveryManager
from app.policies.failure_policy import FailureType


def make_execution(
    completed=None, failed=None, blocked=None, running=None, artifacts=None
):
    class FakeExecution:
        pass
    e = FakeExecution()
    e.user_request = "build something"
    e.plan_id = "plan-1"
    e.plan_version = 1
    e.completed_steps = completed or []
    e.failed_steps = failed or []
    e.blocked_steps = blocked or []
    e.running_steps = running or []
    e.artifacts = artifacts or []
    e.error = None
    return e


class TestDecisionMatrix:
    def test_timeout_within_budget_retries(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", FailureType.TIMEOUT, attempt_number=0, max_retries=3)
        assert decision == RecoveryDecision.RETRY

    def test_service_unavailable_within_budget_retries(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", FailureType.SERVICE_UNAVAILABLE, attempt_number=1, max_retries=3)
        assert decision == RecoveryDecision.RETRY

    def test_permission_denied_is_blocked(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", FailureType.PERMISSION_DENIED, attempt_number=0, max_retries=10)
        assert decision == RecoveryDecision.BLOCK

    def test_cancelled_terminates(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", FailureType.CANCELLED, attempt_number=0, max_retries=10)
        assert decision == RecoveryDecision.TERMINATE

    def test_contract_violation_triggers_replan(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", FailureType.CONTRACT_VIOLATION, attempt_number=0, max_retries=10)
        assert decision == RecoveryDecision.REPLAN

    def test_verification_failed_triggers_replan(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", FailureType.VERIFICATION_FAILED, attempt_number=0, max_retries=10)
        assert decision == RecoveryDecision.REPLAN

    def test_budget_exhausted_triggers_replan(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", FailureType.TIMEOUT, attempt_number=3, max_retries=3)
        assert decision == RecoveryDecision.REPLAN

    def test_string_failure_type_accepted(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", "TIMEOUT", attempt_number=0, max_retries=3)
        assert decision == RecoveryDecision.RETRY

    def test_unknown_failure_string_maps_to_unknown(self):
        rm = RecoveryManager()
        decision = rm.analyze_failure("step-1", "UNKNOWN_GARBAGE", attempt_number=0, max_retries=3)
        # UNKNOWN is retryable within budget
        assert decision == RecoveryDecision.RETRY


class TestDownstreamBlocking:
    def test_single_level_downstream(self):
        """step-2 depends on step-1. If step-1 fails, step-2 should be blocked."""
        deps = {
            "step-1": [],
            "step-2": ["step-1"],
            "step-3": ["step-2"],
        }
        rm = RecoveryManager()
        blocked = rm.compute_downstream_blocked("step-1", deps)
        assert "step-2" in blocked
        assert "step-3" in blocked

    def test_independent_step_not_blocked(self):
        """step-3 does not depend on step-1."""
        deps = {
            "step-1": [],
            "step-2": ["step-1"],
            "step-3": [],
        }
        rm = RecoveryManager()
        blocked = rm.compute_downstream_blocked("step-1", deps)
        assert "step-2" in blocked
        assert "step-3" not in blocked

    def test_no_dependents_returns_empty(self):
        deps = {"step-1": [], "step-2": []}
        rm = RecoveryManager()
        blocked = rm.compute_downstream_blocked("step-1", deps)
        assert blocked == []


class TestRecoveryContext:
    def test_recovery_context_contains_required_fields(self):
        exec_ = make_execution(
            completed=["step-1", "step-2"],
            failed=["step-3"],
            blocked=["step-4", "step-5"],
        )
        rm = RecoveryManager()
        ctx = rm.compute_recovery_context(exec_)
        assert "original_user_request" in ctx
        assert "plan_id" in ctx
        assert "plan_version" in ctx
        assert "completed_steps" in ctx
        assert "failed_steps" in ctx
        assert "blocked_steps" in ctx
        assert "reusable_artifacts" in ctx

    def test_recovery_context_values_correct(self):
        exec_ = make_execution(
            completed=["step-1"],
            failed=["step-2"],
            artifacts=["art-1"],
        )
        rm = RecoveryManager()
        ctx = rm.compute_recovery_context(exec_)
        assert "step-1" in ctx["completed_steps"]
        assert "step-2" in ctx["failed_steps"]
        assert "art-1" in ctx["reusable_artifacts"]

