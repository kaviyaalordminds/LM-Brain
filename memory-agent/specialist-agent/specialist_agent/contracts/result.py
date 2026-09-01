"""
Specialist Agent — Result Contract

Strongly-typed output produced by every specialist agent execution.
The future Master Orchestrator consumes TaskResult objects without
needing to know any internal agent implementation detail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from specialist_agent.contracts.artifact import Artifact


class TaskStatus(str, Enum):
    """Terminal and in-progress status values for a task result."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class VerificationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class VerificationCheck(BaseModel):
    """A single named verification check and its outcome."""

    model_config = {"populate_by_name": True}

    name: str
    verdict: VerificationVerdict
    reason: str = ""
    evidence: list[str] = Field(default_factory=list)


class VerificationOutcome(BaseModel):
    """
    Structured result of the verification phase.

    Never simply returns True/False — always includes the
    checks performed, their individual verdicts, and evidence.
    """

    model_config = {"populate_by_name": True}

    verdict: VerificationVerdict = VerificationVerdict.SKIPPED
    checks: list[VerificationCheck] = Field(default_factory=list)
    reason: str = ""
    errors: list[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def passed(self) -> bool:
        return self.verdict == VerificationVerdict.PASS


class ErrorRecord(BaseModel):
    """A structured error record in the result."""

    model_config = {"populate_by_name": True}

    error_code: str
    message: str
    stage: str = ""   # lifecycle stage where the error occurred
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """
    Strongly-typed task output contract.

    Produced by: SpecialistAgent runtime.
    Consumed by: future Master Orchestrator (or manual test runner).

    This object is the output boundary — orchestrators never access
    internal agent implementation details.
    """

    model_config = {"populate_by_name": True}

    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = Field(..., description="Correlation ID from TaskRequest.")
    agent_id: str = Field(..., description="ID of the agent that produced this result.")
    agent_type: str = Field(..., description="Specialist type e.g. 'image_generation'.")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress fraction 0.0–1.0.",
    )
    output: str | None = Field(None, description="Primary text output of the task.")
    artifacts: list[Artifact] = Field(
        default_factory=list,
        description="Artifacts produced by this task.",
    )
    verification: VerificationOutcome = Field(default_factory=VerificationOutcome)
    errors: list[ErrorRecord] = Field(default_factory=list)
    retry_count: int = Field(default=0, description="Number of retries attempted.")
    started_at: datetime | None = Field(None)
    completed_at: datetime | None = Field(None)
    duration_seconds: float | None = Field(None, description="Wall-clock execution time.")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_error(self, error_code: str, message: str, stage: str = "") -> None:
        """Append a structured error record to this result."""
        self.errors.append(
            ErrorRecord(error_code=error_code, message=message, stage=stage)
        )

    def mark_started(self) -> None:
        self.started_at = datetime.now(timezone.utc)
        self.status = TaskStatus.RUNNING

    def mark_completed(self, output: str | None = None) -> None:
        self.completed_at = datetime.now(timezone.utc)
        self.status = TaskStatus.COMPLETED
        self.progress = 1.0
        if output is not None:
            self.output = output
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def mark_failed(self, error_code: str, message: str, stage: str = "") -> None:
        self.completed_at = datetime.now(timezone.utc)
        self.status = TaskStatus.FAILED
        self.add_error(error_code=error_code, message=message, stage=stage)
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
