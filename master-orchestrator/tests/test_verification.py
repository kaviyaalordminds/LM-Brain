"""
Tests for ResultVerifier — all 7 verification gate checks.

Gate checks:
1. Schema valid (required fields)
2. task_id identity
3. agent_type matches specialist_id
4. Status not failed
5. Artifacts present when expected
6. verification.verdict is PASS or SKIPPED
7. No critical errors
"""
from __future__ import annotations

import pytest

from app.verification.result_verifier import ResultVerifier, VerificationGateResult


def make_attempt(attempt_id: str = "attempt-123"):
    class FakeAttempt:
        pass
    a = FakeAttempt()
    a.attempt_id = attempt_id
    return a


def make_valid_result(**overrides) -> dict:
    base = {
        "task_id": "attempt-123",
        "status": "completed",
        "agent_type": "backend",
        "artifacts": [{"artifact_id": "art-1", "type": "code"}],
        "verification": {"verdict": "PASS"},
        "errors": [],
        "output": "done",
    }
    base.update(overrides)
    return base


def make_plan_step(**overrides) -> dict:
    base = {
        "specialist_id": "backend",
        "expected_outputs": ["backend code"],
    }
    base.update(overrides)
    return base


class TestVerificationGatePasses:
    def test_fully_valid_result_passes(self):
        verifier = ResultVerifier()
        result = make_valid_result()
        step = make_plan_step()
        gate = verifier.verify(result, step, make_attempt())
        assert gate.passed is True
        assert len(gate.checks) == 7
        assert all(c.passed for c in gate.checks)

    def test_skipped_verdict_passes(self):
        result = make_valid_result(verification={"verdict": "SKIPPED"})
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        assert gate.passed is True

    def test_no_expected_outputs_no_artifacts_ok(self):
        """If plan step declares no expected outputs, empty artifacts is fine."""
        result = make_valid_result(artifacts=[])
        step = make_plan_step(expected_outputs=[])
        gate = ResultVerifier().verify(result, step, make_attempt())
        assert gate.passed is True

    def test_running_status_without_artifacts_ok(self):
        """Running tasks aren't required to have artifacts yet."""
        result = make_valid_result(status="running", artifacts=[])
        step = make_plan_step(expected_outputs=["some output"])
        gate = ResultVerifier().verify(result, step, make_attempt())
        assert gate.passed is True


class TestSchemaValidation:
    def test_missing_task_id_fails_schema(self):
        result = {"status": "completed", "agent_type": "backend", "artifacts": [], "verification": {"verdict": "PASS"}, "errors": []}
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        schema_check = next(c for c in gate.checks if c.name == "schema_valid")
        assert schema_check.passed is False
        assert gate.passed is False

    def test_missing_agent_type_fails_schema(self):
        result = {"task_id": "attempt-123", "status": "completed", "artifacts": [], "verification": {"verdict": "PASS"}, "errors": []}
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        schema_check = next(c for c in gate.checks if c.name == "schema_valid")
        assert schema_check.passed is False


class TestStatusCheck:
    def test_failed_status_fails_gate(self):
        result = make_valid_result(status="failed")
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        assert gate.passed is False
        status_check = next(c for c in gate.checks if c.name == "status_not_failed")
        assert status_check.passed is False

    def test_cancelled_status_fails_gate(self):
        result = make_valid_result(status="cancelled")
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        assert gate.passed is False


class TestAgentTypeCheck:
    def test_wrong_agent_type_fails(self):
        result = make_valid_result(agent_type="database")  # step expects "backend"
        gate = ResultVerifier().verify(result, make_plan_step(specialist_id="backend"), make_attempt())
        agent_check = next(c for c in gate.checks if c.name == "agent_type_matches")
        assert agent_check.passed is False

    def test_no_specialist_id_in_step_skips_check(self):
        result = make_valid_result(agent_type="any_type")
        step = {}  # no specialist_id
        gate = ResultVerifier().verify(result, step, make_attempt())
        agent_check = next(c for c in gate.checks if c.name == "agent_type_matches")
        assert agent_check.passed is True


class TestVerificationVerdictCheck:
    def test_verdict_fail_fails_gate(self):
        result = make_valid_result(verification={"verdict": "FAIL"})
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        verdict_check = next(c for c in gate.checks if c.name == "verification_verdict")
        assert verdict_check.passed is False
        assert gate.passed is False


class TestCriticalErrorsCheck:
    def test_critical_error_fails_gate(self):
        result = make_valid_result(errors=[{"error_code": "TOOL_FAILED", "message": "tool crashed"}])
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        err_check = next(c for c in gate.checks if c.name == "no_critical_errors")
        assert err_check.passed is False
        assert gate.passed is False

    def test_info_error_does_not_fail_gate(self):
        result = make_valid_result(errors=[{"error_code": "INFO", "message": "note"}])
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        err_check = next(c for c in gate.checks if c.name == "no_critical_errors")
        assert err_check.passed is True


class TestGateResultStructure:
    def test_gate_result_has_7_checks(self):
        gate = ResultVerifier().verify(make_valid_result(), make_plan_step(), make_attempt())
        assert len(gate.checks) == 7

    def test_fail_reason_populated_on_failure(self):
        result = make_valid_result(status="failed")
        gate = ResultVerifier().verify(result, make_plan_step(), make_attempt())
        assert "fail" in gate.fail_reason().lower() or len(gate.reasons) > 0

