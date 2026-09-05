"""
Interfaces and abstract protocols for Software Development Workspace.
"""

from abc import ABC, abstractmethod

from executive_twins.workspace.models import WorkspaceOperationResult


class ISoftwareWorkspace(ABC):
    """
    Controlled Software Development Workspace Interface.
    Provides safe, isolated operations for software/web development specialists.
    Must enforce path isolation and forbid arbitrary shell/code execution.
    """

    @property
    @abstractmethod
    def workspace_id(self) -> str:
        """Return unique workspace identifier."""
        pass

    @property
    @abstractmethod
    def root_path(self) -> str:
        """Return configured root path string."""
        pass

    @abstractmethod
    def create_workspace(self) -> WorkspaceOperationResult:
        """Initialize workspace directory and state."""
        pass

    @abstractmethod
    def workspace_exists(self) -> bool:
        """Check if workspace directory exists and is active."""
        pass

    @abstractmethod
    def read_file(self, relative_path: str) -> WorkspaceOperationResult:
        """Read content of a workspace-contained file."""
        pass

    @abstractmethod
    def write_file(
        self, relative_path: str, content: str, overwrite: bool = True
    ) -> WorkspaceOperationResult:
        """Create or update a workspace-contained file."""
        pass

    @abstractmethod
    def list_files(self, relative_path: str = ".") -> WorkspaceOperationResult:
        """List files contained within the workspace."""
        pass

    @abstractmethod
    def file_exists(self, relative_path: str) -> bool:
        """Check if a file or directory exists inside the workspace."""
        pass

    @abstractmethod
    def record_artifact(
        self, relative_path: str, description: str = ""
    ) -> WorkspaceOperationResult:
        """Record generated artifact and calculate SHA-256 checksum."""
        pass

    @abstractmethod
    def close_workspace(self, cleanup: bool = False) -> WorkspaceOperationResult:
        """Close workspace and optionally cleanup temporary directory."""
        pass
