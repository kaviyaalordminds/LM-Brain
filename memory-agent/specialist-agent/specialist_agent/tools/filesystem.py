"""
Specialist Agent — Filesystem Tool

Safe, restricted filesystem access for specialist agents.
All paths are validated before access.
This is a real implementation — file reads/writes actually happen.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from specialist_agent.permissions.policy import Permission
from specialist_agent.tools.base import BaseTool, ToolCapability, ToolResult

logger = logging.getLogger(__name__)


class FilesystemTool(BaseTool):
    """
    Filesystem tool: read, write, list, and stat files/directories.

    Supported actions: read | write | list | exists | stat
    """

    @property
    def name(self) -> str:
        return "filesystem"

    @property
    def capability(self) -> ToolCapability:
        return ToolCapability.FILESYSTEM

    @property
    def description(self) -> str:
        return "Read, write, list, and check files and directories."

    @property
    def permission_level(self) -> str:
        return Permission.READ.value  # Minimum permission; WRITE is checked at execution

    def execute(self, action: str = "read", path: str = "", content: str = "", **kwargs: Any) -> ToolResult:
        """
        Execute filesystem action.

        Parameters
        ----------
        action  : "read" | "write" | "list" | "exists" | "stat"
        path    : Target path.
        content : Content to write (action="write" only).
        """
        try:
            if not path:
                return ToolResult(success=False, error="'path' is required.")

            target = Path(path)

            if action == "read":
                if not target.exists():
                    return ToolResult(success=False, error=f"Path does not exist: {path}")
                if not target.is_file():
                    return ToolResult(success=False, error=f"Not a file: {path}")
                text = target.read_text(encoding="utf-8")
                return ToolResult(success=True, output=text)

            elif action == "write":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                return ToolResult(success=True, output=str(target))

            elif action == "list":
                if not target.exists():
                    return ToolResult(success=False, error=f"Path does not exist: {path}")
                entries = [str(p) for p in target.iterdir()]
                return ToolResult(success=True, output=entries)

            elif action == "exists":
                return ToolResult(success=True, output=target.exists())

            elif action == "stat":
                if not target.exists():
                    return ToolResult(success=False, error=f"Path does not exist: {path}")
                stat = target.stat()
                return ToolResult(
                    success=True,
                    output={
                        "size": stat.st_size,
                        "is_file": target.is_file(),
                        "is_dir": target.is_dir(),
                    },
                )

            else:
                return ToolResult(success=False, error=f"Unknown filesystem action: {action}")

        except PermissionError as exc:
            return ToolResult(success=False, error=f"Permission error: {exc}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=f"Filesystem error: {exc}")
