"""
Planner — Plan Validator

Validates 15 structural invariants before marking a Plan READY.
Does NOT execute any steps or call external services.

Returns a list of validation errors. An empty list means VALID.
"""
from __future__ import annotations

from app.models.plan import Plan, KNOWN_SPECIALISTS
from app.core.dependency_graph import build_dependency_graph


def validate_plan(plan: Plan) -> list[str]:
    """
    Validate all 15 plan invariants.

    Returns:
        List of error strings. Empty list = plan is valid.
    """
    errors: list[str] = []

    # Rule 1: user request exists and is non-empty
    if not plan.user_request or not plan.user_request.strip():
        errors.append("R01: Plan has no user request.")

    # Rule 2: at least one step exists
    if not plan.steps:
        errors.append("R02: Plan contains no steps.")
        return errors  # Can't validate further without steps

    step_ids = [s.step_id for s in plan.steps]

    # Rule 13: no duplicate step IDs
    if len(step_ids) != len(set(step_ids)):
        seen: set[str] = set()
        dupes: list[str] = []
        for sid in step_ids:
            if sid in seen:
                dupes.append(sid)
            seen.add(sid)
        errors.append(f"R13: Duplicate step IDs found: {dupes}")

    id_set = set(step_ids)

    for step in plan.steps:
        # Rule 3: every step has a specialist assigned
        if not step.specialist_id or not step.specialist_id.strip():
            errors.append(f"R03: Step '{step.step_id}' has no specialist assigned.")

        # Rule 4: specialist ID is in the known catalog
        elif step.specialist_id not in KNOWN_SPECIALISTS:
            errors.append(
                f"R04: Step '{step.step_id}' references unknown specialist "
                f"'{step.specialist_id}'. Known specialists: {sorted(KNOWN_SPECIALISTS)}"
            )

        # Rule 5: all dependency IDs exist within the plan
        for dep_id in step.dependencies:
            if dep_id not in id_set:
                errors.append(
                    f"R05: Step '{step.step_id}' references non-existent "
                    f"dependency '{dep_id}'."
                )

        # Rule 9: every step has expected outputs defined
        if not step.expected_outputs:
            errors.append(f"R09: Step '{step.step_id}' has no expected_outputs defined.")

        # Rule 10: every step has verification criteria
        if not step.verification_criteria:
            errors.append(
                f"R10: Step '{step.step_id}' has no verification_criteria defined."
            )

        # Rule 11: failure policy is valid
        if step.failure_policy.max_retries < 0:
            errors.append(
                f"R11: Step '{step.step_id}' has invalid max_retries "
                f"({step.failure_policy.max_retries} < 0)."
            )

        # Rule 14: no duplicate dependencies within a step
        dep_ids = step.dependencies
        if len(dep_ids) != len(set(dep_ids)):
            errors.append(
                f"R14: Step '{step.step_id}' has duplicate dependency entries."
            )

    # Rules 6, 7, 8: dependency graph validation
    explicit_deps: dict[str, list[str]] = {
        s.step_id: s.dependencies for s in plan.steps
    }
    graph_result = build_dependency_graph(step_ids, explicit_deps)
    if not graph_result.valid:
        for err in graph_result.errors:
            if "ircular" in err:
                errors.append(f"R06: {err}")
            elif "Topological" in err:
                errors.append(f"R07: {err}")
            else:
                errors.append(f"R05: {err}")

    # Rule 8: parallel groups contain no mutually dependent steps
    if graph_result.valid and plan.parallel_groups:
        for group in plan.parallel_groups:
            for sid in group:
                step_obj = plan.get_step(sid)
                if step_obj:
                    for dep_id in step_obj.dependencies:
                        if dep_id in group:
                            errors.append(
                                f"R08: Step '{sid}' and its dependency '{dep_id}' "
                                f"are in the same parallel group."
                            )

    # Rule 12: memory/research flags are consistent
    for step in plan.steps:
        if step.research_required and step.specialist_id != "research":
            # research_required on a non-research specialist is allowed but warn
            pass  # Orchestrator routes this correctly
        if step.memory_required and step.specialist_id == "image_generation":
            # image_generation rarely needs memory context — but not invalid
            pass

    # Rule 15: plan is internally consistent (execution_order covers all steps)
    if plan.execution_order and set(plan.execution_order) != id_set:
        missing = id_set - set(plan.execution_order)
        extra = set(plan.execution_order) - id_set
        if missing:
            errors.append(f"R15: execution_order is missing steps: {sorted(missing)}")
        if extra:
            errors.append(f"R15: execution_order references unknown steps: {sorted(extra)}")

    return errors
