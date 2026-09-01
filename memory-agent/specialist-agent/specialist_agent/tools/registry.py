"""
Specialist Agent — Tool Registry

A central registry for all available tools.
Agents request tools by name; the registry resolves and returns them.
Permission checks happen BEFORE the tool is returned/executed.

No tool executes unless:
  1. The tool is registered.
  2. The requesting agent's PermissionPolicy allows the required permission.
"""

from __future__ import annotations

import logging
from typing import Any

from specialist_agent.core.errors import PermissionDeniedError, ToolNotFoundError
from specialist_agent.permissions.policy import Permission, PermissionPolicy
from specialist_agent.tools.base import BaseTool, ToolCapability, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for specialist agent tools.

    Usage
    -----
    registry = ToolRegistry()
    registry.register(FilesystemTool())
    tool = registry.get("filesystem", policy)
    result = tool.execute(action="read", path="/some/file")
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, tool: BaseTool) -> None:
        """Register a tool. Overwrites any existing tool with the same name."""
        self._tools[tool.name] = tool
        logger.debug("tool.registered", extra={"tool": tool.name, "mock": tool.is_mock})

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(name, None)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """Return a summary list of all registered tools."""
        return [
            {
                "name": t.name,
                "capability": t.capability.value,
                "description": t.description,
                "permission_level": t.permission_level,
                "is_mock": t.is_mock,
            }
            for t in self._tools.values()
        ]

    def has_tool(self, name: str) -> bool:
        """Return True if a tool with *name* is registered."""
        return name in self._tools

    def get_by_capability(self, capability: ToolCapability) -> list[BaseTool]:
        """Return all tools matching the given capability."""
        return [t for t in self._tools.values() if t.capability == capability]

    # ------------------------------------------------------------------
    # Guarded Access — permission check happens here
    # ------------------------------------------------------------------

    def get(self, name: str, policy: PermissionPolicy | None = None) -> BaseTool:
        """
        Return the tool *name* after verifying the agent's permission.

        Raises
        ------
        ToolNotFoundError      — tool not registered.
        PermissionDeniedError  — agent lacks the required permission.
        """
        if name not in self._tools:
            raise ToolNotFoundError(tool_name=name)

        tool = self._tools[name]

        if policy is not None:
            try:
                required = Permission(tool.permission_level)
            except ValueError:
                # If the tool declares an unknown permission level, block it.
                raise PermissionDeniedError(
                    agent_id=policy.agent_id,
                    permission=tool.permission_level,
                    resource=name,
                )
            policy.require(required, resource=name)

        return tool

    def execute(
        self,
        name: str,
        policy: PermissionPolicy | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Convenience: get tool, check permission, then execute.

        Returns ToolResult — never raises to callers.
        """
        try:
            tool = self.get(name, policy)
        except ToolNotFoundError as exc:
            logger.error("tool.not_found", extra={"tool": name})
            return ToolResult(success=False, error=str(exc))
        except PermissionDeniedError as exc:
            logger.warning("tool.permission_denied", extra={"tool": name})
            return ToolResult(success=False, error=str(exc))

        try:
            result = tool.execute(**kwargs)
            logger.debug(
                "tool.executed",
                extra={"tool": name, "success": result.success, "mock": result.is_mock},
            )
            return result
        except Exception as exc:  # noqa: BLE001
            logger.error("tool.execution_error", extra={"tool": name}, exc_info=True)
            return ToolResult(success=False, error=f"Tool execution error: {exc}")
