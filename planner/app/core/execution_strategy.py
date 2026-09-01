"""
Planner — Execution Strategy

Determines execution mode (SEQUENTIAL / PARALLEL) for each step
based on the computed parallel groups.
"""
from __future__ import annotations

from app.models.plan import PlanStep, ExecutionMode


def apply_execution_strategy(
    steps: list[PlanStep],
    parallel_groups: list[list[str]],
) -> list[PlanStep]:
    """
    Update ExecutionMode on each step based on parallel group membership.

    A step is marked PARALLEL when it belongs to a group with more than one
    step (i.e. it can run concurrently with peer steps in the same wave).

    Returns the updated steps list (mutates in place and returns).
    """
    # Build step_id → group size mapping
    group_sizes: dict[str, int] = {}
    for group in parallel_groups:
        size = len(group)
        for sid in group:
            group_sizes[sid] = size

    for step in steps:
        size = group_sizes.get(step.step_id, 1)
        step.execution_mode = (
            ExecutionMode.PARALLEL if size > 1 else ExecutionMode.SEQUENTIAL
        )

    return steps
