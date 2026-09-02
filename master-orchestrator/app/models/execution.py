from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

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

class ExecutionPhase(str, Enum):
    INTENT_NORMALIZATION = "INTENT_NORMALIZATION"
    PLANNING = "PLANNING"
    SCHEDULING = "SCHEDULING"
    DISPATCHING = "DISPATCHING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    FINALIZING = "FINALIZING"

class Execution(BaseModel):
    execution_id: str
    request_id: str
    user_request: str
    plan_id: Optional[str] = None
    plan_version: int = 1
    status: ExecutionStatus = ExecutionStatus.CREATED
    phase: ExecutionPhase = ExecutionPhase.INTENT_NORMALIZATION
    created_at: str
    updated_at: str
    completed_steps: List[str] = Field(default_factory=list)
    failed_steps: List[str] = Field(default_factory=list)
    running_steps: List[str] = Field(default_factory=list)
    blocked_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    events: List[str] = Field(default_factory=list)
    attempts: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str
