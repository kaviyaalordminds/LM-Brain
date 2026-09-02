from typing import List, Dict, Set
from app.models.state import StepLifecycle

class Scheduler:
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.in_flight: Set[str] = set()

    def tick(self, execution_id: str, step_states: Dict[str, StepLifecycle], plan_dependencies: Dict[str, List[str]]) -> List[str]:
        ready_queue = []
        for step_id, deps in plan_dependencies.items():
            state = step_states.get(f"{execution_id}:{step_id}", StepLifecycle.PENDING)
            
            if state == StepLifecycle.PENDING:
                # Check if all dependencies are COMPLETED
                deps_completed = True
                for dep in deps:
                    dep_state = step_states.get(f"{execution_id}:{dep}", StepLifecycle.PENDING)
                    if dep_state != StepLifecycle.COMPLETED:
                        deps_completed = False
                        break
                
                if deps_completed:
                    ready_queue.append(step_id)

        # We can return all newly ready steps. Engine will limit concurrency.
        return ready_queue

    def cancel(self, execution_id: str):
        self.in_flight.clear()
