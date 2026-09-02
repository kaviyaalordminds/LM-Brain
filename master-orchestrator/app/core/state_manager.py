import threading
import datetime
from typing import Dict, List, Optional, Any
from app.models.state import (
    LEGAL_STEP_TRANSITIONS,
    LEGAL_EXECUTION_TRANSITIONS,
    StepLifecycle,
    ExecutionStatus,
)

class IllegalTransitionError(Exception):
    pass

class StateTransitionRecord:
    def __init__(
        self,
        entity_id: str,
        old_state: Any,
        new_state: Any,
        timestamp: Optional[str] = None,
        correlation_id: str = "",
        entity_type: str = "step"
    ):
        self.entity_id = entity_id
        self.old_state = old_state
        self.new_state = new_state
        self.timestamp = timestamp or datetime.datetime.utcnow().isoformat()
        self.correlation_id = correlation_id
        self.entity_type = entity_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "old_state": str(self.old_state),
            "new_state": str(self.new_state),
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "entity_type": self.entity_type,
        }

class StateManager:
    """
    Deterministic State Machine Manager.
    Enforces legal state transitions for both workflows (ExecutionStatus)
    and individual steps (StepLifecycle). Rejects illegal transitions.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.states: Dict[str, StepLifecycle] = {}
        self.execution_states: Dict[str, ExecutionStatus] = {}
        self.history: List[StateTransitionRecord] = []

    # Step transitions
    def transition_step(
        self,
        execution_id: str,
        step_id: str,
        new_state: StepLifecycle,
        correlation_id: str = ""
    ) -> StateTransitionRecord:
        with self._lock:
            key = f"{execution_id}:{step_id}"
            current_state = self.states.get(key, StepLifecycle.PENDING)

            if new_state == current_state:
                # Idempotent no-op
                return StateTransitionRecord(key, current_state, new_state, correlation_id=correlation_id, entity_type="step")

            legal_next = LEGAL_STEP_TRANSITIONS.get(current_state, set())
            if new_state not in legal_next:
                raise IllegalTransitionError(
                    f"Illegal step transition for [{key}]: Cannot transition from {current_state} to {new_state}. "
                    f"Legal transitions: {[s.value for s in legal_next]}"
                )

            self.states[key] = new_state
            record = StateTransitionRecord(
                key,
                current_state,
                new_state,
                correlation_id=correlation_id,
                entity_type="step"
            )
            self.history.append(record)
            return record

    # Backwards compatibility
    def transition(self, execution_id: str, step_id: str, new_state: StepLifecycle) -> StateTransitionRecord:
        return self.transition_step(execution_id, step_id, new_state)

    # Execution transitions
    def transition_execution(
        self,
        execution_id: str,
        new_status: ExecutionStatus,
        current_status: Optional[ExecutionStatus] = None,
        correlation_id: str = ""
    ) -> StateTransitionRecord:
        with self._lock:
            active_status = current_status or self.execution_states.get(execution_id, ExecutionStatus.CREATED)

            if new_status == active_status:
                return StateTransitionRecord(
                    execution_id, active_status, new_status, correlation_id=correlation_id, entity_type="execution"
                )

            legal_next = LEGAL_EXECUTION_TRANSITIONS.get(active_status, set())
            if new_status not in legal_next:
                raise IllegalTransitionError(
                    f"Illegal execution transition for [{execution_id}]: Cannot transition from {active_status} to {new_status}. "
                    f"Legal transitions: {[s.value for s in legal_next]}"
                )

            self.execution_states[execution_id] = new_status
            record = StateTransitionRecord(
                execution_id,
                active_status,
                new_status,
                correlation_id=correlation_id,
                entity_type="execution"
            )
            self.history.append(record)
            return record

    def get_step_state(self, execution_id: str, step_id: str) -> StepLifecycle:
        with self._lock:
            return self.states.get(f"{execution_id}:{step_id}", StepLifecycle.PENDING)

    def get_execution_state(self, execution_id: str) -> ExecutionStatus:
        with self._lock:
            return self.execution_states.get(execution_id, ExecutionStatus.CREATED)

    def get_history_for_execution(self, execution_id: str) -> List[StateTransitionRecord]:
        with self._lock:
            return [r for r in self.history if execution_id in r.entity_id]

