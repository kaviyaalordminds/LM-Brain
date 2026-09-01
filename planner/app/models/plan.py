"""
Planner Agent — Core Data Models

Strongly-typed Pydantic models for plans, steps, requests, and enums.
Supports camelCase serialization/deserialization with snake_case Python access.
These are the canonical contracts consumed by the future Master Orchestrator.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


# ---------------------------------------------------------------------------
# Base model with camelCase alias support and by-name population
# ---------------------------------------------------------------------------

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        use_enum_values=True,
    )


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class ExecutionMode(str, Enum):
    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"


class FailureAction(str, Enum):
    RETRY = "RETRY"
    BLOCK_DEPENDENTS = "BLOCK_DEPENDENTS"
    FAIL_PLAN = "FAIL_PLAN"


# ---------------------------------------------------------------------------
# Known Specialist IDs (catalog — references only, no implementations)
# ---------------------------------------------------------------------------

KNOWN_SPECIALISTS: set[str] = {
    "web_development",
    "image_generation",
    "backend",
    "database",
    "api_integration",
    "security",
    "testing",
    "devops",
    "ai_ml",
    "research",
}


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class FailurePolicy(CamelModel):
    """Defines how failure of a step should be handled by the Orchestrator."""

    retry_allowed: bool = Field(default=True)
    max_retries: int = Field(default=2, ge=0)
    failure_action: FailureAction = Field(default=FailureAction.BLOCK_DEPENDENTS)


class GlobalFailurePolicy(CamelModel):
    """Global failure policy governing the overall plan execution."""

    abort_on_critical_failure: bool = Field(default=True)
    max_total_retries: int = Field(default=6, ge=0)
    failure_action: FailureAction = Field(default=FailureAction.FAIL_PLAN)


class GlobalVerificationCriteria(CamelModel):
    """Criteria the Orchestrator checks before marking the plan COMPLETED."""

    all_steps_completed: bool = Field(default=True)
    no_critical_verification_failure: bool = Field(default=True)
    all_required_artifacts_present: bool = Field(default=True)
    all_mandatory_dependencies_completed: bool = Field(default=True)
    custom_criteria: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# PlanStep
# ---------------------------------------------------------------------------

class PlanStep(CamelModel):
    """A single executable unit within the plan. Maps to one specialist agent."""

    step_id: str = Field(..., description="Unique identifier for this step within the plan.")
    title: str = Field(..., description="Short human-readable title.")
    description: str = Field(..., description="Detailed description of what this step should accomplish.")
    specialist_id: str = Field(..., description="ID of the specialist agent responsible for this step.")
    required_capabilities: list[str] = Field(
        default_factory=list,
        description="Capabilities required from the specialist.",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="step_ids that must COMPLETE before this step can start.",
    )
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.SEQUENTIAL,
        description="Whether this step can run in parallel with peer steps.",
    )
    memory_required: bool = Field(
        default=False,
        description="Set true when this step needs pre-loaded context from Memory Agent.",
    )
    research_required: bool = Field(
        default=False,
        description="Set true when this step needs external research before execution.",
    )
    expected_inputs: list[str] = Field(
        default_factory=list,
        description="Inputs expected from dependencies or context.",
    )
    expected_outputs: list[str] = Field(
        default_factory=list,
        description="Artifacts or data this step must produce.",
    )
    verification_criteria: list[str] = Field(
        default_factory=list,
        description="Conditions the Orchestrator checks after step execution.",
    )
    failure_policy: FailurePolicy = Field(default_factory=FailurePolicy)
    status: StepStatus = Field(default=StepStatus.PENDING)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

class Plan(CamelModel):
    """Executable plan produced by the Planner and consumed by the Orchestrator."""

    plan_id: str = Field(..., description="Unique plan identifier.")
    request_id: str = Field(..., description="Original request ID from PlanRequest.")
    user_request: str = Field(..., description="Original natural-language user request.")
    status: PlanStatus = Field(default=PlanStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    steps: list[PlanStep] = Field(default_factory=list)
    dependencies: dict[str, list[str]] = Field(
        default_factory=dict,
        description="step_id -> list of step_ids it depends on.",
    )
    execution_order: list[str] = Field(
        default_factory=list,
        description="Topologically sorted step_ids (sequential fallback order).",
    )
    parallel_groups: list[list[str]] = Field(
        default_factory=list,
        description="Groups of step_ids that may execute concurrently.",
    )
    global_verification_criteria: GlobalVerificationCriteria = Field(
        default_factory=GlobalVerificationCriteria
    )
    global_failure_policy: GlobalFailurePolicy = Field(default_factory=GlobalFailurePolicy)
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Populated when validation fails.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_step(self, step_id: str) -> PlanStep | None:
        return next((s for s in self.steps if s.step_id == step_id), None)


# ---------------------------------------------------------------------------
# PlanRequest (API input)
# ---------------------------------------------------------------------------

class PlanRequest(CamelModel):
    """Input contract sent by callers to request plan creation."""

    request_id: str = Field(
        default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}",
        description="Caller-supplied or auto-generated request ID.",
    )
    user_request: str = Field(..., description="Natural-language user request.")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional context hints (existing architecture, project info, etc).",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional planning constraints.",
    )
    expected_output: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional description of expected outputs.",
    )

    @field_validator("user_request")
    @classmethod
    def user_request_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("userRequest must not be empty or whitespace.")
        return v.strip()


# ---------------------------------------------------------------------------
# API Response / Error Models
# ---------------------------------------------------------------------------

class PlanStatusResponse(CamelModel):
    plan_id: str
    request_id: str
    status: PlanStatus
    step_count: int
    completed_steps: int
    failed_steps: int
    validation_errors: list[str] = Field(default_factory=list)


class PlanValidationResponse(CamelModel):
    plan_id: str
    valid: bool
    status: PlanStatus
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ErrorResponse(CamelModel):
    error_code: str
    message: str
    details: list[str] = Field(default_factory=list)
    request_id: str | None = None


class HealthResponse(CamelModel):
    status: str = "ok"
    service: str = "planner"
    version: str = "1.0.0"
