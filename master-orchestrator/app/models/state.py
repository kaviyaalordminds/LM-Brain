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

class ExecutionStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

LEGAL_STEP_TRANSITIONS: Dict[StepLifecycle, Set[StepLifecycle]] = {
    StepLifecycle.PENDING: {StepLifecycle.READY, StepLifecycle.BLOCKED, StepLifecycle.SKIPPED},
    StepLifecycle.READY: {StepLifecycle.QUEUED, StepLifecycle.BLOCKED, StepLifecycle.SKIPPED, StepLifecycle.FAILED},
    StepLifecycle.QUEUED: {StepLifecycle.DISPATCHED, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.DISPATCHED: {StepLifecycle.RUNNING, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.RUNNING: {StepLifecycle.VERIFYING, StepLifecycle.FAILED, StepLifecycle.SKIPPED},
    StepLifecycle.VERIFYING: {StepLifecycle.COMPLETED, StepLifecycle.FAILED},
    StepLifecycle.COMPLETED: set(),  # Immutable terminal state
    StepLifecycle.FAILED: {StepLifecycle.READY},  # Only retry/replan can make it READY
    StepLifecycle.BLOCKED: {StepLifecycle.READY, StepLifecycle.SKIPPED},
    StepLifecycle.SKIPPED: set(),  # Immutable terminal state
}

# Alias for backwards compatibility
LEGAL_TRANSITIONS = LEGAL_STEP_TRANSITIONS

LEGAL_EXECUTION_TRANSITIONS: Dict[ExecutionStatus, Set[ExecutionStatus]] = {
    ExecutionStatus.CREATED: {ExecutionStatus.PLANNING, ExecutionStatus.CANCELLED},
    ExecutionStatus.PLANNING: {ExecutionStatus.PLANNED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED},
    ExecutionStatus.PLANNED: {ExecutionStatus.RUNNING, ExecutionStatus.PAUSED, ExecutionStatus.CANCELLED},
    ExecutionStatus.RUNNING: {
        ExecutionStatus.PAUSED,
        ExecutionStatus.RECOVERING,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED
    },
    ExecutionStatus.PAUSED: {ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED},
    ExecutionStatus.RECOVERING: {ExecutionStatus.RUNNING, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED},
    ExecutionStatus.COMPLETED: set(),  # Terminal state: COMPLETED -> RUNNING is strictly illegal
    ExecutionStatus.FAILED: {ExecutionStatus.RECOVERING},  # FAILED -> COMPLETED directly is illegal without recovery
    ExecutionStatus.CANCELLED: set(),  # Terminal state: CANCELLED -> RUNNING is strictly illegal
}

TERMINAL_EXECUTION_STATES: Set[ExecutionStatus] = {
    ExecutionStatus.COMPLETED,
    ExecutionStatus.CANCELLED,
}

TERMINAL_STEP_STATES: Set[StepLifecycle] = {
    StepLifecycle.COMPLETED,
    StepLifecycle.SKIPPED,
}

