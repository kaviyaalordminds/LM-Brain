import threading
from app.models.state import LEGAL_TRANSITIONS, StepLifecycle
from typing import Dict, Tuple

class IllegalTransitionError(Exception): pass

class StateTransitionRecord:
    def __init__(self, old_state: StepLifecycle, new_state: StepLifecycle):
        self.old_state = old_state
        self.new_state = new_state

class StateManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.states: Dict[str, StepLifecycle] = {}

    def transition(self, execution_id: str, step_id: str, new_state: StepLifecycle) -> StateTransitionRecord:
        with self._lock:
            key = f"{execution_id}:{step_id}"
            current_state = self.states.get(key, StepLifecycle.PENDING)
            
            if new_state not in LEGAL_TRANSITIONS.get(current_state, set()) and new_state != current_state:
                raise IllegalTransitionError(f"Cannot transition from {current_state} to {new_state}")
            
            self.states[key] = new_state
            return StateTransitionRecord(current_state, new_state)
