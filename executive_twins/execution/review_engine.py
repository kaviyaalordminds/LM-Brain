from typing import List

from executive_twins.schemas.common import ExecutiveReviewOutcome, VerificationStatus
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.twin import ReviewDecision


class ReviewEngine:
    """
    Evidence-First Review Engine.
    Validates Specialist execution results against success criteria and task-specific required evidence categories.
    An Executive Twin NEVER accepts an unevidenced text claim as successful execution.
    """

    @staticmethod
    def evaluate_result(request: DelegationRequest, result: DelegationResult) -> ReviewDecision:
        # 1. Check Specialist Execution Status
        if result.status == "NO_REGISTERED_SPECIALIST_AVAILABLE":
            return ReviewDecision(
                outcome=ExecutiveReviewOutcome.NO_REGISTERED_SPECIALIST_AVAILABLE,
                reasoning=f"No registered specialist was available for task: {request.task}",
            )

        if result.status in ["FAILED", "TIMEOUT", "EXECUTION_FAILED"]:
            return ReviewDecision(
                outcome=ExecutiveReviewOutcome.SPECIALIST_FAILURE,
                reasoning=f"Specialist '{result.specialist_id}' execution failed: {result.errors}",
            )

        # 2. Evidence Verification: Check that required evidence categories are present
        missing_ev: List[str] = []
        for req_cat in request.required_evidence_categories:
            if not result.evidence.contains_category(req_cat):
                missing_ev.append(req_cat.value)

        if missing_ev:
            return ReviewDecision(
                outcome=ExecutiveReviewOutcome.MORE_EVIDENCE_REQUIRED,
                reasoning=f"Delegation result is missing required empirical evidence categories: {missing_ev}",
                missing_evidence=missing_ev,
                revision_instructions="Provide empirical evidence (artifact, log, test report, or API response). Text-only assertions are rejected.",
            )

        # 3. Verification Status Check
        if result.verification_status == VerificationStatus.FAILED:
            return ReviewDecision(
                outcome=ExecutiveReviewOutcome.REVISION_REQUIRED,
                reasoning=f"Specialist verification failed for delegation '{request.delegation_id}'.",
                revision_instructions="Re-execute task and resolve automated test/build assertion failures.",
            )

        # 4. Check that at least some evidence exists if criteria are specified
        if request.success_criteria and len(result.evidence.items) == 0:
            return ReviewDecision(
                outcome=ExecutiveReviewOutcome.MORE_EVIDENCE_REQUIRED,
                reasoning="Task has explicit success criteria but zero system-generated evidence items were attached.",
                missing_evidence=["SYSTEM_EVIDENCE"],
            )

        return ReviewDecision(
            outcome=ExecutiveReviewOutcome.APPROVED,
            reasoning=f"Specialist execution verified successfully with {len(result.evidence.items)} system evidence items.",
        )
