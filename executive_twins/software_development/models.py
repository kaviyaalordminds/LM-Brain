"""
Typed data models for Software Development Agent and bounded development workflows.
Strictly reuses existing schemas for common types, evidence, and facts.
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
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)


class PlanStepAction(str, Enum):
    """Controlled, typed plan action categories. Arbitrary shell commands are forbidden."""
    INSPECT = "INSPECT"
    CREATE_FILE = "CREATE_FILE"
    READ_FILE = "READ_FILE"
    UPDATE_FILE = "UPDATE_FILE"
    DELETE_FILE = "DELETE_FILE"
    LIST_FILES = "LIST_FILES"
    RUN_TEST = "RUN_TEST"
    RUN_BUILD = "RUN_BUILD"
    RUN_LINT = "RUN_LINT"
    RUN_TYPECHECK = "RUN_TYPECHECK"
    WORKSPACE_BUILD = "WORKSPACE_BUILD"
    VALIDATE_PROJECT = "VALIDATE_PROJECT"
    GIT_STATUS = "GIT_STATUS"
    GIT_DIFF = "GIT_DIFF"
    GIT_STAGE = "GIT_STAGE"
    GIT_COMMIT = "GIT_COMMIT"
    GIT_BRANCH = "GIT_BRANCH"
    GIT_LOG = "GIT_LOG"
    GIT_UNSTAGE = "GIT_UNSTAGE"
    DOCKER_AVAILABILITY = "DOCKER_AVAILABILITY"
    DOCKER_BUILD = "DOCKER_BUILD"
    DOCKER_RUN = "DOCKER_RUN"
    DOCKER_INSPECT = "DOCKER_INSPECT"
    DOCKER_STOP = "DOCKER_STOP"
    DOCKER_REMOVE = "DOCKER_REMOVE"


class DevelopmentFileSpec(BaseModel):
    """Specification of a file to be developed or validated in a project."""
    path: str
    purpose: str
    is_required: bool = True


class PlanStepStatus(str, Enum):
    """Lifecycle status of an individual development plan step."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PlanStep(BaseModel):
    """Represents a discrete, typed development action within a bounded plan."""
    step_id: str
    action: PlanStepAction
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    status: PlanStepStatus = PlanStepStatus.PENDING
    result_output: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    failure_reason: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DevelopmentPlanStatus(str, Enum):
    """Lifecycle status of the entire development plan."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class DevelopmentPlan(BaseModel):
    """Ordered collection of development steps executed within the bounded development loop."""
    plan_id: str
    request_id: str
    project_goal: Optional[str] = None
    workspace_id: Optional[str] = None
    files: List[DevelopmentFileSpec] = Field(default_factory=list)
    validation_steps: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    steps: List[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0
    status: DevelopmentPlanStatus = DevelopmentPlanStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    @property
    def current_step(self) -> Optional[PlanStep]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def completed_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if s.status == PlanStepStatus.COMPLETED]

    @property
    def failed_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if s.status == PlanStepStatus.FAILED]


class DevelopmentRequest(BaseModel):
    """
    Strongly typed software development request submitted to the Software Development Agent.
    """
    request_id: str
    specialist_id: str = "spec_software_dev_01"
    workspace_id: str
    task: str
    requirements: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    security_context: SecurityContext = Field(default_factory=SecurityContext)
    max_iterations: int = 5
    max_steps: int = 25
    timeout_seconds: float = 300.0


class DevelopmentStatus(str, Enum):
    """Outcome status of a development request."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    TIMEOUT = "TIMEOUT"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"


class DevelopmentResult(BaseModel):
    """
    Structured outcome of a software development execution.
    Contains empirical evidence, verifiable facts, recorded artifacts, and step history.
    """
    request_id: str
    workspace_id: str
    status: DevelopmentStatus
    completed_steps: List[PlanStep] = Field(default_factory=list)
    failed_steps: List[PlanStep] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)
    evidence: EvidenceSet = Field(default_factory=EvidenceSet)
    facts: List[FactItem] = Field(default_factory=list)
    verification: VerificationStatus = VerificationStatus.UNVERIFIED
    summary: str
    failure_reason: Optional[str] = None
    iterations_run: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0


class DiagnosticResult(BaseModel):
    """Result of failure diagnosis when a plan step fails."""
    can_recover: bool = False
    diagnosis: str
    suggested_fix_steps: List[PlanStep] = Field(default_factory=list)
    reason: Optional[str] = None
