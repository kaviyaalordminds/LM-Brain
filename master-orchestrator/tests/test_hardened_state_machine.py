import pytest
from app.models.state import (
    StepLifecycle,
    ExecutionStatus,
    LEGAL_STEP_TRANSITIONS,
    LEGAL_EXECUTION_TRANSITIONS,
)
from app.core.state_manager import StateManager, IllegalTransitionError

def test_legal_execution_transitions():
    sm = StateManager()
    exec_id = "exec-test-01"

    # CREATED -> PLANNING -> PLANNED -> RUNNING -> COMPLETED
    sm.transition_execution(exec_id, ExecutionStatus.PLANNING, current_status=ExecutionStatus.CREATED)
    assert sm.get_execution_state(exec_id) == ExecutionStatus.PLANNING

    sm.transition_execution(exec_id, ExecutionStatus.PLANNED)
    assert sm.get_execution_state(exec_id) == ExecutionStatus.PLANNED

    sm.transition_execution(exec_id, ExecutionStatus.RUNNING)
    assert sm.get_execution_state(exec_id) == ExecutionStatus.RUNNING

    sm.transition_execution(exec_id, ExecutionStatus.COMPLETED)
    assert sm.get_execution_state(exec_id) == ExecutionStatus.COMPLETED

def test_illegal_execution_transitions_rejected():
    sm = StateManager()
    exec_id = "exec-test-illegal"

    # COMPLETED -> RUNNING must be rejected!
    sm.transition_execution(exec_id, ExecutionStatus.COMPLETED, current_status=ExecutionStatus.RUNNING)
    with pytest.raises(IllegalTransitionError) as exc_info:
        sm.transition_execution(exec_id, ExecutionStatus.RUNNING)
    assert "Cannot transition from ExecutionStatus.COMPLETED to ExecutionStatus.RUNNING" in str(exc_info.value)

    # CANCELLED -> RUNNING must be rejected!
    exec_cancel = "exec-cancel"
    sm.transition_execution(exec_cancel, ExecutionStatus.CANCELLED, current_status=ExecutionStatus.CREATED)
    with pytest.raises(IllegalTransitionError):
        sm.transition_execution(exec_cancel, ExecutionStatus.RUNNING)

def test_step_lifecycle_transitions():
    sm = StateManager()
    exec_id = "exec-step-01"
    step_id = "step-sec"

    # PENDING -> READY -> QUEUED -> DISPATCHED -> RUNNING -> VERIFYING -> COMPLETED
    sm.transition_step(exec_id, step_id, StepLifecycle.READY)
    sm.transition_step(exec_id, step_id, StepLifecycle.QUEUED)
    sm.transition_step(exec_id, step_id, StepLifecycle.DISPATCHED)
    sm.transition_step(exec_id, step_id, StepLifecycle.RUNNING)
    sm.transition_step(exec_id, step_id, StepLifecycle.VERIFYING)
    sm.transition_step(exec_id, step_id, StepLifecycle.COMPLETED)
    assert sm.get_step_state(exec_id, step_id) == StepLifecycle.COMPLETED

    # COMPLETED -> RUNNING must be rejected!
    with pytest.raises(IllegalTransitionError):
        sm.transition_step(exec_id, step_id, StepLifecycle.RUNNING)
