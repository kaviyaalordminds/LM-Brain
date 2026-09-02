"""
Tests for Control API — pause, resume, cancel behavior with real MasterOrchestrator.
"""
from __future__ import annotations

import pytest
from app.core.orchestrator import MasterOrchestrator
from app.models.execution import ExecutionStatus
from app.persistence.repository import InMemoryExecutionRepository

class MockEngine:
    class MockScheduler:
        def cancel(self, execution_id): pass
    scheduler = MockScheduler()
    async def run(self, execution_id, plan): pass

class MockPlanner:
    async def create_plan(self, *args, **kwargs): return {"plan_id": "p1", "steps": []}
    async def check_health(self): return True

@pytest.mark.asyncio
async def test_control_api_pause_resume_cancel():
    repo = InMemoryExecutionRepository()
    orchestrator = MasterOrchestrator(repo=repo, engine=MockEngine(), planner=MockPlanner())
    
    # 1. Create execution
    exec_record = await orchestrator.create_execution("Test user request")
    assert exec_record.status == ExecutionStatus.CREATED
    
    # 2. Pause
    paused = await orchestrator.pause(exec_record.execution_id)
    assert paused.status == ExecutionStatus.PAUSED
    persisted = await orchestrator.get_execution(exec_record.execution_id)
    assert persisted.status == ExecutionStatus.PAUSED
    
    # 3. Resume
    resumed = await orchestrator.resume(exec_record.execution_id)
    assert resumed.status == ExecutionStatus.RUNNING
    persisted = await orchestrator.get_execution(exec_record.execution_id)
    assert persisted.status == ExecutionStatus.RUNNING
    
    # 4. Cancel
    cancelled = await orchestrator.cancel(exec_record.execution_id)
    assert cancelled.status == ExecutionStatus.CANCELLED
    persisted = await orchestrator.get_execution(exec_record.execution_id)
    assert persisted.status == ExecutionStatus.CANCELLED

