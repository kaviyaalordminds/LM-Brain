"""
Specialist Agent — Research Tool

Interface for research capabilities.
Delegates to the existing Memory Agent research abstraction —
does NOT duplicate Jina logic.

All results are tagged UNVERIFIED until validated through the
existing validation workflow.
"""

from __future__ import annotations

import logging
from typing import Any

from specialist_agent.permissions.policy import Permission
from specialist_agent.tools.base import BaseTool, ToolCapability, ToolResult

logger = logging.getLogger(__name__)


class ResearchTool(BaseTool):
    """
    Research tool — thin wrapper over the Memory Agent research interface.

    Results returned by this tool are ALWAYS tagged as UNVERIFIED.
    They must flow through the existing ValidationLayer before
    being trusted or written to the knowledge base.
    """

    def __init__(self, memory_client: Any | None = None) -> None:
        self._memory_client = memory_client
        self._configured = memory_client is not None

    @property
    def name(self) -> str:
        return "research"

    @property
    def capability(self) -> ToolCapability:
        return ToolCapability.RESEARCH

    @property
    def description(self) -> str:
        return (
            "Conduct external research via the Memory Agent. "
            "Results are always UNVERIFIED until validated."
        )

    @property
    def permission_level(self) -> str:
        return Permission.NETWORK.value

    def execute(self, query: str = "", task_id: str | None = None, **kwargs: Any) -> ToolResult:
        """
        Research *query* through the Memory Agent.

        Returns UNVERIFIED evidence items.
        Never auto-promotes evidence to VALIDATED or APPROVED.
        """
        if not query.strip():
            return ToolResult(success=False, error="'query' is required.")

        if not self._configured:
            return ToolResult(
                success=False,
                error=(
                    "Research tool not configured — "
                    "Memory Agent client is not available. "
                    "Set MEMORY_AGENT_URL to connect."
                ),
                metadata={"error_code": "MEMORY_CLIENT_NOT_CONFIGURED"},
            )

        try:
            import asyncio

            async def _run() -> dict[str, Any]:
                return await self._memory_client.research(query=query, task_id=task_id)

            result = asyncio.run(_run())
            return ToolResult(
                success=True,
                output=result,
                metadata={
                    "trust_level": "UNVERIFIED",
                    "query": query,
                    "note": "Evidence is UNVERIFIED — validate before trusting.",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("research.tool_error", extra={"query": query[:100]}, exc_info=True)
            return ToolResult(success=False, error=f"Research error: {exc}")
