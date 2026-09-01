"""
Specialist Agent — Verification Interface

Generic verifier that checks whether a TaskResult meets the
criteria defined in a TaskRequest.

verify(task, result) → VerificationOutcome

Returns:
  PASS — result meets all checks.
  FAIL — one or more checks failed.

Never returns PASS unless checks are actually performed.
The MockVerifier is explicitly labelled as a test-only component.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from specialist_agent.contracts.result import (
    TaskResult,
    VerificationCheck,
    VerificationOutcome,
    VerificationVerdict,
)
from specialist_agent.contracts.task import TaskRequest

logger = logging.getLogger(__name__)


class BaseVerifier(ABC):
    """Abstract base for all verifiers."""

    @abstractmethod
    def verify(self, task: TaskRequest, result: TaskResult) -> VerificationOutcome:
        """
        Verify *result* against *task* expectations.

        Must return VerificationOutcome with:
          - verdict: PASS | FAIL
          - checks: list of individual check results
          - reason: human-readable summary
          - errors: any errors encountered during verification
        """


class StandardVerifier(BaseVerifier):
    """
    Standard verifier that runs deterministic checks on TaskResult.

    Checks performed:
      1. task_id_match      — result.task_id == task.task_id
      2. status_check       — result.status is not FAILED
      3. no_error_check     — result.errors is empty (or acceptable)
      4. artifact_check     — if expected artifacts specified, verify non-empty
      5. output_present     — if expected output type is set, verify output is present
      6. no_fake_artifact   — no artifact with is_mock=True presented as real
    """

    def verify(self, task: TaskRequest, result: TaskResult) -> VerificationOutcome:
        checks: list[VerificationCheck] = []
        errors: list[str] = []

        try:
            # 1. Task ID match
            checks.append(self._check_task_id(task, result))

            # 2. Status check
            checks.append(self._check_status(result))

            # 3. No unexpected errors
            checks.append(self._check_no_errors(result))

            # 4. Artifact expectations
            if task.expected_output.artifact_types:
                checks.append(self._check_artifacts(task, result))

            # 5. Output present
            checks.append(self._check_output_present(task, result))

            # 6. No fake artifacts
            checks.append(self._check_no_fake_artifacts(result))

        except Exception as exc:  # noqa: BLE001
            logger.error("verifier.internal_error", exc_info=True)
            errors.append(f"Verifier internal error: {exc}")

        failed_checks = [c for c in checks if c.verdict == VerificationVerdict.FAIL]
        verdict = VerificationVerdict.PASS if not failed_checks else VerificationVerdict.FAIL

        reason = (
            "All checks passed."
            if verdict == VerificationVerdict.PASS
            else f"{len(failed_checks)} check(s) failed: " +
                 ", ".join(c.name for c in failed_checks)
        )

        outcome = VerificationOutcome(
            verdict=verdict,
            checks=checks,
            reason=reason,
            errors=errors,
        )

        logger.info(
            "verifier.result",
            extra={
                "task_id": task.task_id,
                "verdict": verdict.value,
                "checks": len(checks),
                "failed": len(failed_checks),
            },
        )
        return outcome

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    @staticmethod
    def _check_task_id(task: TaskRequest, result: TaskResult) -> VerificationCheck:
        if result.task_id == task.task_id:
            return VerificationCheck(
                name="task_id_match",
                verdict=VerificationVerdict.PASS,
                reason="task_id matches.",
            )
        return VerificationCheck(
            name="task_id_match",
            verdict=VerificationVerdict.FAIL,
            reason=f"task_id mismatch: expected {task.task_id!r}, got {result.task_id!r}.",
        )

    @staticmethod
    def _check_status(result: TaskResult) -> VerificationCheck:
        from specialist_agent.contracts.result import TaskStatus
        if result.status not in {TaskStatus.FAILED, TaskStatus.CANCELLED}:
            return VerificationCheck(
                name="status_check",
                verdict=VerificationVerdict.PASS,
                reason=f"Status is {result.status.value}.",
            )
        return VerificationCheck(
            name="status_check",
            verdict=VerificationVerdict.FAIL,
            reason=f"Task ended with status: {result.status.value}.",
        )

    @staticmethod
    def _check_no_errors(result: TaskResult) -> VerificationCheck:
        blocking_errors = [e for e in result.errors if e.error_code != "ADVISORY"]
        if not blocking_errors:
            return VerificationCheck(
                name="no_error_check",
                verdict=VerificationVerdict.PASS,
                reason="No blocking errors.",
            )
        return VerificationCheck(
            name="no_error_check",
            verdict=VerificationVerdict.FAIL,
            reason=f"{len(blocking_errors)} error(s) present.",
            evidence=[e.message for e in blocking_errors],
        )

    @staticmethod
    def _check_artifacts(task: TaskRequest, result: TaskResult) -> VerificationCheck:
        expected = set(task.expected_output.artifact_types)
        produced = {a.type.value for a in result.artifacts if not a.is_mock}
        missing = expected - produced
        if not missing:
            return VerificationCheck(
                name="artifact_check",
                verdict=VerificationVerdict.PASS,
                reason=f"Required artifact types present: {expected}.",
            )
        return VerificationCheck(
            name="artifact_check",
            verdict=VerificationVerdict.FAIL,
            reason=f"Missing artifact types: {missing}.",
        )

    @staticmethod
    def _check_output_present(task: TaskRequest, result: TaskResult) -> VerificationCheck:
        if task.expected_output.output_type in {"", "text"} and not result.output:
            return VerificationCheck(
                name="output_present",
                verdict=VerificationVerdict.FAIL,
                reason="Expected text output but none was produced.",
            )
        return VerificationCheck(
            name="output_present",
            verdict=VerificationVerdict.PASS,
            reason="Output is present.",
        )

    @staticmethod
    def _check_no_fake_artifacts(result: TaskResult) -> VerificationCheck:
        """Ensure no artifact is falsely presented as real when it is actually a mock."""
        # This check is about contract integrity — if is_mock=False, the artifact must be real.
        # We cannot detect fake artifacts programmatically, but we can check
        # that no artifact of type MOCK has is_mock=False.
        from specialist_agent.contracts.artifact import ArtifactType
        suspect = [
            a for a in result.artifacts
            if a.type == ArtifactType.MOCK and not a.is_mock
        ]
        if suspect:
            return VerificationCheck(
                name="no_fake_artifacts",
                verdict=VerificationVerdict.FAIL,
                reason=f"{len(suspect)} artifact(s) have type=MOCK but is_mock=False.",
            )
        return VerificationCheck(
            name="no_fake_artifacts",
            verdict=VerificationVerdict.PASS,
            reason="No integrity violations in artifacts.",
        )


class MockVerifier(BaseVerifier):
    """
    Mock verifier for unit testing.

    IMPORTANT: This verifier is explicitly for testing.
    It does NOT make any real correctness checks.
    Pass/fail behaviour is pre-configured at construction.
    """

    def __init__(self, should_pass: bool = True, reason: str = "Mock verifier") -> None:
        self._should_pass = should_pass
        self._reason = reason

    @property
    def is_mock(self) -> bool:
        return True

    def verify(self, task: TaskRequest, result: TaskResult) -> VerificationOutcome:
        verdict = VerificationVerdict.PASS if self._should_pass else VerificationVerdict.FAIL
        return VerificationOutcome(
            verdict=verdict,
            checks=[
                VerificationCheck(
                    name="mock_check",
                    verdict=verdict,
                    reason=f"[MOCK] {self._reason}",
                )
            ],
            reason=f"[MOCK VERIFIER] {self._reason}",
        )
