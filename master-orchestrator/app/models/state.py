from enum import Enum
from typing import Dict, Set

class StepLifecycle(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"

LEGAL_TRANSITIONS: Dict[StepLifecycle, Set[StepLifecycle]] = {
    StepLifecycle.PENDING: {StepLifecycle.READY, StepLifecycle.BLOCKED},
    StepLifecycle.READY: {StepLifecycle.QUEUED, StepLifecycle.BLOCKED, StepLifecycle.SKIPPED},
    StepLifecycle.QUEUED: {StepLifecycle.DISPATCHED, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.DISPATCHED: {StepLifecycle.RUNNING, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.RUNNING: {StepLifecycle.VERIFYING, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.VERIFYING: {StepLifecycle.COMPLETED, StepLifecycle.FAILED},
    StepLifecycle.COMPLETED: set(),
    StepLifecycle.FAILED: {StepLifecycle.READY},
    StepLifecycle.BLOCKED: {StepLifecycle.READY},
    StepLifecycle.SKIPPED: set(),
}
