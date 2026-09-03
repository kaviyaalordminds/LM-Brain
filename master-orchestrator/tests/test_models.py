"""
Tests for all Pydantic models — Execution, State, Events, Dispatch, Artifacts.
"""
from __future__ import annotations

import pytest

from app.models.execution import Execution, ExecutionPhase, ExecutionStatus
from app.models.state import LEGAL_TRANSITIONS, StepLifecycle
from app.models.events import EventType, ExecutionEvent
from app.models.dispatch import AttemptStatus, DispatchAttempt, DispatchRequest
from app.models.artifacts import LineageArtifact, TrustState


class TestExecutionModel:
    def test_execution_status_values(self):
        expected = {"CREATED", "PLANNING", "PLANNED", "RUNNING", "PAUSED", "RECOVERING", "COMPLETED", "FAILED", "CANCELLED"}
        assert {s.value for s in ExecutionStatus} == expected

    def test_execution_phase_values(self):
        expected = {"INTENT_NORMALIZATION", "PLANNING", "SCHEDULING", "DISPATCHING", "VERIFYING", "RECOVERING", "FINALIZING"}
        assert {p.value for p in ExecutionPhase} == expected

    def test_execution_model_instantiation(self):
        import datetime, uuid
        e = Execution(
            execution_id="exec-1",
            request_id="req-1",
            user_request="Build me a backend API",
            created_at=datetime.datetime.utcnow().isoformat(),
            updated_at=datetime.datetime.utcnow().isoformat(),
            correlation_id="corr-1",
        )
        assert e.execution_id == "exec-1"
        assert e.status == ExecutionStatus.CREATED
        assert e.phase == ExecutionPhase.INTENT_NORMALIZATION
        assert e.plan_version == 1
        assert e.completed_steps == []
        assert e.failed_steps == []

    def test_execution_default_lists(self):
        import datetime
        e = Execution(
            execution_id="e", request_id="r", user_request="test",
            created_at=datetime.datetime.utcnow().isoformat(),
            updated_at=datetime.datetime.utcnow().isoformat(),
            correlation_id="c",
        )
        assert isinstance(e.completed_steps, list)
        assert isinstance(e.failed_steps, list)
        assert isinstance(e.running_steps, list)
        assert isinstance(e.blocked_steps, list)
        assert isinstance(e.artifacts, list)
        assert isinstance(e.metadata, dict)


class TestStateModel:
    def test_step_lifecycle_values(self):
        expected = {"PENDING", "READY", "QUEUED", "DISPATCHED", "RUNNING", "VERIFYING", "COMPLETED", "FAILED", "BLOCKED", "SKIPPED"}
        assert {s.value for s in StepLifecycle} == expected

    def test_legal_transitions_covers_all_states(self):
        for state in StepLifecycle:
            assert state in LEGAL_TRANSITIONS

    def test_completed_has_no_legal_transitions(self):
        assert LEGAL_TRANSITIONS[StepLifecycle.COMPLETED] == set()

    def test_skipped_has_no_legal_transitions(self):
        assert LEGAL_TRANSITIONS[StepLifecycle.SKIPPED] == set()

    def test_failed_can_transition_to_ready(self):
        assert StepLifecycle.READY in LEGAL_TRANSITIONS[StepLifecycle.FAILED]


class TestEventModel:
    def test_all_23_event_types(self):
        expected = {
            "EXECUTION_CREATED", "PLAN_REQUESTED", "PLAN_RECEIVED", "STEP_READY",
            "STEP_QUEUED", "STEP_DISPATCHED", "STEP_STARTED", "STEP_COMPLETED",
            "STEP_FAILED", "VERIFICATION_STARTED", "VERIFICATION_PASSED",
            "VERIFICATION_FAILED", "RETRY_SCHEDULED", "RECOVERY_STARTED",
            "REPLAN_REQUESTED", "REPLAN_RECEIVED", "ARTIFACT_CREATED",
            "EXECUTION_PAUSED", "EXECUTION_RESUMED", "EXECUTION_CANCELLED",
            "EXECUTION_COMPLETED", "EXECUTION_FAILED", "MEMORY_CONTEXT_FETCHED",
        }
        actual = {e.value for e in EventType}
        assert actual == expected

    def test_execution_event_instantiation(self):
        import datetime, uuid
        event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.EXECUTION_CREATED,
            execution_id="exec-1",
            correlation_id="corr-1",
            timestamp=datetime.datetime.utcnow().isoformat(),
            payload={"user_request": "test"},
        )
        assert event.event_type == EventType.EXECUTION_CREATED
        assert event.execution_id == "exec-1"
        assert event.step_id is None  # optional fields
        assert event.task_id is None

    def test_event_optional_fields_default_none(self):
        import datetime, uuid
        event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.STEP_COMPLETED,
            execution_id="exec-1",
            correlation_id="corr-1",
            timestamp=datetime.datetime.utcnow().isoformat(),
            payload={},
        )
        assert event.plan_id is None
        assert event.attempt_id is None


class TestDispatchModel:
    def test_attempt_status_values(self):
        expected = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
        assert {s.value for s in AttemptStatus} == expected

    def test_dispatch_attempt_instantiation(self):
        import datetime, uuid
        attempt = DispatchAttempt(
            attempt_id=str(uuid.uuid4()),
            attempt_number=1,
            step_id="step-1",
            execution_id="exec-1",
            started_at=datetime.datetime.utcnow().isoformat(),
            status=AttemptStatus.RUNNING,
            idempotency_key="exec-1:step-1:attempt-1",
        )
        assert attempt.status == AttemptStatus.RUNNING
        assert attempt.result is None
        assert attempt.error is None

    def test_idempotency_key_format(self):
        import datetime, uuid
        attempt = DispatchAttempt(
            attempt_id="atmp-1",
            attempt_number=0,
            step_id="step-A",
            execution_id="exec-X",
            started_at=datetime.datetime.utcnow().isoformat(),
            status=AttemptStatus.PENDING,
            idempotency_key="exec-X:step-A:atmp-1",
        )
        assert "exec-X" in attempt.idempotency_key
        assert "step-A" in attempt.idempotency_key
        assert "atmp-1" in attempt.idempotency_key


class TestArtifactsModel:
    def test_trust_state_values(self):
        expected = {"UNVERIFIED", "VALIDATED", "APPROVED", "RETRIEVED", "REJECTED", "PENDING"}
        assert {t.value for t in TrustState} == expected


    def test_lineage_artifact_instantiation(self):
        import datetime, uuid
        artifact = LineageArtifact(
            artifact_id=str(uuid.uuid4()),
            execution_id="exec-1",
            plan_id="plan-1",
            plan_version=1,
            step_id="step-1",
            task_id="task-1",
            attempt_id="atmp-1",
            specialist_id="backend",
            artifact_type="code",
            path="/output/app.py",
            url="",
            content="",
            is_mock=False,
            parent_artifact_ids=[],
            source_evidence_refs=[],
            trust_state=TrustState.APPROVED,
            verification_status="PASSED",
            created_at=datetime.datetime.utcnow().isoformat(),
        )
        assert artifact.trust_state == TrustState.APPROVED
        assert artifact.is_mock is False

    def test_mock_artifact_is_flagged(self):
        import datetime, uuid
        artifact = LineageArtifact(
            artifact_id=str(uuid.uuid4()),
            execution_id="exec-1",
            plan_id="plan-1",
            plan_version=1,
            step_id="step-1",
            task_id="task-1",
            attempt_id="atmp-1",
            specialist_id="testing",
            artifact_type="mock",
            path="",
            url="",
            content="[MOCK]",
            is_mock=True,
            parent_artifact_ids=[],
            source_evidence_refs=[],
            trust_state=TrustState.UNVERIFIED,
            verification_status="SKIPPED",
            created_at=datetime.datetime.utcnow().isoformat(),
        )
        assert artifact.is_mock is True

