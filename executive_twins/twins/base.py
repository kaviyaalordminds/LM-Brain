from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import uuid

from executive_twins.schemas.common import (
    ExecutiveReviewOutcome,
    FactItem,
    FactState,
    SecurityContext,
)
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import EvidenceCategory
from executive_twins.schemas.specialist import (
    CapabilityRequirement,
    SpecialistSelectionResult,
)
from executive_twins.schemas.twin import (
    ExecutiveRecommendation,
    ExecutiveTwinConfig,
    ReviewDecision,
    SubtaskSpec,
    TaskDecomposition,
    TwinAnalysis,
)
from executive_twins.utils.audit_logger import AuditLogger


class ExecutiveTwin(ABC):
    """
    Abstract base framework for Executive Digital Twins.
    Executive Twins are CONDITIONAL STRATEGIC DECISION-MAKERS.
    They do NOT directly perform specialist execution. They analyze, decompose tasks into
    CapabilityRequirements, discover specialists via ISpecialistRegistryClient, delegate, review evidence,
    and return ExecutiveRecommendations.
    """

    def __init__(self, config: ExecutiveTwinConfig) -> None:
        self.config = config

    @abstractmethod
    def should_activate(self, request_text: str) -> bool:
        """Evaluate if this Twin should be activated based on executive reasoning requirements."""
        pass

    @abstractmethod
    def generate_capability_requirements(self, request_text: str) -> List[CapabilityRequirement]:
        """
        Generate required capabilities for the given request.
        MUST NOT contain hardcoded specialist IDs or agent names.
        """
        pass

    def analyze(self, request_text: str, context: Optional[Dict[str, Any]] = None) -> TwinAnalysis:
        """
        Analyze request and separate internal state into FACT, INFERENCE, ASSUMPTION, UNKNOWN.
        """
        AuditLogger.log_event("twin.analysis.started", {"twin_id": self.config.twin_id, "role": self.config.role})

        facts: List[FactItem] = [
            FactItem(statement=f"User request received: '{request_text}'", state=FactState.FACT, source="user_input")
        ]
        inferences: List[FactItem] = []
        assumptions: List[FactItem] = []
        unknowns: List[FactItem] = []

        if context:
            for k, v in context.items():
                facts.append(FactItem(statement=f"Context property '{k}': {v}", state=FactState.FACT, source="context"))
        else:
            unknowns.append(
                FactItem(
                    statement="Additional operational context or environment parameters",
                    state=FactState.UNKNOWN,
                    source="environment",
                )
            )

        analysis = TwinAnalysis(
            facts=facts,
            inferences=inferences,
            assumptions=assumptions,
            unknowns=unknowns,
            analysis_summary=f"Analyzed request under {self.config.role} domain scope.",
            confidence=0.90 if context else 0.80,
        )

        return analysis

    def decompose_task(self, request_text: str, analysis: TwinAnalysis) -> TaskDecomposition:
        """
        Decompose objective into capability-requirement subtasks.
        """
        cap_reqs = self.generate_capability_requirements(request_text)
        subtasks: List[SubtaskSpec] = []

        for idx, req in enumerate(cap_reqs, 1):
            subtasks.append(
                SubtaskSpec(
                    task_id=f"subtask-{idx}",
                    title=f"Execute {req.capability_name}",
                    description=req.description,
                    capability_requirement=req,
                    constraints=req.constraints,
                    success_criteria=[f"Successfully fulfill {req.capability_name} with verifiable evidence."],
                )
            )

        return TaskDecomposition(objective=request_text, subtasks=subtasks)

    def create_delegation_requests(
        self,
        decomposition: TaskDecomposition,
        selection_results: List[SpecialistSelectionResult],
        security_context: SecurityContext,
    ) -> List[DelegationRequest]:
        """
        Build structured DelegationRequest objects matching selected registered specialists.
        """
        delegation_requests: List[DelegationRequest] = []

        for subtask, selection in zip(decomposition.subtasks, selection_results):
            if selection.status != "MATCHED" or not selection.selected_specialist:
                continue

            spec = selection.selected_specialist
            del_id = f"del-{uuid.uuid4().hex[:8]}"

            req = DelegationRequest(
                delegation_id=del_id,
                parent_task_id=subtask.task_id,
                executive_twin_id=self.config.twin_id,
                specialist_id=spec.specialist_id,
                objective=subtask.description,
                task=subtask.title,
                required_capabilities=[subtask.capability_requirement.capability_name],
                constraints=subtask.constraints,
                inputs={"objective": subtask.description},
                expected_output=f"Verifiable execution artifact and evidence for {subtask.capability_requirement.capability_name}",
                success_criteria=subtask.success_criteria,
                required_evidence_categories=[EvidenceCategory.ARTIFACT, EvidenceCategory.EXECUTION_LOG],
                priority="normal",
                security_context=security_context,
            )
            delegation_requests.append(req)

        return delegation_requests

    def synthesize_recommendation(
        self,
        request_text: str,
        analysis: TwinAnalysis,
        delegation_results: Optional[List[DelegationResult]] = None,
        review_decisions: Optional[List[ReviewDecision]] = None,
        missing_capabilities: Optional[List[str]] = None,
    ) -> ExecutiveRecommendation:
        """
        Synthesize review outcomes into final ExecutiveRecommendation.
        """
        if delegation_results is None:
            delegation_results = []
        if review_decisions is None:
            review_decisions = []
        if missing_capabilities is None:
            missing_capabilities = []

        rec_id = f"rec-{uuid.uuid4().hex[:8]}"

        if missing_capabilities:
            final_status = ExecutiveReviewOutcome.NO_REGISTERED_SPECIALIST_AVAILABLE
            rec_text = (
                f"[{self.config.role}] Unable to complete executive objective. "
                f"Missing registered specialists for required capabilities: {missing_capabilities}."
            )
            confidence = 0.0
        elif any(rd.outcome == ExecutiveReviewOutcome.SPECIALIST_FAILURE for rd in review_decisions):
            final_status = ExecutiveReviewOutcome.SPECIALIST_FAILURE
            rec_text = f"[{self.config.role}] Executive workflow failed due to specialist execution failure."
            confidence = 0.2
        elif any(rd.outcome == ExecutiveReviewOutcome.REVISION_REQUIRED for rd in review_decisions):
            final_status = ExecutiveReviewOutcome.REVISION_REQUIRED
            rec_text = f"[{self.config.role}] Revision required for specialist execution."
            confidence = 0.5
        elif any(rd.outcome == ExecutiveReviewOutcome.MORE_EVIDENCE_REQUIRED for rd in review_decisions):
            final_status = ExecutiveReviewOutcome.MORE_EVIDENCE_REQUIRED
            rec_text = f"[{self.config.role}] Additional evidence required before executive approval."
            confidence = 0.4
        else:
            final_status = ExecutiveReviewOutcome.APPROVED
            rec_text = (
                f"[{self.config.role}] Executive strategy formulated and verified. "
                f"All {len(delegation_results)} delegated tasks completed with verified evidence."
            )
            confidence = 0.95

        return ExecutiveRecommendation(
            recommendation_id=rec_id,
            executive_twin_id=self.config.twin_id,
            role=self.config.role,
            objective=request_text,
            strategic_analysis=analysis,
            delegation_results=delegation_results,
            review_outcomes=review_decisions,
            final_status=final_status,
            confidence=confidence,
            recommendation_text=rec_text,
            missing_capabilities=missing_capabilities,
        )
