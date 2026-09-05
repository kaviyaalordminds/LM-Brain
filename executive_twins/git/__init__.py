"""
Controlled Git / Version Control Integration Layer for Autonomous Specialist Workers.
Provides safe, structured Git access within Software Development Workspaces.
"""

from executive_twins.git.dev_adapters import (
    BaseGitCapabilityHandler,
    DevGitServiceAdapter,
    GitBranchCapabilityHandler,
    GitCommitCapabilityHandler,
    GitDiffCapabilityHandler,
    GitLogCapabilityHandler,
    GitStageCapabilityHandler,
    GitStatusCapabilityHandler,
    GitUnstageCapabilityHandler,
)
from executive_twins.git.git_service import ControlledGitService
from executive_twins.git.interfaces import IGitService
from executive_twins.git.models import (
    GitLogEntry,
    GitOperationType,
    GitRequest,
    GitResult,
    GitStatus,
)

__all__ = [
    # Models
    "GitOperationType",
    "GitStatus",
    "GitLogEntry",
    "GitRequest",
    "GitResult",
    # Interfaces
    "IGitService",
    # Service
    "ControlledGitService",
    # Dev / Test Adapters & Handlers
    "DevGitServiceAdapter",
    "BaseGitCapabilityHandler",
    "GitStatusCapabilityHandler",
    "GitBranchCapabilityHandler",
    "GitDiffCapabilityHandler",
    "GitStageCapabilityHandler",
    "GitUnstageCapabilityHandler",
    "GitCommitCapabilityHandler",
    "GitLogCapabilityHandler",
]
