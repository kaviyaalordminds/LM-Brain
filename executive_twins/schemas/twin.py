from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import ExecutiveReviewOutcome, FactItem, FactState
from executive_twins.schemas.delegation import DelegationResult
from executive_twins.schemas.specialist import CapabilityRequirement


class ExecutiveTwinConfig(BaseModel):
    twin_id: str
    role: str
    description: str
    activation_conditions: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    decision_scope: List[str] = Field(default_factory=list)
    required_context: List[str] = Field(default_factory=list)
    delegation_policy: str = "capability_matched_only"
    review_policy: str = "evidence_backed_only"


class TwinAnalysis(BaseModel):
    facts: List[FactItem] = Field(default_factory=list)
    inferences: List[FactItem] = Field(default_factory=list)
    assumptions: List[FactItem] = Field(default_factory=list)
    unknowns: List[FactItem] = Field(default_factory=list)
    analysis_summary: str
    confidence: float = 1.0


class SubtaskSpec(BaseModel):
    task_id: str
    title: str
    description: str
    capability_requirement: CapabilityRequirement
    constraints: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)


class TaskDecomposition(BaseModel):
    objective: str
    subtasks: List[SubtaskSpec] = Field(default_factory=list)


class ReviewDecision(BaseModel):
    outcome: ExecutiveReviewOutcome
    reasoning: str
    revision_instructions: Optional[str] = None
    missing_evidence: List[str] = Field(default_factory=list)


class ExecutiveRecommendation(BaseModel):
    recommendation_id: str
    executive_twin_id: str
    role: str
    objective: str
    strategic_analysis: TwinAnalysis
    delegation_results: List[DelegationResult] = Field(default_factory=list)
    review_outcomes: List[ReviewDecision] = Field(default_factory=list)
    final_status: ExecutiveReviewOutcome
    confidence: float
    recommendation_text: str
    missing_capabilities: List[str] = Field(default_factory=list)
