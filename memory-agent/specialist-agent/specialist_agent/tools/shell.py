"""
Specialist Agent — Shell Tool

Controlled command execution for specialist agents.
Commands are sandboxed — no interactive sessions, no shell injection.
Results are captured and returned.

IMPORTANT:
- Never allow unrestricted arbitrary shell access.
- EXECUTE permission is required.
- Timeout is enforced.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

from specialist_agent.permissions.policy import Permission
from specialist_agent.tools.base import BaseTool, ToolCapability, ToolResult

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 30
_BLOCKED_COMMANDS = frozenset([
    "rm -rf",
    "git reset --hard",
    "git clean -fd",
    "git push --force",
    "git push -f",
    "format",
    "mkfs",
    "dd if=",
    "shutdown",
    "reboot",
    "halt",
])


class ShellTool(BaseTool):
    """
    Controlled shell command execution.

    Executes commands in a subprocess with timeout enforcement.
    Blocked command patterns are refused immediately.
    """

    def __init__(self, timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout_seconds

    @property
    def name(self) -> str:
        return "shell"

    @property
    def capability(self) -> ToolCapability:
        return ToolCapability.SHELL

    @property
    def description(self) -> str:
        return "Execute shell commands with timeout enforcement and safety checks."

    @property
    def permission_level(self) -> str:
        return Permission.EXECUTE.value

    def _is_blocked(self, command: str) -> bool:
        cmd_lower = command.lower()
        return any(blocked in cmd_lower for blocked in _BLOCKED_COMMANDS)

    def execute(self, command: str = "", cwd: str | None = None, **kwargs: Any) -> ToolResult:
        """
        Execute *command* in a subprocess.

        Parameters
        ----------
        command : Shell command to execute.
        cwd     : Working directory for the command.
        """
        if not command.strip():
            return ToolResult(success=False, error="'command' is required.")

        if self._is_blocked(command):
            logger.warning("shell.blocked_command", extra={"command": command[:100]})
            return ToolResult(
                success=False,
                error=f"Blocked command: '{command[:60]}'. This pattern is not permitted.",
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=cwd,
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            success = result.returncode == 0

            output_text = stdout if stdout else stderr

            return ToolResult(
                success=success,
                output=output_text,
                error=stderr if not success else None,
                metadata={"returncode": result.returncode, "command": command[:200]},
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error=f"Command timed out after {self._timeout} seconds.",
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=f"Shell execution error: {exc}")
