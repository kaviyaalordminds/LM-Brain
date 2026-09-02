import pytest
from app.core.scheduler import Scheduler
from app.models.state import StepLifecycle

def test_dag_multi_parent_gating_and_isolation():
    """
    Graph:
    A ──┐
        ├──→ C ──→ D
    B ──┘
    E (independent)
    """
    scheduler = Scheduler(max_concurrent_tasks=5)
    exec_id = "exec-dag-01"

    dependencies = {
        "A": [],
        "B": [],
        "C": ["A", "B"],
        "D": ["C"],
        "E": []
    }

    step_states = {
        f"{exec_id}:A": StepLifecycle.PENDING,
        f"{exec_id}:B": StepLifecycle.PENDING,
        f"{exec_id}:C": StepLifecycle.PENDING,
        f"{exec_id}:D": StepLifecycle.PENDING,
        f"{exec_id}:E": StepLifecycle.PENDING,
    }

    # Initial tick: A, B, E have 0 dependencies, so they should be READY
    ready, blocked = scheduler.tick(exec_id, step_states, dependencies)
    assert set(ready) == {"A", "B", "E"}
    assert blocked == []

    # Suppose A and B complete, but E is still running
    step_states[f"{exec_id}:A"] = StepLifecycle.COMPLETED
    step_states[f"{exec_id}:B"] = StepLifecycle.COMPLETED
    step_states[f"{exec_id}:E"] = StepLifecycle.RUNNING

    ready, blocked = scheduler.tick(exec_id, step_states, dependencies)
    assert ready == ["C"]  # C is now unlocked
    assert blocked == []

    # Suppose instead A FAILED, while B completed and E completed
    step_states_failure = {
        f"{exec_id}:A": StepLifecycle.FAILED,
        f"{exec_id}:B": StepLifecycle.COMPLETED,
        f"{exec_id}:C": StepLifecycle.PENDING,
        f"{exec_id}:D": StepLifecycle.PENDING,
        f"{exec_id}:E": StepLifecycle.COMPLETED,
    }

    ready, blocked = scheduler.tick(exec_id, step_states_failure, dependencies)
    assert ready == []  # Neither C nor D can run
    assert "C" in blocked  # C is blocked because A failed!

def test_bounded_concurrency():
    scheduler = Scheduler(max_concurrent_tasks=2)
    exec_id = "exec-bound"

    assert scheduler.register_in_flight(exec_id, "step-1") is True
    assert scheduler.register_in_flight(exec_id, "step-2") is True
    # Exceeding limit of 2:
    assert scheduler.register_in_flight(exec_id, "step-3") is False

    # Once step-1 finishes:
    scheduler.unregister_in_flight(exec_id, "step-1")
    assert scheduler.register_in_flight(exec_id, "step-3") is True
