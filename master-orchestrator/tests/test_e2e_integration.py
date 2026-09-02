import pytest
import asyncio
import uuid
import datetime
from app.core.orchestrator import MasterOrchestrator
from app.core.execution_engine import ExecutionEngine
from app.core.scheduler import Scheduler
from app.core.dispatcher import Dispatcher
from app.core.state_manager import StateManager
from app.persistence.repository import SQLiteExecutionRepository, InMemoryExecutionRepository
from app.persistence.event_store import SQLiteEventStore
from app.clients.planner_client import PlannerClient, PlannerUnavailableError
from app.clients.memory_client import MemoryClient, MemoryUnavailableError
from app.clients.specialist_client import SpecialistClient
from app.verification.result_verifier import ResultVerifier
from app.policies.failure_policy import FailureType
from app.models.execution import ExecutionStatus, Execution
from app.models.state import StepLifecycle

# TEST 1 — Planner unavailable
@pytest.mark.asyncio
async def test_planner_unavailable_fails_honestly():
    client = PlannerClient(base_url="http://127.0.0.1:9999", timeout_seconds=1.0)
    with pytest.raises(PlannerUnavailableError):
        await client.create_plan("Test user request", {}, "req-1")

# TEST 2 — Planner available (mocked / real contract check)
@pytest.mark.asyncio
async def test_planner_contract_parsing():
    class MockSuccessPlanner:
        async def create_plan(self, *args, **kwargs):
            return {
                "plan_id": "plan-101",
                "steps": [
                    {"step_id": "step-1", "specialist_id": "backend", "description": "API"},
                    {"step_id": "step-2", "specialist_id": "database", "description": "DB"}
                ],
                "dependencies": {"step-1": [], "step-2": []}
            }
        async def check_health(self): return True

    repo = InMemoryExecutionRepository()
    engine = None
    orch = MasterOrchestrator(repo, engine, MockSuccessPlanner())
    ex = await orch.create_execution("Build API")
    await orch.start_execution(ex.execution_id)
    persisted = await orch.get_execution(ex.execution_id)
    assert persisted.plan_id == "plan-101"
    assert persisted.status == ExecutionStatus.PLANNED

# TEST 3 — Memory client error handling
@pytest.mark.asyncio
async def test_memory_unavailable_fails_honestly():
    client = MemoryClient(base_url="http://127.0.0.1:9999", timeout_seconds=1.0)
    with pytest.raises(MemoryUnavailableError):
        await client.search("query", "task-1")

# TEST 4 — Specialist model unavailable produces honest failure
@pytest.mark.asyncio
async def test_specialist_model_unavailable_honest_failure():
    class ModelUnavailableSpecialist:
        async def dispatch(self, tr):
            return {
                "task_id": tr["task_id"],
                "status": "failed",
                "output": None,
                "artifacts": [],
                "errors": [{"error_code": "MODEL_UNAVAILABLE", "message": "No model configured"}]
            }
    
    dispatcher = Dispatcher(ModelUnavailableSpecialist())
    attempt = await dispatcher.dispatch("ex-1", {"step_id": "s1", "specialist_id": "backend"}, 0, {})
    assert attempt.status.value == "FAILED"
    assert attempt.failure_type == "MODEL_UNAVAILABLE"

# TEST 5 — DAG dependency: A and B execute before C
@pytest.mark.asyncio
async def test_dag_dependency_execution_order():
    execution_order_log = []
    
    class OrderTrackingSpecialist:
        async def dispatch(self, tr):
            agent = tr["agent_type"]
            execution_order_log.append(agent)
            return {
                "task_id": tr["task_id"],
                "agent_type": agent,
                "status": "completed",
                "output": f"Done {agent}",
                "artifacts": [{"type": "code", "path": f"{agent}.py"}],
                "verification": {"verdict": "PASS"}
            }

    state_mgr = StateManager()
    scheduler = Scheduler(max_concurrent_tasks=5)
    dispatcher = Dispatcher(OrderTrackingSpecialist())
    repo = InMemoryExecutionRepository()
    
    engine = ExecutionEngine(
        scheduler=scheduler,
        dispatcher=dispatcher,
        state_manager=state_mgr,
        repo=repo
    )
    
    ex = Execution(
        execution_id="exec-dag-1",
        request_id="req-1",
        user_request="test",
        created_at=datetime.datetime.utcnow().isoformat(),
        updated_at=datetime.datetime.utcnow().isoformat(),
        correlation_id="exec-dag-1"
    )
    repo.save_execution(ex)
    
    plan = {
        "plan_id": "plan-dag-1",
        "steps": [
            {"step_id": "A", "specialist_id": "database", "description": "DB"},
            {"step_id": "B", "specialist_id": "backend", "description": "Backend"},
            {"step_id": "C", "specialist_id": "testing", "description": "Test"}
        ],
        "dependencies": {
            "A": [],
            "B": [],
            "C": ["A", "B"]
        }
    }
    
    result = await engine.run("exec-dag-1", plan)
    assert result.status == ExecutionStatus.COMPLETED
    assert "database" in execution_order_log
    assert "backend" in execution_order_log
    assert "testing" in execution_order_log
    # C must be executed after both A and B
    idx_a = execution_order_log.index("database")
    idx_b = execution_order_log.index("backend")
    idx_c = execution_order_log.index("testing")
    assert idx_c > idx_a
    assert idx_c > idx_b

# TEST 6 — Parallel execution: independent steps overlap
@pytest.mark.asyncio
async def test_parallel_execution_concurrency():
    active_concurrent = 0
    max_observed_concurrent = 0
    
    class ConcurrencyTrackingSpecialist:
        async def dispatch(self, tr):
            nonlocal active_concurrent, max_observed_concurrent
            active_concurrent += 1
            if active_concurrent > max_observed_concurrent:
                max_observed_concurrent = active_concurrent
            await asyncio.sleep(0.1)  # Simulate concurrent work
            active_concurrent -= 1
            return {
                "task_id": tr["task_id"],
                "agent_type": tr["agent_type"],
                "status": "completed",
                "artifacts": [{"type": "code", "path": "test.py"}],
                "verification": {"verdict": "PASS"}
            }

    state_mgr = StateManager()
    scheduler = Scheduler(max_concurrent_tasks=5)
    dispatcher = Dispatcher(ConcurrencyTrackingSpecialist())
    repo = InMemoryExecutionRepository()
    
    engine = ExecutionEngine(
        scheduler=scheduler,
        dispatcher=dispatcher,
        state_manager=state_mgr,
        repo=repo
    )
    
    ex = Execution(
        execution_id="exec-parallel-1",
        request_id="req-p",
        user_request="test",
        created_at=datetime.datetime.utcnow().isoformat(),
        updated_at=datetime.datetime.utcnow().isoformat(),
        correlation_id="exec-parallel-1"
    )
    repo.save_execution(ex)
    
    plan = {
        "plan_id": "plan-p",
        "steps": [
            {"step_id": "step-1", "specialist_id": "backend", "description": "1"},
            {"step_id": "step-2", "specialist_id": "database", "description": "2"},
            {"step_id": "step-3", "specialist_id": "security", "description": "3"}
        ],
        "dependencies": {"step-1": [], "step-2": [], "step-3": []}
    }
    
    result = await engine.run("exec-parallel-1", plan)
    assert result.status == ExecutionStatus.COMPLETED
    assert max_observed_concurrent >= 2  # Proves concurrent scheduling

# TEST 7 — Verification failure prevents COMPLETED status
@pytest.mark.asyncio
async def test_verification_failure_prevents_completion():
    class VerificationFailingSpecialist:
        async def dispatch(self, tr):
            return {
                "task_id": tr["task_id"],
                "agent_type": tr["agent_type"],
                "status": "completed",  # Claims completed
                "artifacts": [],         # But missing required expected artifacts
                "verification": {"verdict": "FAIL", "reason": "Missing artifacts"}
            }

    state_mgr = StateManager()
    scheduler = Scheduler(max_concurrent_tasks=2)
    dispatcher = Dispatcher(VerificationFailingSpecialist())
    repo = InMemoryExecutionRepository()
    
    engine = ExecutionEngine(
        scheduler=scheduler,
        dispatcher=dispatcher,
        state_manager=state_mgr,
        repo=repo
    )
    
    ex = Execution(
        execution_id="exec-vfail",
        request_id="req-vf",
        user_request="test",
        created_at=datetime.datetime.utcnow().isoformat(),
        updated_at=datetime.datetime.utcnow().isoformat(),
        correlation_id="exec-vfail"
    )
    repo.save_execution(ex)
    
    plan = {
        "plan_id": "plan-vf",
        "steps": [
            {
                "step_id": "s1",
                "specialist_id": "backend",
                "description": "API",
                "expected_outputs": ["code.py"],
                "failure_policy": {"max_retries": 0}
            }
        ],
        "dependencies": {"s1": []}
    }
    
    result = await engine.run("exec-vfail", plan)
    assert result.status == ExecutionStatus.FAILED
    assert "s1" not in ex.completed_steps
    assert "s1" in ex.failed_steps

# TEST 8 — Retry mechanism creates new attempt
@pytest.mark.asyncio
async def test_retry_creates_new_attempt():
    call_count = 0
    class RetryingSpecialist:
        async def dispatch(self, tr):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "task_id": tr["task_id"],
                    "agent_type": tr.get("agent_type", "backend"),
                    "status": "failed",
                    "errors": [{"error_code": "TIMEOUT", "message": "Call timed out"}]
                }
            return {
                "task_id": tr["task_id"],
                "agent_type": tr.get("agent_type", "backend"),
                "status": "completed",
                "artifacts": [{"type": "code", "path": "ok.py"}],
                "verification": {"verdict": "PASS"}
            }


    state_mgr = StateManager()
    scheduler = Scheduler(max_concurrent_tasks=2)
    dispatcher = Dispatcher(RetryingSpecialist())
    repo = InMemoryExecutionRepository()
    
    engine = ExecutionEngine(
        scheduler=scheduler,
        dispatcher=dispatcher,
        state_manager=state_mgr,
        repo=repo
    )
    
    ex = Execution(
        execution_id="exec-retry",
        request_id="req-r",
        user_request="test",
        created_at=datetime.datetime.utcnow().isoformat(),
        updated_at=datetime.datetime.utcnow().isoformat(),
        correlation_id="exec-retry"
    )
    repo.save_execution(ex)
    
    plan = {
        "plan_id": "plan-retry",
        "steps": [
            {
                "step_id": "s-retry",
                "specialist_id": "backend",
                "description": "API",
                "failure_policy": {"max_retries": 2}
            }
        ],
        "dependencies": {"s-retry": []}
    }
    
    result = await engine.run("exec-retry", plan)
    assert result.status == ExecutionStatus.COMPLETED
    assert call_count == 2
    attempts = repo.get_attempts("exec-retry")
    assert len(attempts) == 2
    assert attempts[0].attempt_number == 0
    assert attempts[1].attempt_number == 1

# TEST 9 — Idempotency key format
@pytest.mark.asyncio
async def test_idempotency_keys_unique_per_attempt():
    class DummyClient:
        async def dispatch(self, tr): return {"task_id": tr["task_id"], "status": "completed", "verification": {"verdict": "PASS"}}
    dispatcher = Dispatcher(DummyClient())
    
    att1 = await dispatcher.dispatch("exec-idem", {"step_id": "step-1"}, 0, {})
    att2 = await dispatcher.dispatch("exec-idem", {"step_id": "step-1"}, 1, {})
    
    assert att1.idempotency_key.startswith("exec-idem:step-1:")
    assert att2.idempotency_key.startswith("exec-idem:step-1:")
    assert att1.idempotency_key != att2.idempotency_key

# TEST 10 — Persistence across restart (SQLite)
def test_sqlite_persistence_across_restart(tmp_path):
    db_file = str(tmp_path / "test_pers.db")
    
    # 1. First instance writes
    repo1 = SQLiteExecutionRepository(db_file)
    event_store1 = SQLiteEventStore(db_file)
    
    ex = Execution(
        execution_id="exec-persist-1",
        request_id="req-1",
        user_request="Persist this",
        status=ExecutionStatus.RUNNING,
        created_at=datetime.datetime.utcnow().isoformat(),
        updated_at=datetime.datetime.utcnow().isoformat(),
        correlation_id="exec-persist-1"
    )
    repo1.save_execution(ex)
    
    # 2. Simulate restart with new repository instance pointing to same file
    repo2 = SQLiteExecutionRepository(db_file)
    loaded = repo2.get_execution("exec-persist-1")
    assert loaded is not None
    assert loaded.execution_id == "exec-persist-1"
    assert loaded.user_request == "Persist this"
