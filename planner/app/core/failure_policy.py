"""
Planner — Failure & Retry Policy Builder

Assigns per-step failure policies and builds the global failure policy.
The Planner only DEFINES policy. The Orchestrator EXECUTES it.
"""
from __future__ import annotations

from app.models.plan import (
    PlanStep,
    FailurePolicy,
    FailureAction,
    GlobalFailurePolicy,
)

# Specialists whose failure should fail the entire plan immediately
CRITICAL_SPECIALISTS: set[str] = {"database", "security"}

# Specialists that can be retried more aggressively
HIGH_RETRY_SPECIALISTS: set[str] = {"research", "api_integration"}


def assign_failure_policies(steps: list[PlanStep]) -> list[PlanStep]:
    """
    Assign per-step failure policy based on specialist type and criticality.

    Rules:
    - Critical specialists (database, security): failure_action = FAIL_PLAN
    - High-retry specialists (research, api_integration): max_retries = 3
    - All others: default (retry_allowed=True, max_retries=2, BLOCK_DEPENDENTS)
    """
    for step in steps:
        if step.specialist_id in CRITICAL_SPECIALISTS:
            step.failure_policy = FailurePolicy(
                retry_allowed=True,
                max_retries=2,
                failure_action=FailureAction.FAIL_PLAN,
            )
        elif step.specialist_id in HIGH_RETRY_SPECIALISTS:
            step.failure_policy = FailurePolicy(
                retry_allowed=True,
                max_retries=3,
                failure_action=FailureAction.BLOCK_DEPENDENTS,
            )
        else:
            step.failure_policy = FailurePolicy(
                retry_allowed=True,
                max_retries=2,
                failure_action=FailureAction.BLOCK_DEPENDENTS,
            )
    return steps


def build_global_failure_policy(steps: list[PlanStep]) -> GlobalFailurePolicy:
    """
    Build the global failure policy for the plan.
    Total retries = sum of per-step max_retries.
    """
    total_retries = sum(s.failure_policy.max_retries for s in steps)
    return GlobalFailurePolicy(
        abort_on_critical_failure=True,
        max_total_retries=max(total_retries, 6),
        failure_action=FailureAction.FAIL_PLAN,
    )
