"""
Planner Agent — Core Service Coordinator

Coordinates the full planning lifecycle pipeline:
  USER REQUEST
       ↓
  UNDERSTAND REQUIREMENT & DETECT CAPABILITIES
       ↓
  DECOMPOSE INTO TASKS
       ↓
  ASSIGN SPECIALISTS
       ↓
  BUILD DEPENDENCY GRAPH (DAG, cycle detection)
       ↓
  DETERMINE PARALLEL / SEQUENTIAL EXECUTION
       ↓
  DEFINE INPUTS / OUTPUTS
       ↓
  DEFINE VERIFICATION CRITERIA
       ↓
  DEFINE FAILURE / RETRY POLICY
       ↓
  VALIDATE PLAN (15 structural invariants)
       ↓
  STORE PLAN
       ↓
  RETURN EXECUTABLE PLAN (READY or DRAFT with errors)

The Planner MUST NOT execute any steps, call models, or touch memory/tools.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Callable

from app.core.decomposition import decompose
from app.core.dependency_graph import build_dependency_graph
from app.core.execution_strategy import apply_execution_strategy
from app.core.failure_policy import assign_failure_policies, build_global_failure_policy
from app.core.store import BasePlanStore, InMemoryPlanStore
from app.core.validation import validate_plan
from app.core.verification import assign_verification_criteria, build_global_verification
from app.models.plan import Plan, PlanRequest, PlanStatus

logger = logging.getLogger("planner")


class Planner:
    """
    Planner Agent coordinator.

    Produces structured, validated execution plans for the future Master Orchestrator.
    Does not execute tasks, invoke specialists, call models, or modify storage outside PlanStore.
    """

    def __init__(
        self,
        store: BasePlanStore | None = None,
        id_generator: Callable[[], str] | None = None,
    ) -> None:
        self.store: BasePlanStore = store if store is not None else InMemoryPlanStore()
        self._id_generator: Callable[[], str] = (
            id_generator if id_generator is not None else lambda: f"plan-{uuid.uuid4().hex[:12]}"
        )

    def create_plan(self, request: PlanRequest) -> Plan:
        """
        Create and validate an execution plan from a PlanRequest.

        Returns a Plan in READY status if all 15 validation rules pass,
        or DRAFT status with validation_errors populated if any rule fails.
        """
        plan_id = self._id_generator()
        now = datetime.now(timezone.utc)

        logger.info(
            "EVENT=PLAN_REQUESTED plan_id=%s request_id=%s request_len=%d",
            plan_id,
            request.request_id,
            len(request.user_request),
        )

        # ------------------------------------------------------------------
        # 1. Decomposition: Capability detection & Specialist assignment
        # ------------------------------------------------------------------
        steps = decompose(request.user_request)
        logger.info(
            "EVENT=PLAN_DECOMPOSED plan_id=%s step_count=%d specialists=%s",
            plan_id,
            len(steps),
            [s.specialist_id for s in steps],
        )

        logger.info(
            "EVENT=SPECIALISTS_ASSIGNED plan_id=%s assignments=%s",
            plan_id,
            {s.step_id: s.specialist_id for s in steps},
        )

        # ------------------------------------------------------------------
        # 2. Dependency Graph Resolution
        # ------------------------------------------------------------------
        step_ids = [s.step_id for s in steps]
        explicit_deps = request.constraints.get("explicit_dependencies") if request.constraints else None
        graph_res = build_dependency_graph(step_ids, explicit_dependencies=explicit_deps)

        # Populate dependencies on each PlanStep
        for step in steps:
            step.dependencies = graph_res.dependencies.get(step.step_id, [])

        logger.info(
            "EVENT=DEPENDENCIES_RESOLVED plan_id=%s valid_dag=%s parallel_groups=%d",
            plan_id,
            graph_res.valid,
            len(graph_res.parallel_groups),
        )

        # ------------------------------------------------------------------
        # 3. Execution Strategy (Mark PARALLEL vs SEQUENTIAL)
        # ------------------------------------------------------------------
        steps = apply_execution_strategy(steps, graph_res.parallel_groups)

        # ------------------------------------------------------------------
        # 4. Verification Criteria (Per-step and Global)
        # ------------------------------------------------------------------
        steps = assign_verification_criteria(steps)
        global_verification = build_global_verification(steps)

        # ------------------------------------------------------------------
        # 5. Failure / Retry Policies (Per-step and Global)
        # ------------------------------------------------------------------
        steps = assign_failure_policies(steps)
        global_failure = build_global_failure_policy(steps)

        # ------------------------------------------------------------------
        # 6. Build Initial Plan Object
        # ------------------------------------------------------------------
        plan = Plan(
            plan_id=plan_id,
            request_id=request.request_id,
            user_request=request.user_request,
            status=PlanStatus.DRAFT,
            created_at=now,
            updated_at=now,
            steps=steps,
            dependencies=graph_res.dependencies,
            execution_order=graph_res.execution_order,
            parallel_groups=graph_res.parallel_groups,
            global_verification_criteria=global_verification,
            global_failure_policy=global_failure,
            metadata={
                "context": request.context,
                "constraints": request.constraints,
                "expected_output": request.expected_output,
            },
        )

        # ------------------------------------------------------------------
        # 7. Plan Validation (15 Invariants)
        # ------------------------------------------------------------------
        validation_errors = validate_plan(plan)
        plan.validation_errors = validation_errors

        if not validation_errors and graph_res.valid:
            plan.status = PlanStatus.READY
            logger.info("EVENT=PLAN_VALIDATED plan_id=%s status=READY", plan_id)
            logger.info("EVENT=PLAN_CREATED plan_id=%s status=READY steps=%d", plan_id, len(steps))
        else:
            plan.status = PlanStatus.DRAFT
            all_errors = list(validation_errors) + (graph_res.errors if not graph_res.valid else [])
            plan.validation_errors = all_errors
            logger.warning("EVENT=PLAN_REJECTED plan_id=%s errors=%s", plan_id, all_errors)

        # ------------------------------------------------------------------
        # 8. Store in PlanStore
        # ------------------------------------------------------------------
        self.store.create(plan)
        return plan

    def get_plan(self, plan_id: str) -> Plan | None:
        """Retrieve a stored plan by ID."""
        return self.store.get(plan_id)

    def validate_existing_plan(self, plan_id: str) -> tuple[bool, list[str]]:
        """
        Validate an existing plan in storage.
        Returns (is_valid, error_list).
        """
        plan = self.store.get(plan_id)
        if plan is None:
            return False, [f"Plan '{plan_id}' not found."]
        errors = validate_plan(plan)
        return len(errors) == 0, errors
