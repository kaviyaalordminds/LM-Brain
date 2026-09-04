from typing import Optional

from executive_twins.client.agent_adapter import ISpecialistAgentAdapter
from executive_twins.execution.review_engine import ReviewEngine
from executive_twins.schemas.common import ExecutiveReviewOutcome
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.twin import ReviewDecision


class DelegationEngine:
    """
    Delegation Dispatcher and Bounded Retry Engine.
    Executes structured delegation requests via ISpecialistAgentAdapter and applies the failure state machine.
    """

    def __init__(
        self, agent_adapter: ISpecialistAgentAdapter, max_retries: int = 2
    ) -> None:
        self.agent_adapter = agent_adapter
        self.max_retries = max_retries

    def execute_and_review(
        self, request: DelegationRequest
    ) -> tuple[DelegationResult, ReviewDecision]:
        attempt = 0
        last_result: Optional[DelegationResult] = None
        last_decision: Optional[ReviewDecision] = None

        while attempt <= self.max_retries:
            attempt += 1
            result = self.agent_adapter.execute_delegation(request)
            decision = ReviewEngine.evaluate_result(request, result)

            last_result = result
            last_decision = decision

            # Approved -> Done
            if decision.outcome == ExecutiveReviewOutcome.APPROVED:
                return result, decision

            # Terminal Non-Retryable Outcomes
            if decision.outcome in [
                ExecutiveReviewOutcome.NO_REGISTERED_SPECIALIST_AVAILABLE,
                ExecutiveReviewOutcome.SECURITY_AUTHORIZATION_REQUIRED,
                ExecutiveReviewOutcome.ESCALATE,
            ]:
                return result, decision

            # Retryable Failure Modes (Bounded Retry)
            if attempt > self.max_retries:
                break

            # Update request notes for retry if revision or evidence required
            if decision.outcome in [
                ExecutiveReviewOutcome.REVISION_REQUIRED,
                ExecutiveReviewOutcome.MORE_EVIDENCE_REQUIRED,
            ]:
                request.task += f" [REVISION ATTEMPT {attempt}: {decision.revision_instructions}]"

        return last_result, last_decision  # type: ignore
