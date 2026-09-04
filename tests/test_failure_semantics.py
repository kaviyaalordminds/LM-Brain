import pytest
from executive_twins.client.agent_adapter import MockSpecialistAgentAdapter
from executive_twins.execution.delegation_engine import DelegationEngine
from executive_twins.execution.review_engine import ReviewEngine
from executive_twins.schemas.common import ExecutiveReviewOutcome, VerificationStatus
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import EvidenceCategory, EvidenceSet


def test_failure_semantics_no_specialist_does_not_retry() -> None:
    adapter = MockSpecialistAgentAdapter()
    engine = DelegationEngine(adapter, max_retries=2)

    req = DelegationRequest(
        delegation_id="del-fail-01",
        parent_task_id="st-01",
        executive_twin_id="twin-cmo-01",
        specialist_id="non_existent_spec",
        objective="Do work",
        task="Work task",
        expected_output="Output",
    )

    # Set custom response representing missing specialist
    adapter.set_custom_response(
        "non_existent_spec",
        DelegationResult(
            delegation_id="del-fail-01",
            specialist_id="non_existent_spec",
            status="NO_REGISTERED_SPECIALIST_AVAILABLE",
            output="Specialist unavailable",
        ),
    )

    result, decision = engine.execute_and_review(req)
    assert decision.outcome == ExecutiveReviewOutcome.NO_REGISTERED_SPECIALIST_AVAILABLE


def test_failure_semantics_verification_failed_triggers_bounded_retry() -> None:
    adapter = MockSpecialistAgentAdapter()
    adapter.set_fail_verification(True)  # Forces verification status FAILED
    engine = DelegationEngine(adapter, max_retries=2)

    req = DelegationRequest(
        delegation_id="del-retry-01",
        parent_task_id="st-02",
        executive_twin_id="twin-cmo-01",
        specialist_id="spec-dev-01",
        objective="Build feature",
        task="Build task",
        expected_output="Feature code",
        required_evidence_categories=[EvidenceCategory.ARTIFACT],
    )

    result, decision = engine.execute_and_review(req)
    # After bounded retries (max_retries = 2), outcome should report revision required or specialist failure
    assert decision.outcome in [
        ExecutiveReviewOutcome.REVISION_REQUIRED,
        ExecutiveReviewOutcome.SPECIALIST_FAILURE,
    ]
