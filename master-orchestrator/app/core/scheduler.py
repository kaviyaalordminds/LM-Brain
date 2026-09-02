import threading
from typing import List, Dict, Set, Tuple
from app.models.state import StepLifecycle

class Scheduler:
    """
    Thread-safe DAG Scheduler with bounded concurrency,
    multi-parent dependency gating, and failure isolation.
    """

    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self._lock = threading.RLock()
        self.in_flight: Set[str] = set()

    def tick(
        self,
        execution_id: str,
        step_states: Dict[str, StepLifecycle],
        plan_dependencies: Dict[str, List[str]]
    ) -> Tuple[List[str], List[str]]:
        """
        Evaluate DAG dependencies.
        Returns:
            (ready_queue, blocked_queue)
            ready_queue: steps whose dependencies are ALL COMPLETED and state is PENDING/READY.
            blocked_queue: steps whose dependencies have permanently FAILED or are BLOCKED.
        """
        with self._lock:
            ready_queue: List[str] = []
            blocked_queue: List[str] = []

            for step_id, deps in plan_dependencies.items():
                state = step_states.get(f"{execution_id}:{step_id}", StepLifecycle.PENDING)

                # Only evaluate steps not yet running, completed, or terminal
                if state in (StepLifecycle.PENDING, StepLifecycle.READY):
                    # Check dependency statuses
                    all_deps_completed = True
                    has_failed_dep = False

                    for dep in deps:
                        dep_state = step_states.get(f"{execution_id}:{dep}", StepLifecycle.PENDING)
                        if dep_state != StepLifecycle.COMPLETED:
                            all_deps_completed = False
                        if dep_state in (StepLifecycle.FAILED, StepLifecycle.BLOCKED):
                            has_failed_dep = True

                    if all_deps_completed:
                        ready_queue.append(step_id)
                    elif has_failed_dep:
                        blocked_queue.append(step_id)

            return ready_queue, blocked_queue

    def register_in_flight(self, execution_id: str, step_id: str) -> bool:
        with self._lock:
            key = f"{execution_id}:{step_id}"
            if key in self.in_flight:
                return False  # Already in flight, prevent duplicate dispatch
            if len(self.in_flight) >= self.max_concurrent_tasks:
                return False  # Bounded concurrency reached
            self.in_flight.add(key)
            return True

    def unregister_in_flight(self, execution_id: str, step_id: str) -> None:
        with self._lock:
            key = f"{execution_id}:{step_id}"
            self.in_flight.discard(key)

    def cancel(self, execution_id: str):
        with self._lock:
            # Remove all in-flight items for this execution
            keys_to_remove = [k for k in self.in_flight if k.startswith(f"{execution_id}:")]
            for k in keys_to_remove:
                self.in_flight.remove(k)

