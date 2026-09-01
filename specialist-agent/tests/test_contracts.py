"""
Tests for task, result, and artifact contracts.

Covers:
  - TaskRequest validation
  - TaskResult status transitions
  - Artifact types and mock detection
  - VerificationOutcome
  - AgentEvent creation
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from specialist_agent.contracts.artifact import Artifact, ArtifactType, make_mock_artifact
from specialist_agent.contracts.events import AgentEvent, EventType
from specialist_agent.contracts.result import (
    TaskResult,
    TaskStatus,
    VerificationCheck,
    VerificationOutcome,
    VerificationVerdict,
)
from specialist_agent.contracts.task import TaskRequest


class TestTaskRequest:
    def test_valid_task_request(self):
        task = TaskRequest(
            agent_type="image_generation",
            instruction="Generate a futuristic electric car",
        )
        assert task.agent_type == "image_generation"
        assert task.instruction == "Generate a futuristic electric car"
        assert task.task_id  # UUID is auto-generated

    def test_agent_type_normalised_to_lowercase(self):
        task = TaskRequest(agent_type="IMAGE_GENERATION", instruction="test")
        assert task.agent_type == "image_generation"

    def test_empty_instruction_raises(self):
        with pytest.raises(ValidationError):
            TaskRequest(agent_type="web_development", instruction="")

    def test_whitespace_instruction_raises(self):
        with pytest.raises(ValidationError):
            TaskRequest(agent_type="web_development", instruction="   ")

    def test_empty_agent_type_raises(self):
        with pytest.raises(ValidationError):
            TaskRequest(agent_type="", instruction="Do something")

    def test_default_constraints(self):
        task = TaskRequest(agent_type="research", instruction="Find REST API best practices")
        assert task.constraints.max_retries == 2
        assert task.constraints.require_verification is True
        assert task.constraints.dry_run is False

    def test_task_context_defaults(self):
        task = TaskRequest(agent_type="backend", instruction="Build an API")
        assert task.context.context_items == []
        assert task.context.trust_level == "RETRIEVED"

    def test_tools_allowed_defaults_to_empty(self):
        task = TaskRequest(agent_type="security", instruction="Audit the config")
        assert task.tools_allowed == []


class TestTaskResult:
    def _make_result(self) -> TaskResult:
        return TaskResult(
            task_id="task-123",
            agent_id="agent-456",
            agent_type="web_development",
        )

    def test_initial_status_is_pending(self):
        r = self._make_result()
        assert r.status == TaskStatus.PENDING

    def test_mark_started(self):
        r = self._make_result()
        r.mark_started()
        assert r.status == TaskStatus.RUNNING
        assert r.started_at is not None

    def test_mark_completed(self):
        r = self._make_result()
        r.mark_started()
        r.mark_completed(output="Done!")
        assert r.status == TaskStatus.COMPLETED
        assert r.output == "Done!"
        assert r.progress == 1.0
        assert r.duration_seconds is not None

    def test_mark_failed(self):
        r = self._make_result()
        r.mark_started()
        r.mark_failed(error_code="MODEL_UNAVAILABLE", message="No model", stage="running")
        assert r.status == TaskStatus.FAILED
        assert len(r.errors) == 1
        assert r.errors[0].error_code == "MODEL_UNAVAILABLE"

    def test_add_error(self):
        r = self._make_result()
        r.add_error("TEST_ERROR", "Something went wrong", "test_stage")
        assert r.errors[0].error_code == "TEST_ERROR"
        assert r.errors[0].message == "Something went wrong"
        assert r.errors[0].stage == "test_stage"


class TestVerificationOutcome:
    def test_pass_verdict(self):
        outcome = VerificationOutcome(
            verdict=VerificationVerdict.PASS,
            reason="All checks passed.",
            checks=[
                VerificationCheck(
                    name="task_id_match",
                    verdict=VerificationVerdict.PASS,
                    reason="IDs match.",
                )
            ],
        )
        assert outcome.passed is True

    def test_fail_verdict(self):
        outcome = VerificationOutcome(
            verdict=VerificationVerdict.FAIL,
            reason="Check failed.",
        )
        assert outcome.passed is False

    def test_skipped_verdict_not_passed(self):
        outcome = VerificationOutcome()
        assert outcome.passed is False


class TestArtifact:
    def test_code_artifact(self):
        art = Artifact(type=ArtifactType.CODE, path="/tmp/main.py")
        assert art.type == ArtifactType.CODE
        assert not art.is_mock
        assert art.is_real()

    def test_image_artifact(self):
        art = Artifact(type=ArtifactType.IMAGE, path="/tmp/output.png", mime_type="image/png")
        assert art.type == ArtifactType.IMAGE
        assert art.mime_type == "image/png"
        assert art.is_real()

    def test_reference_artifact(self):
        art = Artifact(type=ArtifactType.REFERENCE, url="https://example.com")
        assert art.url == "https://example.com"

    def test_mock_artifact_is_flagged(self):
        art = make_mock_artifact("test label", agent_id="agent-1")
        assert art.is_mock is True
        assert art.is_real() is False
        assert art.type == ArtifactType.MOCK
        assert "MOCK" in (art.content or "")

    def test_real_artifact_not_mocked(self):
        art = Artifact(type=ArtifactType.DOCUMENT, path="/reports/result.md")
        assert art.is_mock is False
        assert art.is_real() is True


class TestAgentEvent:
    def test_create_event(self):
        event = AgentEvent.create(
            event_type=EventType.AGENT_SPAWNED,
            agent_id="agent-1",
            task_id="task-1",
            message="Agent spawned.",
        )
        assert event.event_type == EventType.AGENT_SPAWNED
        assert event.agent_id == "agent-1"
        assert event.task_id == "task-1"
        assert event.event_id  # auto UUID
        assert event.timestamp is not None

    def test_all_event_types_exist(self):
        expected = [
            "AGENT_SPAWNED", "TASK_ASSIGNED", "AGENT_RUNNING",
            "VERIFICATION_STARTED", "VERIFICATION_PASSED", "VERIFICATION_FAILED",
            "REFLECTION_STARTED", "RETRY_STARTED", "TASK_COMPLETED",
            "AGENT_TERMINATED", "AGENT_ERROR",
            "TOOL_REQUESTED", "TOOL_EXECUTED", "TOOL_DENIED", "TOOL_ERROR",
            "MEMORY_REQUESTED", "MEMORY_RETURNED", "MEMORY_NOT_FOUND",
            "MODEL_RESOLVED", "MODEL_UNAVAILABLE",
        ]
        for name in expected:
            assert hasattr(EventType, name), f"Missing EventType: {name}"
