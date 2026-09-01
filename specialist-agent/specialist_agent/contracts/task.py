"""
Specialist Agent — Task Contract

Strongly-typed input for every specialist agent task.
The future Master Orchestrator sends TaskRequest objects.
The specialist runtime consumes them — neither side knows
the other's internal implementation.

This contract is the ONLY communication boundary between
orchestrator and specialist.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator


class TaskContext(BaseModel):
    """
    Context block passed to the agent.

    context_items: Pre-retrieved memory context (from Memory Agent).
    trust_level:   Provenance tag for the context items.
    """

    model_config = {"populate_by_name": True}

    context_items: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Pre-retrieved memory/knowledge items.",
    )
    trust_level: str = Field(
        default="RETRIEVED",
        description="Trust level of context: RETRIEVED | VALIDATED | APPROVED | UNVERIFIED",
    )
    extra: dict[str, Any] = Field(default_factory=dict)


class TaskConstraints(BaseModel):
    """Execution constraints for the task."""

    model_config = {"populate_by_name": True}

    max_duration_seconds: int = Field(default=300, ge=1, description="Max wall-clock time.")
    max_retries: int = Field(default=2, ge=0, description="Max retry attempts after failure.")
    require_verification: bool = Field(default=True, description="Must pass verification before COMPLETE.")
    dry_run: bool = Field(default=False, description="If True, no side effects are produced.")


class ExpectedOutput(BaseModel):
    """Describes what the caller expects the result to contain."""

    model_config = {"populate_by_name": True}

    output_type: str = Field(
        default="text",
        description="Expected output type: text | code | image | document | reference | structured",
    )
    artifact_types: list[str] = Field(
        default_factory=list,
        description="Expected artifact types e.g. ['code', 'document']",
    )
    description: str = Field(default="", description="Human-readable description of expected output.")


class TaskRequest(BaseModel):
    """
    Strongly-typed task input contract.

    Sent by: future Master Orchestrator (or manual test runner).
    Consumed by: SpecialistAgent runtime.

    This object is the boundary — agents never access orchestrator internals.
    """

    model_config = {"populate_by_name": True}

    task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique task identifier (UUID4).",
    )
    agent_type: str = Field(
        ...,
        description="Target specialist type e.g. 'image_generation', 'web_development'.",
    )
    instruction: str = Field(
        ...,
        min_length=1,
        description="Natural-language instruction for the agent.",
    )
    context: TaskContext = Field(
        default_factory=TaskContext,
        description="Pre-loaded context block.",
    )
    constraints: TaskConstraints = Field(
        default_factory=TaskConstraints,
        description="Execution constraints.",
    )
    expected_output: ExpectedOutput = Field(
        default_factory=ExpectedOutput,
        description="Describes expected output.",
    )
    tools_allowed: list[str] = Field(
        default_factory=list,
        description="Explicit tool whitelist (empty = use agent defaults).",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key/value metadata for tracing and correlation.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC creation timestamp.",
    )

    @field_validator("agent_type")
    @classmethod
    def agent_type_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("agent_type must not be empty or whitespace.")
        return v.strip().lower()

    @field_validator("instruction")
    @classmethod
    def instruction_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("instruction must not be empty or whitespace.")
        return v.strip()
