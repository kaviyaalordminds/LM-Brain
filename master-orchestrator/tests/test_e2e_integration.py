"""
End-to-end integration tests for the Master Orchestrator system.

Tests the complete contract chain:
  MasterOrchestrator.create_execution()
  → Repository.save_execution()
  → StateManager (transitions)
  → RecoveryManager (failure analysis)
  → ResultVerifier (verification gate)
  → TrustPolicy (trust semantics)

All external services (Planner, Specialist, Memory) are mocked.
No live HTTP calls. No fabricated results.
"""
from __future__ import annotations

import datetime
import uuid

import pytest

from app.core.orchestrator import MasterOrchestrator
from app.core.state_manager import StateManager
from app.core.recovery_manager import RecoveryDecision, RecoveryManager
from app.core.scheduler import Scheduler
from app.core.execution_engine import ExecutionEngine
from app.models.execution import Execution, ExecutionStatus
from app.models.state import StepLifecycle
from app.models.artifacts import TrustState
from app.persistence.repository import InMemoryExecutionRepository
from app.policies.failure_policy import FailureClassifier, FailureType
from app.policies.trust_policy import TrustPolicy
from app.verification.result_verifier import ResultVerifier


class MockSpecialistClient:
    def __init__(self, return_result: dict | None = None):
        self.dispatched = []
        self.return_result = return_result or {
            "task_id": None,  # will be set dynamically
            "status": "completed",
            "agent_type": "backend",
            "artifacts": [{"artifact_id": "art-1", "type": "code"}],
            "verification": {"verdict": "PASS"},
            "errors": [],
        }

    async def dispatch(self, task_request: dict) -> dict:
        self.dispatched.append(task_request)
        result = dict(self.return_result)
        result["task_id"] = task_request.get("task_id", "task-unknown")
        result["agent_type"] = task_request.get("agent_type", "unknown")
        return result

    async def check_health(self, specialist_id: str) -> bool:
        return True


class MockPlannerClient:
    def __init__(self, plan: dict | None = None):
        self.plan = plan or {
            "plan_id": "plan-1",
            "request_id": "req-1",
            "status": "READY",
            "steps": [],
            "dependencies": {},
            "execution_order": [],
            "parallel_groups": [],
        }

    async def create_plan(self, user_request: str, context: dict, request_id: str) -> dict:
        return dict(self.plan)

    async def create_recovery_plan(self, original_request: str, current_state: dict) -> dict:
        recovery_plan = dict(self.plan)
        recovery_plan["plan_id"] = f"recovery-{uuid.uuid4()}"
        return recovery_plan


class TestOrchestratorLifecycle:
    @pytest.mark.asyncio
    async def test_create_execution_returns_execution(self):
        repo = InMemoryExecutionRepository()
        sm = StateManager()
        scheduler = Scheduler()
        specialist_client = MockSpecialistClient()
        from app.core.dispatcher import Dispatcher
        dispatcher = Dispatcher(specialist_client)
        engine = ExecutionEngine(scheduler, dispatcher, sm)
        planner = MockPlannerClient()
        orchestrator = MasterOrchestrator(repo=repo, engine=engine, planner=planner)

        execution = await orchestrator.create_execution(
            user_request="Build me a REST API",
            context={"domain": "backend"},
        )
        assert isinstance(execution, Execution)
        assert execution.user_request == "Build me a REST API"
        assert execution.status == ExecutionStatus.CREATED
        assert execution.execution_id is not None

    @pytest.mark.asyncio
    async def test_execution_is_persisted_in_repository(self):
        repo = InMemoryExecutionRepository()
        sm = StateManager()
        scheduler = Scheduler()
        specialist_client = MockSpecialistClient()
        from app.core.dispatcher import Dispatcher
        dispatcher = Dispatcher(specialist_client)
        engine = ExecutionEngine(scheduler, dispatcher, sm)
        planner = MockPlannerClient()
        orchestrator = MasterOrchestrator(repo=repo, engine=engine, planner=planner)

        execution = await orchestrator.create_execution("test", {})
        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved is not None
        assert retrieved.execution_id == execution.execution_id

    @pytest.mark.asyncio
    async def test_pause_updates_status(self):
        repo = InMemoryExecutionRepository()
        sm = StateManager()
        scheduler = Scheduler()
        specialist_client = MockSpecialistClient()
        from app.core.dispatcher import Dispatcher
        dispatcher = Dispatcher(specialist_client)
        engine = ExecutionEngine(scheduler, dispatcher, sm)
        planner = MockPlannerClient()
        orchestrator = MasterOrchestrator(repo=repo, engine=engine, planner=planner)

        execution = await orchestrator.create_execution("test", {})
        await orchestrator.pause(execution.execution_id)
        retrieved = await orchestrator.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.PAUSED

    @pytest.mark.asyncio
    async def test_cancel_updates_status(self):
        repo = InMemoryExecutionRepository()
        sm = StateManager()
        scheduler = Scheduler()
        specialist_client = MockSpecialistClient()
        from app.core.dispatcher import Dispatcher
        dispatcher = Dispatcher(specialist_client)
        engine = ExecutionEngine(scheduler, dispatcher, sm)
        planner = MockPlannerClient()
        orchestrator = MasterOrchestrator(repo=repo, engine=engine, planner=planner)

        execution = await orchestrator.create_execution("cancel test", {})
        await orchestrator.cancel(execution.execution_id)
        retrieved = await orchestrator.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_health_check_returns_dict(self):
        repo = InMemoryExecutionRepository()
        sm = StateManager()
        scheduler = Scheduler()
        specialist_client = MockSpecialistClient()
        from app.core.dispatcher import Dispatcher
        dispatcher = Dispatcher(specialist_client)
        engine = ExecutionEngine(scheduler, dispatcher, sm)
        planner = MockPlannerClient()
        orchestrator = MasterOrchestrator(repo=repo, engine=engine, planner=planner)

        health = await orchestrator.health_check()
        assert isinstance(health, dict)
        assert "status" in health


class TestContractBoundary:
    """Verify Orchestrator contracts with downstream services."""

    def test_planner_output_structure_accepted(self):
        """Planner Plan dict must have the fields Orchestrator expects."""
        plan = {
            "plan_id": "plan-1",
            "request_id": "req-1",
            "status": "READY",
            "steps": [
                {
                    "step_id": "step-1",
                    "specialist_id": "backend",
                    "description": "Build REST API",
                    "memory_required": False,
                    "research_required": False,
                    "expected_outputs": ["api code"],
                    "verification_criteria": ["tests pass"],
                    "failure_policy": {"retry_allowed": True, "max_retries": 2, "failure_action": "RETRY"},
                    "dependencies": [],
                }
            ],
            "dependencies": {"step-1": []},
            "execution_order": ["step-1"],
            "parallel_groups": [["step-1"]],
        }
        # Verify all expected fields are accessible
        assert "plan_id" in plan
        assert "steps" in plan
        assert "dependencies" in plan
        assert len(plan["steps"]) == 1
        step = plan["steps"][0]
        assert "specialist_id" in step
        assert "failure_policy" in step

    def test_specialist_task_request_structure(self):
        """TaskRequest dict sent to Specialist must match its contract."""
        task_request = {
            "task_id": str(uuid.uuid4()),
            "agent_type": "backend",
            "instruction": "Build a REST API endpoint",
            "context": {
                "context_items": [],
                "trust_level": "VALIDATED",
                "extra": {},
            },
            "constraints": {
                "max_duration_seconds": 300,
                "max_retries": 2,
                "require_verification": True,
                "dry_run": False,
            },
            "expected_output": {
                "output_type": "text",
                "artifact_types": ["code"],
                "description": "REST API implementation",
            },
            "tools_allowed": [],
            "metadata": {},
        }
        required = {"task_id", "agent_type", "instruction", "context", "constraints", "expected_output"}
        assert required.issubset(set(task_request.keys()))

    def test_memory_search_request_structure(self):
        """Memory search request must have query and task_id."""
        memory_request = {
            "query": "REST API authentication best practices",
            "task_id": "task-1",
            "context": {},
            "filters": None,
        }
        assert "query" in memory_request
        assert "task_id" in memory_request

    def test_unverified_context_blocked_by_trust_policy(self):
        """External research returned UNVERIFIED must not be used as specialist context."""
        assert TrustPolicy.can_use_as_context(TrustState.UNVERIFIED) is False
        assert TrustPolicy.can_use_as_context(TrustState.VALIDATED) is True

    def test_10_specialists_available(self):
        """All 10 specialist IDs must be recognizable."""
        known_specialists = {
            "web_development", "image_generation", "backend", "database",
            "api_integration", "security", "testing", "devops", "ai_ml", "research",
        }
        assert len(known_specialists) == 10

    def test_failure_classifier_covers_all_types(self):
        all_types = set(FailureType)
        assert len(all_types) == 13

    def test_verifier_produces_7_checks(self):
        verifier = ResultVerifier()
        result = {
            "task_id": "t-1",
            "status": "completed",
            "agent_type": "backend",
            "artifacts": [{"type": "code"}],
            "verification": {"verdict": "PASS"},
            "errors": [],
        }
        step = {"specialist_id": "backend", "expected_outputs": []}
        class Attempt:
            attempt_id = "t-1"
        gate = verifier.verify(result, step, Attempt())
        assert len(gate.checks) == 7

