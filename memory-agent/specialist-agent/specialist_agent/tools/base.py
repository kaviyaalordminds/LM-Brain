"""
Specialist Agent — Tool Abstraction

Defines the base Tool interface that every tool must implement.
Tools are registered in a ToolRegistry and requested by name.
No tool may be executed unless the agent's PermissionPolicy allows it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ToolCapability(str, Enum):
    """Logical capability categories for tools."""

    FILESYSTEM = "filesystem"
    SHELL = "shell"
    HTTP = "http"
    DATABASE = "database"
    IMAGE_GENERATION = "image_generation"
    RESEARCH = "research"
    CODING = "coding"
    BROWSER = "browser"


class ToolResult(BaseModel):
    """Structured result returned by every tool execution."""

    model_config = {"populate_by_name": True}

    success: bool
    output: Any = None
    error: str | None = None
    is_mock: bool = False   # True only when a mock tool ran — never real execution
    metadata: dict[str, Any] = {}


class BaseTool(ABC):
    """
    Abstract base for all Specialist Agent tools.

    Implementers must provide:
      - name        : unique registry key
      - capability  : ToolCapability enum value
      - description : human-readable purpose
      - permission_level : Permission required to use this tool
      - execute()   : the actual tool implementation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name used as the registry key."""

    @property
    @abstractmethod
    def capability(self) -> ToolCapability:
        """Logical capability this tool provides."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this tool does."""

    @property
    @abstractmethod
    def permission_level(self) -> str:
        """Permission required to use this tool (Permission enum value)."""

    @property
    def is_mock(self) -> bool:
        """Return True if this is a mock implementation."""
        return False

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with the provided keyword arguments.

        Must return a ToolResult — never raise naked exceptions to callers.
        Wrap all internal errors in ToolResult(success=False, error=...).
        """

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"capability={self.capability.value}, mock={self.is_mock})"
        )
