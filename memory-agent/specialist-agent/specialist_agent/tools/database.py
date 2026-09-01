"""
Specialist Agent — Database Tool

Safe database query interface for specialist agents.
Actual database connections are configured externally.
If no database is configured, returns controlled NOT_CONFIGURED status.
DATABASE permission is required.
"""

from __future__ import annotations

import logging
from typing import Any

from specialist_agent.permissions.policy import Permission
from specialist_agent.tools.base import BaseTool, ToolCapability, ToolResult

logger = logging.getLogger(__name__)


class DatabaseTool(BaseTool):
    """
    Database tool — thin interface over a configurable backend.

    Supported actions: query | execute | schema | ping
    """

    def __init__(self, connection_string: str | None = None) -> None:
        self._connection_string = connection_string
        self._configured = bool(connection_string and connection_string.strip())

    @property
    def name(self) -> str:
        return "database"

    @property
    def capability(self) -> ToolCapability:
        return ToolCapability.DATABASE

    @property
    def description(self) -> str:
        return "Execute database queries and schema operations."

    @property
    def permission_level(self) -> str:
        return Permission.DATABASE.value

    def execute(
        self,
        action: str = "ping",
        sql: str = "",
        params: list[Any] | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute a database action.

        Parameters
        ----------
        action : "ping" | "query" | "execute" | "schema"
        sql    : SQL statement (not used for ping).
        params : Positional parameters for parameterised queries.
        """
        if not self._configured:
            return ToolResult(
                success=False,
                error="DATABASE NOT CONFIGURED — set connection_string to enable database operations.",
                metadata={"status": "NOT_CONFIGURED"},
            )

        if action == "ping":
            return ToolResult(
                success=True,
                output={"status": "connected", "connection": "configured"},
            )

        # For actual query/execute, we would connect here.
        # Returning NOT_IMPLEMENTED since the real DB driver depends on the environment.
        return ToolResult(
            success=False,
            error=(
                f"Database action '{action}' requires a configured driver. "
                "Install and configure the appropriate database connector."
            ),
            metadata={"action": action, "status": "DRIVER_NOT_CONFIGURED"},
        )


class MockDatabaseTool(BaseTool):
    """
    Mock database tool for deterministic unit testing.

    IMPORTANT: is_mock=True — results are never real database operations.
    """

    @property
    def name(self) -> str:
        return "database"

    @property
    def capability(self) -> ToolCapability:
        return ToolCapability.DATABASE

    @property
    def description(self) -> str:
        return "[MOCK] Mock database tool for testing."

    @property
    def permission_level(self) -> str:
        return Permission.DATABASE.value

    @property
    def is_mock(self) -> bool:
        return True

    def execute(self, action: str = "ping", sql: str = "", **kwargs: Any) -> ToolResult:
        if action == "ping":
            return ToolResult(
                success=True,
                output={"status": "mock_connected"},
                is_mock=True,
            )
        return ToolResult(
            success=True,
            output={"rows": [], "affected": 0, "sql": sql},
            is_mock=True,
        )
