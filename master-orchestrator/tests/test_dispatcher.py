"""
Tests for Dispatcher — deterministic mapping, attempt creation, idempotency key generation.
"""
from __future__ import annotations

import pytest
from app.core.dispatcher import Dispatcher
from app.models.dispatch import AttemptStatus

class MockSpecialistClient:
    def __init__(self, return_status="completed"):
        self.dispatched_requests = []
        self.return_status = return_status

    async def dispatch(self, task_request: dict) -> dict:
        self.dispatched_requests.append(task_request)
        return {
            "result_id": "res-123",
            "task_id": task_request.get("task_id"),
            "agent_type": task_request.get("agent_type"),
            "status": self.return_status,
            "output": "Execution completed",
            "artifacts": [{"artifact_id": "art-1", "type": "code"}],
            "verification": {"verdict": "PASS"},
            "errors": []
        }

@pytest.mark.asyncio
async def test_dispatcher_maps_plan_step_deterministically():
    mock_client = MockSpecialistClient()
    dispatcher = Dispatcher(mock_client)
    
    step = {
        "step_id": "step-backend-1",
        "title": "Build REST API",
        "description": "Implement authentication and CRUD endpoints",
        "specialist_id": "backend",
        "expected_outputs": ["backend code", "API documentation"],
        "verification_criteria": ["All routes pass tests"],
        "failure_policy": {"max_retries": 2}
    }
    
    mem_ctx = {"items": [{"title": "API Guide"}], "trust_level": "RETRIEVED"}
    
    attempt = await dispatcher.dispatch(
        execution_id="exec-001",
        step=step,
        attempt_number=0,
        memory_context=mem_ctx,
        plan_id="plan-999",
        plan_version=1
    )
    
    assert attempt.execution_id == "exec-001"
    assert attempt.step_id == "step-backend-1"
    assert attempt.attempt_number == 0
    assert attempt.status == AttemptStatus.COMPLETED
    assert attempt.idempotency_key == f"exec-001:step-backend-1:{attempt.attempt_number}"

    
    # Inspect mapped task_request
    assert len(mock_client.dispatched_requests) == 1
    tr = mock_client.dispatched_requests[0]
    assert tr["agent_type"] == "backend"
    assert "Build REST API" in tr["instruction"]
    assert "code" in tr["expected_output"]["artifact_types"]
    assert tr["metadata"]["execution_id"] == "exec-001"
    assert tr["metadata"]["plan_id"] == "plan-999"

@pytest.mark.asyncio
async def test_dispatcher_records_failure_on_specialist_error():
    class FailingClient:
        async def dispatch(self, task_request: dict) -> dict:
            return {
                "task_id": task_request.get("task_id"),
                "status": "failed",
                "errors": [{"error_code": "MODEL_UNAVAILABLE", "message": "No model configured"}]
            }
            
    dispatcher = Dispatcher(FailingClient())
    step = {"step_id": "step-fail", "specialist_id": "ai_ml", "description": "Run AI classification"}
    attempt = await dispatcher.dispatch("exec-002", step, 0, {})
    
    assert attempt.status == AttemptStatus.FAILED
    assert attempt.failure_type == "MODEL_UNAVAILABLE"
    assert "No model configured" in attempt.error

