"""
Planner ↔ Specialist Contract Adapter

Converts between Planner models (PlanStep) and Specialist Agent models (TaskRequest / TaskResult).
Pure contract transformation — NEVER executes any agent, tool, model, or network request.
"""
from __future__ import annotations

from typing import Any

from app.models.plan import PlanStep, StepStatus


def map_plan_step_to_specialist_task_dict(
    step: PlanStep,
    context_items: list[dict[str, Any]] | None = None,
    trust_level: str = "RETRIEVED",
) -> dict[str, Any]:
    """
    Transform a PlanStep into the canonical TaskRequest dictionary format
    compatible with `specialist_agent.contracts.task.TaskRequest`.

    Ensures zero loss of verification criteria, dependencies, expected inputs/outputs,
    or execution constraints.
    """
    # Infer artifact category
    artifact_types = []
    for out in step.expected_outputs:
        out_lower = out.lower()
        if "code" in out_lower or "script" in out_lower or "component" in out_lower:
            artifact_types.append("code")
        elif "image" in out_lower or "picture" in out_lower:
            artifact_types.append("image")
        elif "schema" in out_lower or "ddl" in out_lower:
            artifact_types.append("schema")
        elif "docker" in out_lower or "pipeline" in out_lower or "config" in out_lower:
            artifact_types.append("config")
        elif "report" in out_lower or "audit" in out_lower:
            artifact_types.append("report")
        elif "test" in out_lower:
            artifact_types.append("test_result")
        elif "documentation" in out_lower or "guide" in out_lower or "finding" in out_lower:
            artifact_types.append("document")
        else:
            artifact_types.append("document")

    exec_mode = (
        step.execution_mode.value
        if hasattr(step.execution_mode, "value")
        else str(step.execution_mode)
    )
    fail_action = (
        step.failure_policy.failure_action.value
        if hasattr(step.failure_policy.failure_action, "value")
        else str(step.failure_policy.failure_action)
    )

    return {
        "task_id": step.step_id,
        "agent_type": step.specialist_id,
        "instruction": f"{step.title}: {step.description}",
        "context": {
            "context_items": context_items or [],
            "trust_level": trust_level,
            "extra": {
                "expected_inputs": step.expected_inputs,
                "memory_required": step.memory_required,
                "research_required": step.research_required,
            },
        },
        "constraints": {
            "max_retries": step.failure_policy.max_retries,
            "require_verification": True,
            "dry_run": False,
        },
        "expected_output": {
            "output_type": "code" if "code" in artifact_types else "text",
            "artifact_types": list(set(artifact_types)),
            "description": "; ".join(step.expected_outputs),
        },
        "metadata": {
            "step_id": step.step_id,
            "dependencies": step.dependencies,
            "execution_mode": exec_mode,
            "verification_criteria": step.verification_criteria,
            "failure_action": fail_action,
            "required_capabilities": step.required_capabilities,
        },
    }


def map_task_result_dict_to_step_status(result_dict: dict[str, Any]) -> StepStatus:
    """
    Map a Specialist Agent TaskResult dictionary to a PlanStep StepStatus.
    """
    raw_status = str(result_dict.get("status", "")).lower()
    if raw_status == "completed":
        return StepStatus.COMPLETED
    elif raw_status == "failed":
        return StepStatus.FAILED
    elif raw_status == "running":
        return StepStatus.RUNNING
    elif raw_status == "cancelled":
        return StepStatus.SKIPPED
    return StepStatus.PENDING
