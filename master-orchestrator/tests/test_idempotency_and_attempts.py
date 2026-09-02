import pytest
import uuid
import datetime
from app.persistence.repository import SQLiteExecutionRepository
from app.models.dispatch import DispatchAttempt, AttemptStatus

def test_idempotency_ledger(tmp_path):
    db_file = str(tmp_path / "test_idempotency.db")
    repo = SQLiteExecutionRepository(db_path=db_file)

    key = "idem-req-12345"
    exec_id = "exec-idem-01"
    response_payload = {"execution_id": exec_id, "status": "CREATED"}

    # First check: not present
    assert repo.check_idempotency(key) is None

    # Record idempotency
    repo.record_idempotency(key, exec_id, response_payload)

    # Second check: present and identical
    cached = repo.check_idempotency(key)
    assert cached == response_payload

def test_immutable_historical_attempts(tmp_path):
    db_file = str(tmp_path / "test_attempts.db")
    repo = SQLiteExecutionRepository(db_path=db_file)
    exec_id = "exec-att-test"

    # Attempt 1: Failed
    att1 = DispatchAttempt(
        attempt_id="att-1",
        attempt_number=1,
        step_id="step-sec",
        task_id="task-1",
        execution_id=exec_id,
        specialist_id="security",
        started_at=datetime.datetime.utcnow().isoformat(),
        completed_at=datetime.datetime.utcnow().isoformat(),
        duration_ms=250.0,
        status=AttemptStatus.FAILED,
        failure_type="MODEL_UNAVAILABLE",
        error="No model provider configured",
        idempotency_key=f"{exec_id}:step-sec:1"
    )
    repo.save_attempt(att1)

    # Attempt 2: Failed
    att2 = DispatchAttempt(
        attempt_id="att-2",
        attempt_number=2,
        step_id="step-sec",
        task_id="task-2",
        execution_id=exec_id,
        specialist_id="security",
        started_at=datetime.datetime.utcnow().isoformat(),
        completed_at=datetime.datetime.utcnow().isoformat(),
        duration_ms=310.0,
        status=AttemptStatus.FAILED,
        failure_type="MODEL_UNAVAILABLE",
        error="No model provider configured",
        idempotency_key=f"{exec_id}:step-sec:2"
    )
    repo.save_attempt(att2)

    history = repo.get_attempts(exec_id)
    assert len(history) == 2
    assert history[0].attempt_number == 1
    assert history[1].attempt_number == 2
    assert history[0].attempt_id == "att-1"
    assert history[1].attempt_id == "att-2"
