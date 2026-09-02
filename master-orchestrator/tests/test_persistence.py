"""
Tests for ExecutionRepository and EventStore persistence — save, retrieve, update, lineage.
"""
from __future__ import annotations

import datetime
import uuid

import pytest

from app.models.execution import Execution, ExecutionStatus
from app.models.dispatch import AttemptStatus, DispatchAttempt
from app.models.artifacts import LineageArtifact, TrustState
from app.persistence.repository import InMemoryExecutionRepository


def make_execution(eid: str = "exec-1") -> Execution:
    return Execution(
        execution_id=eid,
        request_id="req-1",
        user_request="test request",
        created_at=datetime.datetime.utcnow().isoformat(),
        updated_at=datetime.datetime.utcnow().isoformat(),
        correlation_id=eid,
    )


def make_attempt(execution_id: str, step_id: str) -> DispatchAttempt:
    aid = str(uuid.uuid4())
    return DispatchAttempt(
        attempt_id=aid,
        attempt_number=0,
        step_id=step_id,
        execution_id=execution_id,
        started_at=datetime.datetime.utcnow().isoformat(),
        status=AttemptStatus.COMPLETED,
        idempotency_key=f"{execution_id}:{step_id}:{aid}",
    )


def make_artifact(execution_id: str) -> LineageArtifact:
    return LineageArtifact(
        artifact_id=str(uuid.uuid4()),
        execution_id=execution_id,
        plan_id="plan-1",
        plan_version=1,
        step_id="step-1",
        task_id="task-1",
        attempt_id="atmp-1",
        specialist_id="backend",
        artifact_type="code",
        path="/output/api.py",
        url="",
        content="",
        is_mock=False,
        parent_artifact_ids=[],
        source_evidence_refs=[],
        trust_state=TrustState.APPROVED,
        verification_status="PASSED",
        created_at=datetime.datetime.utcnow().isoformat(),
    )


class TestInMemoryRepository:
    def test_save_and_get_execution(self):
        repo = InMemoryExecutionRepository()
        exec_ = make_execution("exec-1")
        repo.save_execution(exec_)
        retrieved = repo.get_execution("exec-1")
        assert retrieved is not None
        assert retrieved.execution_id == "exec-1"

    def test_get_nonexistent_execution_returns_none(self):
        repo = InMemoryExecutionRepository()
        assert repo.get_execution("nonexistent") is None

    def test_update_execution(self):
        repo = InMemoryExecutionRepository()
        exec_ = make_execution("exec-1")
        repo.save_execution(exec_)
        exec_.status = ExecutionStatus.RUNNING
        repo.update_execution(exec_)
        retrieved = repo.get_execution("exec-1")
        assert retrieved.status == ExecutionStatus.RUNNING

    def test_list_executions(self):
        repo = InMemoryExecutionRepository()
        repo.save_execution(make_execution("exec-1"))
        repo.save_execution(make_execution("exec-2"))
        all_execs = repo.list_executions()
        ids = [e.execution_id for e in all_execs]
        assert "exec-1" in ids
        assert "exec-2" in ids

    def test_save_and_get_attempts(self):
        repo = InMemoryExecutionRepository()
        exec_ = make_execution("exec-1")
        repo.save_execution(exec_)
        attempt = make_attempt("exec-1", "step-1")
        repo.save_attempt(attempt)
        attempts = repo.get_attempts("exec-1")
        assert len(attempts) == 1
        assert attempts[0].execution_id == "exec-1"

    def test_attempts_filtered_by_execution(self):
        repo = InMemoryExecutionRepository()
        a1 = make_attempt("exec-1", "step-1")
        a2 = make_attempt("exec-2", "step-1")
        repo.save_attempt(a1)
        repo.save_attempt(a2)
        exec1_attempts = repo.get_attempts("exec-1")
        assert len(exec1_attempts) == 1
        assert exec1_attempts[0].execution_id == "exec-1"

    def test_multiple_attempts_same_execution(self):
        repo = InMemoryExecutionRepository()
        for _ in range(3):
            repo.save_attempt(make_attempt("exec-1", "step-1"))
        attempts = repo.get_attempts("exec-1")
        assert len(attempts) == 3

    def test_save_and_get_artifacts(self):
        repo = InMemoryExecutionRepository()
        artifact = make_artifact("exec-1")
        repo.save_artifact(artifact)
        artifacts = repo.get_artifacts("exec-1")
        assert len(artifacts) == 1
        assert artifacts[0].execution_id == "exec-1"

    def test_artifacts_filtered_by_execution(self):
        repo = InMemoryExecutionRepository()
        repo.save_artifact(make_artifact("exec-1"))
        repo.save_artifact(make_artifact("exec-2"))
        assert len(repo.get_artifacts("exec-1")) == 1
        assert len(repo.get_artifacts("exec-2")) == 1

    def test_save_and_get_plan_versions(self):
        repo = InMemoryExecutionRepository()
        plan_v1 = {"plan_id": "plan-1", "version": 1, "steps": []}
        plan_v2 = {"plan_id": "plan-1", "version": 2, "steps": ["recovery-step"]}
        repo.save_plan_version(plan_v1)
        repo.save_plan_version(plan_v2)
        versions = repo.get_plan_versions("plan-1")
        assert len(versions) == 2

    def test_plan_versions_filtered_by_plan_id(self):
        repo = InMemoryExecutionRepository()
        repo.save_plan_version({"plan_id": "plan-1", "version": 1})
        repo.save_plan_version({"plan_id": "plan-2", "version": 1})
        assert len(repo.get_plan_versions("plan-1")) == 1
        assert len(repo.get_plan_versions("plan-2")) == 1

    def test_no_shared_state_between_instances(self):
        repo1 = InMemoryExecutionRepository()
        repo2 = InMemoryExecutionRepository()
        repo1.save_execution(make_execution("exec-1"))
        assert repo2.get_execution("exec-1") is None

