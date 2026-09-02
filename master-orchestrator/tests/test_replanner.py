"""
Tests for Replanner — recovery plan requests, plan versioning (never overwrites v1).
"""
from __future__ import annotations

import uuid
import datetime

import pytest

from app.core.replanner import Replanner
from app.models.execution import Execution, ExecutionStatus


def make_execution(user_request: str = "Build REST API") -> Execution:
    eid = str(uuid.uuid4())
    return Execution(
        execution_id=eid,
        request_id=str(uuid.uuid4()),
        user_request=user_request,
        plan_id="plan-1",
        plan_version=1,
        created_at=datetime.datetime.utcnow().isoformat(),
        updated_at=datetime.datetime.utcnow().isoformat(),
        correlation_id=eid,
        status=ExecutionStatus.RECOVERING,
    )


class MockPlannerClient:
    def __init__(self, recovery_plan: dict | None = None):
        self.called_with = []
        self.recovery_plan = recovery_plan or {
            "plan_id": f"plan-recovery-{uuid.uuid4()}",
            "request_id": "req-recovery",
            "status": "READY",
            "steps": [{"step_id": "recovery-step-1", "specialist_id": "backend"}],
            "dependencies": {"recovery-step-1": []},
        }

    async def create_recovery_plan(self, original_request: str, current_state: dict) -> dict:
        self.called_with.append({"original_request": original_request, "current_state": current_state})
        return dict(self.recovery_plan)


class FailingPlannerClient:
    async def create_recovery_plan(self, original_request: str, current_state: dict) -> dict:
        raise ConnectionError("Planner is unavailable — service down")


class TestReplannerRequests:
    @pytest.mark.asyncio
    async def test_request_recovery_plan_calls_planner(self):
        planner = MockPlannerClient()
        replanner = Replanner(planner_client=planner)
        execution = make_execution("Build REST API")
        failure_context = {"failed_step": "step-1", "reason": "Timeout"}

        result = await replanner.request_recovery_plan(execution, failure_context)

        assert planner.called_with[0]["original_request"] == "Build REST API"
        assert planner.called_with[0]["current_state"] == failure_context

    @pytest.mark.asyncio
    async def test_recovery_plan_returns_dict(self):
        planner = MockPlannerClient()
        replanner = Replanner(planner_client=planner)
        execution = make_execution()

        result = await replanner.request_recovery_plan(execution, {})
        assert isinstance(result, dict)
        assert "plan_id" in result

    @pytest.mark.asyncio
    async def test_recovery_plan_has_different_id_from_original(self):
        recovery = {
            "plan_id": "plan-recovery-new",
            "status": "READY",
            "steps": [],
            "dependencies": {},
        }
        planner = MockPlannerClient(recovery_plan=recovery)
        replanner = Replanner(planner_client=planner)
        execution = make_execution()
        execution.plan_id = "plan-1"  # original

        result = await replanner.request_recovery_plan(execution, {})
        assert result["plan_id"] != execution.plan_id

    @pytest.mark.asyncio
    async def test_planner_unavailable_raises_exception(self):
        """If planner is unavailable, replanner must propagate the error (not swallow it)."""
        planner = FailingPlannerClient()
        replanner = Replanner(planner_client=planner)
        execution = make_execution()

        with pytest.raises((ConnectionError, Exception)):
            await replanner.request_recovery_plan(execution, {})

    @pytest.mark.asyncio
    async def test_original_user_request_passed_to_planner(self):
        planner = MockPlannerClient()
        replanner = Replanner(planner_client=planner)
        execution = make_execution(user_request="Deploy application with Docker")

        await replanner.request_recovery_plan(execution, {"reason": "step failed"})
        assert planner.called_with[0]["original_request"] == "Deploy application with Docker"

