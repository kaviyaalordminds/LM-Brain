"""
Tests for 15 Plan Validation Rules in validate_plan().
"""
from __future__ import annotations

import pytest

from app.core.validation import validate_plan
from app.models.plan import (
    Plan,
    PlanStep,
    PlanStatus,
    StepStatus,
    ExecutionMode,
    FailurePolicy,
    FailureAction,
    GlobalFailurePolicy,
    GlobalVerificationCriteria,
)


def _make_valid_step(step_id: str, specialist_id: str = "backend", deps: list[str] | None = None) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        title=f"Step {step_id}",
        description=f"Description for {step_id}",
        specialist_id=specialist_id,
        required_capabilities=["server_side_apis"],
        dependencies=deps or [],
        execution_mode=ExecutionMode.SEQUENTIAL,
        expected_outputs=["Source code artifacts"],
        verification_criteria=["Endpoints exist", "Tests pass"],
        failure_policy=FailurePolicy(),
        status=StepStatus.PENDING,
    )


def _make_valid_plan(steps: list[PlanStep] | None = None) -> Plan:
    step_list = steps if steps is not None else [_make_valid_step("step-01-backend")]
    step_ids = [s.step_id for s in step_list]
    return Plan(
        plan_id="plan-test-001",
        request_id="req-test-001",
        user_request="Build a backend API service",
        status=PlanStatus.READY,
        steps=step_list,
        dependencies={s.step_id: s.dependencies for s in step_list},
        execution_order=step_ids,
        parallel_groups=[step_ids],
        global_verification_criteria=GlobalVerificationCriteria(),
        global_failure_policy=GlobalFailurePolicy(),
    )


class TestPlanValidation:
    def test_valid_plan_passes_all_rules(self):
        plan = _make_valid_plan()
        errors = validate_plan(plan)
        assert errors == []

    def test_r01_empty_user_request(self):
        plan = _make_valid_plan()
        plan.user_request = ""
        errors = validate_plan(plan)
        assert any("R01" in e for e in errors)

    def test_r02_no_steps_in_plan(self):
        plan = _make_valid_plan(steps=[])
        errors = validate_plan(plan)
        assert any("R02" in e for e in errors)

    def test_r03_missing_specialist_id(self):
        step = _make_valid_step("step-01")
        step.specialist_id = ""
        plan = _make_valid_plan(steps=[step])
        errors = validate_plan(plan)
        assert any("R03" in e for e in errors)

    def test_r04_unknown_specialist_id(self):
        step = _make_valid_step("step-01", specialist_id="quantum_wizard")
        plan = _make_valid_plan(steps=[step])
        errors = validate_plan(plan)
        assert any("R04" in e for e in errors)

    def test_r05_nonexistent_dependency(self):
        step = _make_valid_step("step-01", deps=["step-nonexistent"])
        plan = _make_valid_plan(steps=[step])
        errors = validate_plan(plan)
        assert any("R05" in e for e in errors)

    def test_r06_circular_dependency(self):
        step_a = _make_valid_step("step-A", deps=["step-B"])
        step_b = _make_valid_step("step-B", deps=["step-A"])
        plan = _make_valid_plan(steps=[step_a, step_b])
        errors = validate_plan(plan)
        assert any("R06" in e or "Circular" in e for e in errors)

    def test_r08_dependent_steps_in_same_parallel_group(self):
        step_a = _make_valid_step("step-A")
        step_b = _make_valid_step("step-B", deps=["step-A"])
        plan = _make_valid_plan(steps=[step_a, step_b])
        plan.parallel_groups = [["step-A", "step-B"]]  # Invalid: mutually dependent
        errors = validate_plan(plan)
        assert any("R08" in e for e in errors)

    def test_r09_missing_expected_outputs(self):
        step = _make_valid_step("step-01")
        step.expected_outputs = []
        plan = _make_valid_plan(steps=[step])
        errors = validate_plan(plan)
        assert any("R09" in e for e in errors)

    def test_r10_missing_verification_criteria(self):
        step = _make_valid_step("step-01")
        step.verification_criteria = []
        plan = _make_valid_plan(steps=[step])
        errors = validate_plan(plan)
        assert any("R10" in e for e in errors)

    def test_r11_negative_retries(self):
        step = _make_valid_step("step-01")
        step.failure_policy.max_retries = -1
        plan = _make_valid_plan(steps=[step])
        errors = validate_plan(plan)
        assert any("R11" in e for e in errors)

    def test_r13_duplicate_step_ids(self):
        step1 = _make_valid_step("step-01")
        step2 = _make_valid_step("step-01")  # Duplicate
        plan = _make_valid_plan(steps=[step1, step2])
        errors = validate_plan(plan)
        assert any("R13" in e for e in errors)

    def test_r14_duplicate_dependencies_in_step(self):
        step_a = _make_valid_step("step-A")
        step_b = _make_valid_step("step-B", deps=["step-A", "step-A"])
        plan = _make_valid_plan(steps=[step_a, step_b])
        errors = validate_plan(plan)
        assert any("R14" in e for e in errors)

    def test_r15_execution_order_missing_step(self):
        step_a = _make_valid_step("step-A")
        step_b = _make_valid_step("step-B")
        plan = _make_valid_plan(steps=[step_a, step_b])
        plan.execution_order = ["step-A"]  # Missing step-B
        errors = validate_plan(plan)
        assert any("R15" in e for e in errors)
