"""
Typed data models and schemas for Master Orchestrator and Autonomous Control Loop.
Enforces typed lifecycle status tracking, bounded execution state, and structured evidence propagation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from executive_twins.reasoning.models import ReasoningPlan, ReasoningResponse, ReasoningStep
from executive_twins.schemas.common import (
    FactItem,
    FailureState,
    SecurityContext,
    VerificationStatus,
)
from executive_twins.schemas.evidence import EvidenceSet, TypedEvidence
from executive_twins.schemas.twin import ExecutiveRecommendation


class OrchestrationStatus(str, Enum):
    """Lifecycle statuses for the autonomous orchestration workflow."""
    RECEIVED = "RECEIVED"
    PERCEIVING = "PERCEIVING"
    PLANNING = "PLANNING"
    VALIDATING = "VALIDATING"
    SELECTING_CAPABILITIES = "SELECTING_CAPABILITIES"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    REPLANNING = "REPLANNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"


class StepExecutionRecord(BaseModel):
    """
    Detailed execution record for an individual step within an orchestration workflow.
    """
    step_id: str
    objective: str
    required_capability: str
    specialist_id: Optional[str] = None
    status: str = "PENDING"  # PENDING, COMPLETED, FAILED, SKIPPED, NOT_ATTEMPTED
    output: str = ""
    artifacts: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


class OrchestrationRequest(BaseModel):
    """
    Input request submitted to the Master Orchestrator.
    """
    request_id: str
    user_goal: str
    context: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: List[str] = Field(default_factory=list)
    available_capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    security_context: SecurityContext = Field(default_factory=SecurityContext)
    require_twin_evaluation: bool = True
    require_memory_writeback: bool = True


class OrchestrationConfig(BaseModel):
    """
    Configurable operational limits and bounds for the autonomous control loop.
    """
    max_iterations: int = 20
    max_recovery_attempts: int = 3
    max_consecutive_failures: int = 3
    max_plan_steps: int = 20
    timeout_seconds: float = 300.0
    min_confidence: float = 0.5


class OrchestrationState(BaseModel):
    """
    Mutable state tracker for an in-flight autonomous control loop execution.
    Never stores plaintext secrets or credentials.
    """
    request: OrchestrationRequest
    current_status: OrchestrationStatus = OrchestrationStatus.RECEIVED
    current_plan: Optional[ReasoningPlan] = None
    current_step_index: int = 0
    completed_steps: List[StepExecutionRecord] = Field(default_factory=list)
    failed_steps: List[StepExecutionRecord] = Field(default_factory=list)
    skipped_steps: List[StepExecutionRecord] = Field(default_factory=list)
    observations: List[TypedEvidence] = Field(default_factory=list)
    evidence_set: EvidenceSet = Field(default_factory=EvidenceSet)
    recovery_count: int = 0
    consecutive_failure_count: int = 0
    iteration_count: int = 0
    selected_specialists: Dict[str, str] = Field(default_factory=dict)  # capability -> specialist_id
    outputs: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    unresolved_information: List[str] = Field(default_factory=list)
    final_result: Optional[str] = None
    executive_twin_recommendation: Optional[ExecutiveRecommendation] = None
    memory_writeback_status: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrchestrationResult(BaseModel):
    """
    Authoritative, structured outcome of a Master Orchestrator workflow execution.
    """
    request_id: str
    final_status: OrchestrationStatus
    completed_steps: List[StepExecutionRecord] = Field(default_factory=list)
    failed_steps: List[StepExecutionRecord] = Field(default_factory=list)
    skipped_steps: List[StepExecutionRecord] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    evidence: EvidenceSet = Field(default_factory=EvidenceSet)
    failures: List[Dict[str, Any]] = Field(default_factory=list)
    recovery_history: List[Dict[str, Any]] = Field(default_factory=list)
    final_message: str = ""
    memory_writeback_status: Optional[str] = None
    iterations_run: int = 0
    recovery_attempts: int = 0
    duration_seconds: float = 0.0
    executive_twin_id: Optional[str] = None
