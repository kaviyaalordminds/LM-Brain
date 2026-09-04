import pytest
from executive_twins.execution.review_engine import ReviewEngine
from executive_twins.schemas.common import ExecutiveReviewOutcome
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
)


def test_review_engine_approves_valid_evidence() -> None:
    req = DelegationRequest(
        delegation_id="del-01",
        parent_task_id="st-01",
        executive_twin_id="twin-cmo-01",
        specialist_id="spec-design-01",
        objective="Create UI mockup",
        task="UI mockup design",
        expected_output="UI artifact",
        required_evidence_categories=[EvidenceCategory.ARTIFACT, EvidenceCategory.EXECUTION_LOG],
    )

    evidence = EvidenceSet(
        items=[
            ArtifactEvidence(evidence_id="ev-1", artifact_uri="file:///mockup.png", mime_type="image/png"),
            ExecutionLogEvidence(evidence_id="ev-2", execution_id="ex-1", log_snippet="Design generated"),
        ]
    )

    result = DelegationResult(
        delegation_id="del-01",
        specialist_id="spec-design-01",
        status="SUCCESS",
        output="Mockup completed",
        artifacts=["file:///mockup.png"],
        evidence=evidence,
    )

    decision = ReviewEngine.evaluate_result(req, result)
    assert decision.outcome == ExecutiveReviewOutcome.APPROVED


def test_review_engine_rejects_missing_required_evidence() -> None:
    req = DelegationRequest(
        delegation_id="del-02",
        parent_task_id="st-02",
        executive_twin_id="twin-cmo-01",
        specialist_id="spec-dev-01",
        objective="Build app backend",
        task="Backend build",
        expected_output="Backend code",
        required_evidence_categories=[EvidenceCategory.ARTIFACT, EvidenceCategory.EXECUTION_LOG],
    )

    # Empty evidence set (pure text response)
    result = DelegationResult(
        delegation_id="del-02",
        specialist_id="spec-dev-01",
        status="SUCCESS",
        output="Backend build completed successfully",
        artifacts=[],
        evidence=EvidenceSet(items=[]),
    )

    decision = ReviewEngine.evaluate_result(req, result)
    assert decision.outcome == ExecutiveReviewOutcome.MORE_EVIDENCE_REQUIRED
    assert "ARTIFACT" in decision.missing_evidence or "EXECUTION_LOG" in decision.missing_evidence
