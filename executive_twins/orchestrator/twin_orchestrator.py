from typing import Any, Dict, List, Optional
import uuid

from executive_twins.client.agent_adapter import ISpecialistAgentAdapter
from executive_twins.client.registry_client import ISpecialistRegistryClient
from executive_twins.execution.delegation_engine import DelegationEngine
from executive_twins.schemas.common import (
    ExecutiveReviewOutcome,
    SecurityContext,
)
from executive_twins.schemas.delegation import DelegationResult
from executive_twins.schemas.specialist import SpecialistSelectionResult
from executive_twins.schemas.twin import ExecutiveRecommendation, ReviewDecision
from executive_twins.twins.base import ExecutiveTwin
from executive_twins.twins.ceo import CEOTwin
from executive_twins.twins.cfo import CFOTwin
from executive_twins.twins.cmo import CMOTwin
from executive_twins.twins.coo import COOTwin
from executive_twins.twins.cto import CTOTwin
from executive_twins.utils.audit_logger import AuditLogger


class TwinOrchestrator:
    """
    Internal Executive Twin Orchestrator.
    Manages Twin resolution, conditional activation, capability discovery via ISpecialistRegistryClient,
    structured delegation dispatch, evidence review, and final recommendation synthesis.
    Bound inside the Master Orchestrator workflow.
    """

    def __init__(
        self,
        registry_client: ISpecialistRegistryClient,
        agent_adapter: ISpecialistAgentAdapter,
        max_retries: int = 2,
    ) -> None:
        self.registry_client = registry_client
        self.agent_adapter = agent_adapter
        self.delegation_engine = DelegationEngine(agent_adapter, max_retries=max_retries)

        # Registered Executive Twins
        self.twins: List[ExecutiveTwin] = [
            CMOTwin(),  # Primary for marketing app request
            CEOTwin(),
            COOTwin(),
            CTOTwin(),
            CFOTwin(),
        ]

    def resolve_twin(self, request_text: str) -> Optional[ExecutiveTwin]:
        """Resolve relevant Executive Twin based on conditional activation."""
        AuditLogger.log_event("twin.resolution.started", {"request_text": request_text})
        for twin in self.twins:
            if twin.should_activate(request_text):
                AuditLogger.log_event(
                    "twin.resolved", {"twin_id": twin.config.twin_id, "role": twin.config.role}
                )
                return twin
        return None

    def process_request(
        self,
        request_text: str,
        context: Optional[Dict[str, Any]] = None,
        security_context: Optional[SecurityContext] = None,
    ) -> ExecutiveRecommendation:
        if security_context is None:
            security_context = SecurityContext()

        # Step 1: Twin Resolution
        twin = self.resolve_twin(request_text)
        if not twin:
            # No executive reasoning required
            AuditLogger.log_event("twin.activation.skipped", {"reason": "No executive reasoning required."})
            return ExecutiveRecommendation(
                recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                executive_twin_id="none",
                role="None",
                objective=request_text,
                strategic_analysis=ExecutiveTwin.analyze(self.twins[0], request_text, context),  # type: ignore
                delegation_results=[],
                review_outcomes=[],
                final_status=ExecutiveReviewOutcome.APPROVED,
                confidence=1.0,
                recommendation_text="NO_EXECUTIVE_TWIN_REQUIRED: Direct task execution path available.",
                missing_capabilities=[],
            )

        AuditLogger.log_event(
            "twin.activated", {"twin_id": twin.config.twin_id, "role": twin.config.role}
        )

        # Step 2: Strategic Analysis
        analysis = twin.analyze(request_text, context)

        # Step 3: Task Decomposition into CapabilityRequirements
        decomposition = twin.decompose_task(request_text, analysis)

        # Step 4: Query Specialist Registry for matching capabilities
        cap_reqs = [st.capability_requirement for st in decomposition.subtasks]
        AuditLogger.log_event(
            "specialist.discovery.started", {"required_capabilities": [c.capability_name for c in cap_reqs]}
        )

        selection_results: List[SpecialistSelectionResult] = self.registry_client.discover_specialists(
            cap_reqs, security_context
        )

        # Check if any capability has NO_REGISTERED_SPECIALIST_AVAILABLE
        missing_capabilities: List[str] = []
        for sel in selection_results:
            if sel.status == "NO_REGISTERED_SPECIALIST_AVAILABLE" or not sel.selected_specialist:
                for req in cap_reqs:
                    if req.capability_name not in missing_capabilities:
                        # Check if capability was matched in any selection
                        matched_in_any = any(
                            s.selected_specialist and any(c.name.lower() == req.capability_name.lower() for c in s.selected_specialist.capabilities)
                            for s in selection_results
                        )
                        if not matched_in_any:
                            missing_capabilities.append(req.capability_name)

        if missing_capabilities:
            AuditLogger.log_event(
                "specialist.discovery.failed", {"missing_capabilities": missing_capabilities}
            )
            return twin.synthesize_recommendation(
                request_text=request_text,
                analysis=analysis,
                delegation_results=[],
                review_decisions=[],
                missing_capabilities=missing_capabilities,
            )

        # Log selected specialists
        for sel in selection_results:
            if sel.selected_specialist:
                AuditLogger.log_event(
                    "specialist.selected",
                    {
                        "specialist_id": sel.selected_specialist.specialist_id,
                        "name": sel.selected_specialist.name,
                        "matched_capabilities": sel.matched_capabilities,
                        "provenance_snapshot": sel.selected_specialist.provenance.snapshot_id,
                    },
                )

        # Step 5: Build Structured Delegation Requests
        delegation_requests = twin.create_delegation_requests(
            decomposition=decomposition,
            selection_results=selection_results,
            security_context=security_context,
        )

        # Step 6: Dispatch Delegations and Run Review Engine
        delegation_results: List[DelegationResult] = []
        review_decisions: List[ReviewDecision] = []

        for del_req in delegation_requests:
            AuditLogger.log_event(
                "delegation.created",
                {
                    "delegation_id": del_req.delegation_id,
                    "specialist_id": del_req.specialist_id,
                    "task": del_req.task,
                },
            )

            result, decision = self.delegation_engine.execute_and_review(del_req)

            AuditLogger.log_event(
                "evidence.received",
                {
                    "delegation_id": del_req.delegation_id,
                    "specialist_id": del_req.specialist_id,
                    "evidence_count": len(result.evidence.items),
                    "review_outcome": decision.outcome.value,
                },
            )

            delegation_results.append(result)
            review_decisions.append(decision)

        # Step 7: Synthesize Final Recommendation
        recommendation = twin.synthesize_recommendation(
            request_text=request_text,
            analysis=analysis,
            delegation_results=delegation_results,
            review_decisions=review_decisions,
            missing_capabilities=[],
        )

        AuditLogger.log_event(
            "recommendation.created",
            {
                "recommendation_id": recommendation.recommendation_id,
                "final_status": recommendation.final_status.value,
                "confidence": recommendation.confidence,
            },
        )

        return recommendation
