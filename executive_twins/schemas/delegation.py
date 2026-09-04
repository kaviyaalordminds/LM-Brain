from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import SecurityContext, VerificationStatus
from executive_twins.schemas.evidence import EvidenceCategory, EvidenceSet


class DelegationRequest(BaseModel):
    delegation_id: str
    parent_task_id: str
    executive_twin_id: str
    specialist_id: str
    objective: str
    task: str
    required_capabilities: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_output: str
    success_criteria: List[str] = Field(default_factory=list)
    required_evidence_categories: List[EvidenceCategory] = Field(default_factory=list)
    priority: str = "normal"
    security_context: SecurityContext = Field(default_factory=SecurityContext)


class DelegationResult(BaseModel):
    delegation_id: str
    specialist_id: str
    status: str  # "SUCCESS", "FAILED", "TIMEOUT", "EVIDENCE_MISSING", etc.
    output: str
    artifacts: List[str] = Field(default_factory=list)
    evidence: EvidenceSet = Field(default_factory=EvidenceSet)
    confidence: float = 1.0
    errors: List[str] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
