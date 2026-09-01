"""
Specialist Agent — Memory Agent Client

A thin HTTP client that specialist agents use to request context from
the existing Memory Agent.

This client does NOT contain any Obsidian, BM25, or Jina logic.
It simply talks to the Memory Agent API and returns structured results.

Architecture:
  Specialist Agent
        ↓
  MemoryClient (this file)
        ↓
  Memory Agent HTTP API (http://localhost:8001)
        ↓
  Obsidian / Jina / ValidationLayer / etc.

Context trust levels are ALWAYS preserved:
  - Results from memory.search → RETRIEVED
  - Results from memory.research → UNVERIFIED

The client never promotes trust levels silently.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class MemoryClientError(Exception):
    """Raised when the Memory Agent client encounters a communication error."""


# Trust level constants — match Memory Agent ApprovalStatus
TRUST_RETRIEVED = "RETRIEVED"
TRUST_UNVERIFIED = "UNVERIFIED"
TRUST_VALIDATED = "VALIDATED"
TRUST_APPROVED = "APPROVED"


@dataclass
class MemoryContext:
    """
    Context returned by the Memory Agent.

    trust_level: Provenance tag from the Memory Agent.
                 RETRIEVED  → directly from Obsidian (trusted).
                 UNVERIFIED → from external research (must validate).
    """

    query: str
    results: list[dict[str, Any]]
    trust_level: str
    found: bool
    count: int
    sources: list[str]


class MemoryClient:
    """
    Thin HTTP client for the existing Memory Agent.

    Parameters
    ----------
    base_url : Memory Agent base URL (e.g. "http://localhost:8001").
    timeout  : Request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        task_id: str | None = None,
    ) -> MemoryContext:
        """
        Search the Memory Agent's Obsidian knowledge base.

        Results are tagged RETRIEVED (highest internal trust).
        """
        payload: dict[str, Any] = {"query": query}
        if task_id:
            payload["taskId"] = task_id

        try:
            data = self._post("/api/v1/memory/search", payload)
            results = data.get("results", [])
            return MemoryContext(
                query=query,
                results=results,
                trust_level=TRUST_RETRIEVED,
                found=data.get("found", False),
                count=data.get("count", 0),
                sources=[r.get("sourceNote", "") for r in results if r.get("sourceNote")],
            )
        except MemoryClientError:
            raise
        except Exception as exc:
            raise MemoryClientError(f"Memory search failed: {exc}") from exc

    async def research(
        self,
        query: str,
        task_id: str | None = None,
    ) -> MemoryContext:
        """
        Trigger external research through the Memory Agent.

        Results are ALWAYS tagged UNVERIFIED.
        They must not be trusted or written to Obsidian without validation.
        """
        payload: dict[str, Any] = {"query": query}
        if task_id:
            payload["taskId"] = task_id

        try:
            data = self._post("/api/v1/memory/research", payload)
            evidence = data.get("evidence", [])
            return MemoryContext(
                query=query,
                results=evidence,
                trust_level=TRUST_UNVERIFIED,  # Always UNVERIFIED
                found=bool(evidence),
                count=data.get("count", 0),
                sources=data.get("sources", []),
            )
        except MemoryClientError:
            raise
        except Exception as exc:
            raise MemoryClientError(f"Memory research failed: {exc}") from exc

    async def retrieve_context(self, task_id: str) -> MemoryContext:
        """Retrieve all cached context for a task from the Memory Agent."""
        try:
            data = self._get(f"/api/v1/memory/context/{task_id}")
            context_items = data.get("context", [])
            return MemoryContext(
                query=task_id,
                results=context_items,
                trust_level=TRUST_RETRIEVED,
                found=bool(context_items),
                count=len(context_items),
                sources=data.get("sources", []),
            )
        except MemoryClientError:
            raise
        except Exception as exc:
            raise MemoryClientError(f"Context retrieval failed: {exc}") from exc

    def is_available(self) -> bool:
        """Return True if the Memory Agent responds to health checks."""
        try:
            self._get("/health")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Private HTTP helpers
    # ------------------------------------------------------------------

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._send(req)

    def _get(self, path: str) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self._base_url}{path}",
            method="GET",
        )
        return self._send(req)

    def _send(self, req: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            raise MemoryClientError(f"HTTP {exc.code}: {exc.reason} — {req.full_url}") from exc
        except urllib.error.URLError as exc:
            raise MemoryClientError(
                f"Memory Agent unreachable at {self._base_url}: {exc.reason}. "
                "Ensure MEMORY_AGENT_URL is correct and the service is running."
            ) from exc
        except json.JSONDecodeError as exc:
            raise MemoryClientError(f"Invalid JSON from Memory Agent: {exc}") from exc
