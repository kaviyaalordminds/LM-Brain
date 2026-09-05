"""
Data models and schemas for Controlled Git / Version Control Integration Layer.
Provides typed Git operations, requests, and structured result models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from executive_twins.schemas.common import FactItem
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    DataEvidence,
    ExecutionLogEvidence,
    VerificationEvidence,
)


class GitOperationType(str, Enum):
    """Supported controlled Git operations."""
    STATUS = "STATUS"
    CURRENT_BRANCH = "CURRENT_BRANCH"
    LIST_BRANCHES = "LIST_BRANCHES"
    CREATE_BRANCH = "CREATE_BRANCH"
    CHECKOUT_BRANCH = "CHECKOUT_BRANCH"
    DIFF = "DIFF"
    STAGE_FILES = "STAGE_FILES"
    UNSTAGE_FILES = "UNSTAGE_FILES"
    COMMIT = "COMMIT"
    LOG = "LOG"


class GitStatus(str, Enum):
    """Outcome and state status for controlled Git operations."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    INVALID_OPERATION = "INVALID_OPERATION"
    INVALID_INPUT = "INVALID_INPUT"
    REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
    NOT_A_REPOSITORY = "NOT_A_REPOSITORY"
    CLEAN = "CLEAN"
    DIRTY = "DIRTY"


class GitLogEntry(BaseModel):
    """Structured commit log entry."""
    commit_id: str
    author: str
    date: str
    message: str


class GitRequest(BaseModel):
    """
    Structured request for controlled Git operations inside a workspace boundary.
    Arbitrary raw Git commands, command strings, and shell execution parameters are strictly forbidden.
    """
    model_config = ConfigDict(extra="forbid")

    operation: GitOperationType
    workspace_id: str
    branch_name: Optional[str] = None
    base_branch: Optional[str] = None
    paths: List[str] = Field(default_factory=list)
    commit_message: Optional[str] = None
    limit: Optional[int] = None


class GitResult(BaseModel):
    """
    Structured outcome of a controlled Git operation.
    Contains explicit typed fields for repository status, branches, changes, diffs,
    commits, log entries, facts, and evidence.
    """
    success: bool
    operation: GitOperationType
    status: GitStatus
    message: Optional[str] = None
    branch: Optional[str] = None
    branches: List[str] = Field(default_factory=list)
    changed_files: List[str] = Field(default_factory=list)
    staged_files: List[str] = Field(default_factory=list)
    unstaged_files: List[str] = Field(default_factory=list)
    diff: Optional[str] = None
    commit_id: Optional[str] = None
    commit_message: Optional[str] = None
    log_entries: List[GitLogEntry] = Field(default_factory=list)
    exit_code: Optional[int] = None
    is_truncated: bool = False
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    facts: List[FactItem] = Field(default_factory=list)
    evidence: List[Union[ExecutionLogEvidence, ArtifactEvidence, DataEvidence, VerificationEvidence]] = Field(
        default_factory=list
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
