"""
Interfaces and abstract protocols for Controlled Git / Version Control Integration.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from executive_twins.git.models import GitResult
from executive_twins.workspace.interfaces import ISoftwareWorkspace


class IGitService(ABC):
    """
    Controlled Git Service Interface.
    Provides safe, bounded, and structured version control operations within an ISoftwareWorkspace.
    Arbitrary Git commands, shell execution, direct .git mutation, and credential manipulation are forbidden.
    """

    @property
    @abstractmethod
    def workspace(self) -> ISoftwareWorkspace:
        """Return the underlying controlled workspace security boundary."""
        pass

    @abstractmethod
    def status(self) -> GitResult:
        """Retrieve structured repository status including branch, clean/dirty state, and changed files."""
        pass

    @abstractmethod
    def current_branch(self) -> GitResult:
        """Retrieve the name of the current active Git branch."""
        pass

    @abstractmethod
    def list_branches(self) -> GitResult:
        """List available Git branches in the repository."""
        pass

    @abstractmethod
    def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> GitResult:
        """Create a new Git branch from the current HEAD or an optional validated base branch."""
        pass

    @abstractmethod
    def checkout_branch(self, branch_name: str) -> GitResult:
        """Checkout an existing validated Git branch."""
        pass

    @abstractmethod
    def diff(self, paths: Optional[List[str]] = None) -> GitResult:
        """Retrieve a bounded diff of workspace changes or specific workspace-relative paths."""
        pass

    @abstractmethod
    def stage_files(self, paths: List[str]) -> GitResult:
        """Stage explicit workspace-relative files for commit."""
        pass

    @abstractmethod
    def unstage_files(self, paths: List[str]) -> GitResult:
        """Unstage explicit workspace-relative files."""
        pass

    @abstractmethod
    def commit(self, message: str) -> GitResult:
        """Create a commit with a validated, bounded commit message."""
        pass

    @abstractmethod
    def log(self, limit: int = 10) -> GitResult:
        """Retrieve a bounded list of recent structured commit log entries."""
        pass
