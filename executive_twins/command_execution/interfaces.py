"""
Interfaces and abstract protocols for Controlled Build & Test Command Execution.
"""

from abc import ABC, abstractmethod
from executive_twins.command_execution.models import CommandRequest, CommandResult


class ICommandExecutor(ABC):
    """
    Interface for controlled workspace command execution.
    Executes allowlisted, validated commands within a Software Development Workspace.
    Must NOT expose raw shell, subprocess APIs, or arbitrary host paths.
    """

    @abstractmethod
    def execute(self, request: CommandRequest) -> CommandResult:
        """
        Execute an approved command deterministically inside the workspace boundary.
        """
        pass
