"""
Typed data models and schemas for Coding / Reasoning Model Integration.
Enforces structured reasoning contracts, bounded execution limits, and strict schema validation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import (
    FactItem,
    FactState,
    FailureState,
    SecurityContext,
    VerificationStatus,
)
from executive_twins.schemas.evidence import BaseEvidence, EvidenceSet, TypedEvidence


class ReasoningMode(str, Enum):
    """Modes of operation supported by the reasoning engine."""
    PLAN = "PLAN"
    DECOMPOSE = "DECOMPOSE"
    DECIDE = "DECIDE"
    RECOVER = "RECOVER"
    REPLAN = "REPLAN"
    DEVELOP = "DEVELOP"
    ANALYZE = "ANALYZE"


class ReasoningStatus(str, Enum):
    """Deterministic status outcomes for reasoning requests."""
    SUCCESS = "SUCCESS"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    INVALID = "INVALID"
    FAILED = "FAILED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


class RiskLevel(str, Enum):
    """Categorization of potential operational risk associated with a reasoning step."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReasoningStep(BaseModel):
    """
    Structured representation of an individual proposed action or decision.
    Represents declarative capability requirements and objectives, NOT raw shell/filesystem commands.
    """
    step_id: str
    objective: str
    required_capability: str
    specialist_role: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    expected_output: str = ""
    verification_requirement: str = ""
    rationale: str = ""
    risk_level: RiskLevel = RiskLevel.LOW
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ReasoningPlan(BaseModel):
    """
    Machine-validatable structured execution plan produced by the reasoning engine.
    """
    plan_id: str
    goal: str
    steps: List[ReasoningStep] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    verification_requirements: List[str] = Field(default_factory=list)


class ReasoningRequest(BaseModel):
    """
    Structured reasoning request submitted to the Reasoning Service.
    Contains goal, state, available capabilities, empirical evidence, and company knowledge.
    Never exposes credentials or unrestricted system handles.
    """
    request_id: str
    user_goal: str
    context: Dict[str, Any] = Field(default_factory=dict)
    available_capabilities: List[str] = Field(default_factory=list)
    relevant_company_knowledge: List[FactItem] = Field(default_factory=list)
    current_state: Dict[str, Any] = Field(default_factory=dict)
    previous_actions: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[TypedEvidence] = Field(default_factory=list)
    failures: List[Dict[str, Any]] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    mode: ReasoningMode = ReasoningMode.PLAN
    security_context: SecurityContext = Field(default_factory=SecurityContext)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningResponse(BaseModel):
    """
    Structured outcome of a reasoning cycle.
    Directs the Master Orchestrator via declarative plans and decisions.
    """
    request_id: str
    status: ReasoningStatus
    reasoning_mode: ReasoningMode
    structured_plan: Optional[ReasoningPlan] = None
    decision: Optional[str] = None
    unresolved_questions: List[str] = Field(default_factory=list)
    required_information: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    failure_diagnosis: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningConfig(BaseModel):
    """
    Configurable operational bounds and safety limits for reasoning execution.
    """
    max_request_size: int = 100_000
    max_response_size: int = 100_000
    max_plan_steps: int = 20
    max_recovery_iterations: int = 3
    timeout_seconds: float = 60.0
    min_confidence: float = 0.5
