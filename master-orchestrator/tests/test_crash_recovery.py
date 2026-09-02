import pytest
import datetime
import asyncio
from app.persistence.repository import SQLiteExecutionRepository
from app.models.execution import Execution, ExecutionStatus, ExecutionPhase
from app.core.orchestrator import MasterOrchestrator
from app.core.execution_engine import ExecutionEngine
from app.core.state_manager import StateManager
from app.core.scheduler import Scheduler
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_crash_recovery_preserves_completed_steps(tmp_path):
    db_file = str(tmp_path / "test_crash.db")
    repo = SQLiteExecutionRepository(db_path=db_file)
    state_manager = StateManager()
    scheduler = Scheduler()
    engine = ExecutionEngine(
        state_manager=state_manager,
        scheduler=scheduler,
        dispatcher=AsyncMock(),
        verifier=AsyncMock(),
        repo=repo
    )
    orchestrator = MasterOrchestrator(repo=repo, engine=engine, planner=AsyncMock())

    # Create an interrupted execution in SQLite
    exec_id = "exec-crash-01"
    plan_id = "plan-crash-01"
    now = datetime.datetime.utcnow().isoformat()

    plan_data = {
        "plan_id": plan_id,
        "plan_version": 1,
        "steps": [
            {"step_id": "step-1", "title": "Step 1", "dependencies": []},
            {"step_id": "step-2", "title": "Step 2", "dependencies": ["step-1"]},
        ],
        "dependencies": {"step-1": [], "step-2": ["step-1"]}
    }
    repo.save_plan_version(plan_data)

    interrupted_exec = Execution(
        execution_id=exec_id,
        request_id="req-crash",
        user_request="Simulate interrupted task",
        plan_id=plan_id,
        plan_version=1,
        status=ExecutionStatus.RUNNING,
        phase=ExecutionPhase.DISPATCHING,
        created_at=now,
        updated_at=now,
        completed_steps=["step-1"],
        running_steps=["step-2"],
        pending_steps=[],
        correlation_id=exec_id
    )
    repo.save_execution(interrupted_exec)

    # Trigger crash recovery
    recovered_ids = await orchestrator.recover_interrupted_workflows()
    assert exec_id in recovered_ids

    # Step-1 must still be COMPLETED (never re-executed!)
    reconstructed = repo.get_execution(exec_id)
    assert reconstructed.status == ExecutionStatus.RUNNING
    assert "step-1" in reconstructed.completed_steps
    assert "step-2" in reconstructed.pending_steps
