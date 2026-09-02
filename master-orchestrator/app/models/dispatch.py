from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum

class AttemptStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"

class DispatchRequest(BaseModel):
    dispatch_id: str
    execution_id: str
    plan_id: str
    plan_version: int
    step_id: str
    task_id: str
    attempt_id: str
    specialist_id: str
    idempotency_key: str
    instruction: str
    memory_required: bool
    research_required: bool
    expected_outputs: Dict[str, Any]
    verification_criteria: List[str]
    metadata: Dict[str, Any]

class DispatchAttempt(BaseModel):
    model_config = {"protected_namespaces": ()}

    attempt_id: str
    attempt_number: int

    step_id: str
    task_id: str = ""
    execution_id: str
    specialist_id: str = ""
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    status: AttemptStatus
    failure_type: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    model_reference: Optional[str] = None
    result_reference: Optional[str] = None
    correlation_id: str = ""
    idempotency_key: str

