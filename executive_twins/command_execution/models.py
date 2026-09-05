"""
Data models and schemas for Controlled Build & Test Command Execution.
Provides typed command definitions, execution requests, and structured result models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field

from executive_twins.schemas.common import FactItem
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)


class CommandType(str, Enum):
    """Controlled development command categories."""
    BUILD = "BUILD"
    TEST = "TEST"
    LINT = "LINT"
    TYPECHECK = "TYPECHECK"
    PACKAGE = "PACKAGE"


class CommandStatus(str, Enum):
    """Outcome status for controlled command execution."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    REJECTED = "REJECTED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    INVALID_COMMAND = "INVALID_COMMAND"


class CommandRequest(BaseModel):
    """
    Structured request for controlled command execution inside a workspace boundary.
    Arbitrary raw command strings and unrestricted subprocess parameters are forbidden.
    """
    command_type: CommandType
    executable: str
    arguments: List[str] = Field(default_factory=list)
    workspace_id: str
    timeout_seconds: float = Field(default=30.0, ge=0.1, le=300.0)
    path_arguments: List[str] = Field(default_factory=list)


class CommandResult(BaseModel):
    """
    Structured outcome of a controlled command execution.
    Contains stdout/stderr, exit code, execution metrics, facts, and evidence.
    """
    success: bool
    status: CommandStatus
    command_type: CommandType
    executable: str
    arguments: List[str] = Field(default_factory=list)
    workspace_id: str
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    is_truncated: bool = False
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    facts: List[FactItem] = Field(default_factory=list)
    evidence: List[Union[ExecutionLogEvidence, TestEvidence, VerificationEvidence, ArtifactEvidence]] = Field(
        default_factory=list
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
