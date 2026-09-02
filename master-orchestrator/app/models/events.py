from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class EventType(str, Enum):
    EXECUTION_CREATED = "EXECUTION_CREATED"
    PLAN_REQUESTED = "PLAN_REQUESTED"
    PLAN_RECEIVED = "PLAN_RECEIVED"
    STEP_READY = "STEP_READY"
    STEP_QUEUED = "STEP_QUEUED"
    STEP_DISPATCHED = "STEP_DISPATCHED"
    STEP_STARTED = "STEP_STARTED"
    STEP_COMPLETED = "STEP_COMPLETED"
    STEP_FAILED = "STEP_FAILED"
    VERIFICATION_STARTED = "VERIFICATION_STARTED"
    VERIFICATION_PASSED = "VERIFICATION_PASSED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    REPLAN_REQUESTED = "REPLAN_REQUESTED"
    REPLAN_RECEIVED = "REPLAN_RECEIVED"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    EXECUTION_PAUSED = "EXECUTION_PAUSED"
    EXECUTION_RESUMED = "EXECUTION_RESUMED"
    EXECUTION_CANCELLED = "EXECUTION_CANCELLED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    MEMORY_CONTEXT_FETCHED = "MEMORY_CONTEXT_FETCHED"

class ExecutionEvent(BaseModel):
    event_id: str
    event_type: EventType
    execution_id: str
    plan_id: Optional[str] = None
    plan_version: Optional[int] = None
    step_id: Optional[str] = None
    task_id: Optional[str] = None
    attempt_id: Optional[str] = None
    correlation_id: str
    timestamp: str
    payload: Dict[str, Any]
