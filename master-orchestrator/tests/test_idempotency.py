"""
Tests for Idempotency — dispatch key uniqueness, duplicate detection, collision prevention.

Idempotency key format: execution_id:step_id:attempt_id
"""
from __future__ import annotations

import pytest

from app.models.dispatch import AttemptStatus, DispatchAttempt


def make_attempt(execution_id: str, step_id: str, attempt_id: str, attempt_number: int = 0) -> DispatchAttempt:
    import datetime
    key = f"{execution_id}:{step_id}:{attempt_id}"
    return DispatchAttempt(
        attempt_id=attempt_id,
        attempt_number=attempt_number,
        step_id=step_id,
        execution_id=execution_id,
        started_at=datetime.datetime.utcnow().isoformat(),
        status=AttemptStatus.RUNNING,
        idempotency_key=key,
    )


class TestIdempotencyKeyGeneration:
    def test_key_contains_all_three_components(self):
        attempt = make_attempt("exec-abc", "step-xyz", "atmp-001")
        key = attempt.idempotency_key
        assert "exec-abc" in key
        assert "step-xyz" in key
        assert "atmp-001" in key

    def test_key_format_is_colon_separated(self):
        attempt = make_attempt("exec-1", "step-1", "atmp-1")
        assert attempt.idempotency_key == "exec-1:step-1:atmp-1"

    def test_different_attempt_numbers_produce_different_keys(self):
        attempt_0 = make_attempt("exec-1", "step-1", "atmp-0", 0)
        attempt_1 = make_attempt("exec-1", "step-1", "atmp-1", 1)
        assert attempt_0.idempotency_key != attempt_1.idempotency_key

    def test_different_steps_produce_different_keys(self):
        a1 = make_attempt("exec-1", "step-A", "atmp-1")
        a2 = make_attempt("exec-1", "step-B", "atmp-1")
        assert a1.idempotency_key != a2.idempotency_key

    def test_different_executions_produce_different_keys(self):
        a1 = make_attempt("exec-1", "step-1", "atmp-1")
        a2 = make_attempt("exec-2", "step-1", "atmp-1")
        assert a1.idempotency_key != a2.idempotency_key


class TestIdempotencyRegistry:
    """Test that a simple registry correctly detects duplicates."""

    def test_first_registration_succeeds(self):
        registry: set[str] = set()
        attempt = make_attempt("exec-1", "step-1", "atmp-1")
        # First time: not in registry
        assert attempt.idempotency_key not in registry
        registry.add(attempt.idempotency_key)

    def test_duplicate_registration_detected(self):
        registry: set[str] = set()
        a1 = make_attempt("exec-1", "step-1", "atmp-1")
        a2 = make_attempt("exec-1", "step-1", "atmp-1")  # same key
        registry.add(a1.idempotency_key)
        # Second attempt with same key must be detected as duplicate
        assert a2.idempotency_key in registry

    def test_retry_attempt_has_different_key(self):
        """Retry attempts MUST have a new attempt_id (and therefore a different key)."""
        registry: set[str] = set()
        original = make_attempt("exec-1", "step-1", "atmp-original")
        retry = make_attempt("exec-1", "step-1", "atmp-retry")  # new attempt_id
        registry.add(original.idempotency_key)
        # Retry key must NOT be in registry
        assert retry.idempotency_key not in registry

    def test_100_unique_keys_no_collisions(self):
        import uuid
        registry: set[str] = set()
        for _ in range(100):
            key = f"exec-1:step-1:{uuid.uuid4()}"
            assert key not in registry, f"Collision detected for {key}"
            registry.add(key)
        assert len(registry) == 100


class TestAttemptStatusTransitions:
    def test_completed_attempt_records_result(self):
        import datetime
        attempt = make_attempt("exec-1", "step-1", "atmp-1")
        attempt.status = AttemptStatus.COMPLETED
        attempt.result = {"status": "completed", "output": "done"}
        attempt.completed_at = datetime.datetime.utcnow().isoformat()
        assert attempt.status == AttemptStatus.COMPLETED
        assert attempt.result is not None

    def test_failed_attempt_records_error(self):
        import datetime
        attempt = make_attempt("exec-1", "step-1", "atmp-1")
        attempt.status = AttemptStatus.FAILED
        attempt.error = "Specialist timed out"
        attempt.failure_type = "TIMEOUT"
        attempt.completed_at = datetime.datetime.utcnow().isoformat()
        assert attempt.status == AttemptStatus.FAILED
        assert attempt.failure_type == "TIMEOUT"

