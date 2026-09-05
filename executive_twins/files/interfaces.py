"""
Interfaces and abstract protocols for Controlled Files API.
"""

from abc import ABC, abstractmethod
from executive_twins.files.models import FileOperationResult


class IFileService(ABC):
    """
    Interface for controlled workspace file operations.
    Accepts workspace abstraction and enforces security boundary.
    Must not expose host filesystem paths, shell commands, or arbitrary execution.
    """

    @abstractmethod
    def create_file(
        self, relative_path: str, content: str, overwrite: bool = False
    ) -> FileOperationResult:
        """Create a file inside workspace root."""
        pass

    @abstractmethod
    def read_file(self, relative_path: str) -> FileOperationResult:
        """Read content of a workspace-contained file."""
        pass

    @abstractmethod
    def update_file(self, relative_path: str, content: str) -> FileOperationResult:
        """Update an existing workspace-contained file."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> FileOperationResult:
        """Delete a workspace-contained file."""
        pass

    @abstractmethod
    def list_files(self, relative_path: str = "") -> FileOperationResult:
        """List files contained within workspace relative path."""
        pass

    @abstractmethod
    def file_exists(self, relative_path: str) -> FileOperationResult:
        """Check if file or directory exists inside workspace relative path."""
        pass

    @abstractmethod
    def get_file_metadata(self, relative_path: str) -> FileOperationResult:
        """Retrieve typed metadata for a file or directory inside workspace."""
        pass
