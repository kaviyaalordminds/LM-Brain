from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional

from executive_twins.schemas.common import VerificationStatus
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    TestEvidence,
)


class ISpecialistAgentAdapter(ABC):
    """
    Interface for dispatching structured delegation requests to Specialist Execution engines.
    Executive Twins NEVER execute specialist tools directly.
    """

    @abstractmethod
    def execute_delegation(self, request: DelegationRequest) -> DelegationResult:
        """Execute a structured delegation request and return system evidence."""
        pass


class MockSpecialistAgentAdapter(ISpecialistAgentAdapter):
    """
    DEV_TEST_ONLY_ADAPTER: Mock implementation of specialist execution for testing.
    Generates deterministic system execution outputs and evidence.
    """

    def __init__(self) -> None:
        self._custom_responses: Dict[str, DelegationResult] = {}
        self._should_fail_verification: bool = False
        self._should_omit_evidence: bool = False

    def set_custom_response(self, specialist_id: str, result: DelegationResult) -> None:
        self._custom_responses[specialist_id] = result

    def set_fail_verification(self, fail: bool) -> None:
        self._should_fail_verification = fail

    def set_omit_evidence(self, omit: bool) -> None:
        self._should_omit_evidence = omit

    def execute_delegation(self, request: DelegationRequest) -> DelegationResult:
        if request.specialist_id in self._custom_responses:
            return self._custom_responses[request.specialist_id]

        evidence_set = EvidenceSet()

        if not self._should_omit_evidence:
            # Add artifact evidence if ARTIFACT is required or standard
            if EvidenceCategory.ARTIFACT in request.required_evidence_categories or not request.required_evidence_categories:
                evidence_set.items.append(
                    ArtifactEvidence(
                        evidence_id=f"ev-art-{request.delegation_id}",
                        artifact_uri=f"file:///outputs/artifact_{request.delegation_id}.txt",
                        mime_type="text/plain",
                        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        description=f"Generated output artifact for task '{request.task}'",
                    )
                )

            # Add execution log evidence if EXECUTION_LOG is required
            if EvidenceCategory.EXECUTION_LOG in request.required_evidence_categories or not request.required_evidence_categories:
                evidence_set.items.append(
                    ExecutionLogEvidence(
                        evidence_id=f"ev-log-{request.delegation_id}",
                        execution_id=f"exec-{request.delegation_id}",
                        log_snippet=f"[INFO] Executed subtask '{request.task}' for specialist '{request.specialist_id}'. Exit code 0.",
                        exit_code=0,
                        description="Execution trace log",
                    )
                )

            # Add test evidence if TEST category requested
            if EvidenceCategory.TEST in request.required_evidence_categories:
                evidence_set.items.append(
                    TestEvidence(
                        evidence_id=f"ev-test-{request.delegation_id}",
                        suite_name=f"suite-{request.delegation_id}",
                        tests_passed=5,
                        tests_failed=0,
                        report_uri=f"file:///reports/test_{request.delegation_id}.html",
                        description="Automated unit test execution suite report",
                    )
                )

        verification_status = VerificationStatus.VERIFIED if not self._should_fail_verification else VerificationStatus.FAILED
        status = "SUCCESS" if verification_status == VerificationStatus.VERIFIED else "FAILED"

        return DelegationResult(
            delegation_id=request.delegation_id,
            specialist_id=request.specialist_id,
            status=status,
            output=f"Specialist '{request.specialist_id}' successfully executed task: {request.task}",
            artifacts=[f"file:///outputs/artifact_{request.delegation_id}.txt"],
            evidence=evidence_set,
            confidence=0.95,
            errors=[] if verification_status == VerificationStatus.VERIFIED else ["Verification assertion failed."],
            verification_status=verification_status,
            completed_at=datetime.now(timezone.utc),
        )
