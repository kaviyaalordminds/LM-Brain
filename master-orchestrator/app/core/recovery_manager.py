"""
Master Orchestrator — Recovery Manager

Analyzes failures and decides on recovery action.
Key principle: never restart the entire workflow for a single step failure.
Preserve completed work; only recover the failed portion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.policies.failure_policy import FailureType
from app.policies.retry_policy import REQUIRES_REPLAN, NON_RETRYABLE, RetryPolicy


class RecoveryDecision(str, Enum):
    RETRY = "RETRY"
    REPLAN = "REPLAN"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    TERMINATE = "TERMINATE"


@dataclass
class RecoveryAnalysis:
    decision: RecoveryDecision
    step_id: str
    failure_type: FailureType
    attempt_number: int
    reason: str
    reusable_artifacts: list[str]
    downstream_blocked: list[str]


class RecoveryManager:
    """
    Analyzes step failures and determines the appropriate recovery action.

    Decision matrix:
    - NON_RETRYABLE (PERMISSION_DENIED, CANCELLED) → BLOCK or TERMINATE
    - REQUIRES_REPLAN (CONTRACT_VIOLATION, VERIFICATION_FAILED) → REPLAN
    - Retry budget remains → RETRY
    - Retry budget exhausted → REPLAN
    - Unknown + budget remains → RETRY
    """

    def analyze_failure(
        self,
        step_id: str,
        failure_type: FailureType | str,
        attempt_number: int,
        max_retries: int,
    ) -> RecoveryDecision:
        """
        Determine the recovery action for a failed step.

        Never silently falls back — always returns an explicit decision.
        """
        if isinstance(failure_type, str):
            try:
                failure_type = FailureType(failure_type)
            except ValueError:
                failure_type = FailureType.UNKNOWN

        # Non-retryable failures go straight to block/terminate
        if failure_type in NON_RETRYABLE:
            if failure_type == FailureType.CANCELLED:
                return RecoveryDecision.TERMINATE
            return RecoveryDecision.BLOCK

        # Failures that require replanning instead of simple retry
        if failure_type in REQUIRES_REPLAN:
            return RecoveryDecision.REPLAN

        # Check retry budget
        if RetryPolicy.should_retry(failure_type, attempt_number, max_retries):
            return RecoveryDecision.RETRY

        # Budget exhausted — request replan
        return RecoveryDecision.REPLAN

    def compute_recovery_context(self, execution) -> dict:
        """
        Summarize the current execution state for Planner recovery plan request.

        Includes: completed steps (reusable), failed steps, blocked steps,
        and artifact IDs that are safe to reuse.
        """
        return {
            "original_user_request": execution.user_request,
            "plan_id": execution.plan_id,
            "plan_version": execution.plan_version,
            "completed_steps": list(execution.completed_steps),
            "failed_steps": list(execution.failed_steps),
            "blocked_steps": list(execution.blocked_steps),
            "running_steps": list(execution.running_steps),
            "reusable_artifacts": list(execution.artifacts),
            "error": execution.error,
        }

    def compute_downstream_blocked(
        self,
        failed_step_id: str,
        dependencies: dict[str, list[str]],
    ) -> list[str]:
        """
        Find all steps that are blocked due to a failed step dependency.

        Uses BFS from the failed step across the dependency graph.
        """
        blocked = []
        queue = [failed_step_id]
        visited = {failed_step_id}

        while queue:
            current = queue.pop(0)
            for step_id, deps in dependencies.items():
                if current in deps and step_id not in visited:
                    blocked.append(step_id)
                    visited.add(step_id)
                    queue.append(step_id)

        return blocked

    def isolate_failure(
        self,
        failed_step_id: str,
        dependencies: dict[str, list[str]],
        completed_steps: list[str],
        all_step_ids: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Isolate failure: partition steps into affected (blocked/needing recovery)
        and preserved (already completed or completely independent).
        """
        downstream = set(self.compute_downstream_blocked(failed_step_id, dependencies))
        downstream.add(failed_step_id)

        affected = [s for s in all_step_ids if s in downstream]
        preserved = [s for s in all_step_ids if s not in downstream and s in completed_steps]

        return affected, preserved

    def create_replan_metadata(
        self,
        execution,
        failed_step_id: str,
        failure_reason: str,
        new_plan_id: str,
        new_plan_version: int,
        affected_steps: list[str],
        preserved_steps: list[str]
    ) -> dict:
        """Create canonical recovery replan record for persistence in plan_versions."""
        import datetime
        return {
            "parent_plan_id": execution.plan_id,
            "parent_plan_version": execution.plan_version,
            "new_plan_id": new_plan_id,
            "new_plan_version": new_plan_version,
            "recovery_reason": failure_reason,
            "trigger_step_id": failed_step_id,
            "affected_steps": affected_steps,
            "preserved_steps": preserved_steps,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }


