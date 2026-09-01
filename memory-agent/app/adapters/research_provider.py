"""
Memory Agent — Research Provider Adapter

Defines the ResearchProvider abstract interface and the MockResearchProvider
implementation used for development and testing.

INTEGRATION POINT
─────────────────
To connect a real external research provider (web search, approved API, etc.):

1. Create a class inheriting from ResearchProvider.
2. Implement search(), fetch(), and extract_evidence().
3. Read the API key from settings.research_api_key — never hardcode it.
4. In app/main.py, replace MockResearchProvider with your implementation.

All research results MUST be returned with:
    approval_status = ApprovalStatus.UNVERIFIED

They must never be promoted to 'approved' without going through
the ValidationLayer and MemoryWriter pipeline.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.models.memory import ApprovalStatus, EvidenceItem


# ─────────────────────────────────────────────────────────────────────────────
# Custom Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class ResearchProviderError(Exception):
    """Raised when the research provider is unavailable or returns an error."""


class ResearchTimeoutError(Exception):
    """Raised when a research request exceeds the configured timeout."""


class InvalidResearchResultError(Exception):
    """Raised when a research result is malformed or cannot be parsed."""


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Interface
# ─────────────────────────────────────────────────────────────────────────────


class ResearchProvider(ABC):
    """
    Abstract interface for external research providers.

    Implementations must ensure all returned EvidenceItems have:
        approval_status = ApprovalStatus.UNVERIFIED

    External research results may NEVER be returned as 'approved'.
    """

    @abstractmethod
    async def search(self, query: str) -> list[EvidenceItem]:
        """
        Search an external source for evidence relevant to *query*.

        Returns a list of EvidenceItems, all marked UNVERIFIED.
        Returns an empty list if nothing relevant is found.
        Raises ResearchProviderError on provider failure.
        Raises ResearchTimeoutError on timeout.
        """
        ...

    @abstractmethod
    async def fetch(self, url: str) -> EvidenceItem:
        """
        Fetch content from a specific URL/reference.

        Returns an EvidenceItem marked UNVERIFIED.
        Raises ResearchProviderError if the URL is unreachable.
        """
        ...

    @abstractmethod
    async def extract_evidence(self, raw: str, source: str) -> EvidenceItem:
        """
        Parse raw content into a structured EvidenceItem.

        Raises InvalidResearchResultError if the content cannot be parsed.
        """
        ...


# ─────────────────────────────────────────────────────────────────────────────
# Mock Implementation
# ─────────────────────────────────────────────────────────────────────────────

# Canned responses keyed by query fragment.
_MOCK_RESPONSES: dict[str, list[dict[str, str]]] = {
    "default": [
        {
            "source": "https://example-research.com/article/ai-memory-systems",
            "title": "AI Memory Systems: A Survey",
            "content": (
                "Modern AI memory systems distinguish between short-term working memory "
                "and long-term persistent knowledge stores. "
                "Retrieval-augmented generation (RAG) architectures use vector databases "
                "or document stores to provide relevant context at inference time. "
                "Evidence-based validation before knowledge promotion is considered "
                "a critical safety property in production systems."
            ),
        },
        {
            "source": "https://example-research.com/article/knowledge-validation",
            "title": "Evidence Validation in Knowledge Bases",
            "content": (
                "Knowledge base integrity depends on strict validation pipelines. "
                "Best practices include: (1) multi-source corroboration, "
                "(2) provenance tracking, (3) deterministic approval gates, "
                "and (4) immutable audit trails for all write operations. "
                "A single model's self-assertion is never treated as sufficient evidence."
            ),
        },
    ],
    "security": [
        {
            "source": "https://example-research.com/article/ai-security",
            "title": "AI System Security Practices",
            "content": (
                "Secure AI systems enforce: API key management via environment variables, "
                "execution sandboxing, least-privilege tool access, "
                "and audit logging of all sensitive operations. "
                "Secrets must never appear in source code or logs."
            ),
        },
    ],
    "architecture": [
        {
            "source": "https://example-research.com/article/autonomous-agents",
            "title": "Autonomous Agent Architectures",
            "content": (
                "Multi-agent architectures typically separate perception, planning, "
                "execution, and memory into distinct layers. "
                "An orchestrator coordinates task lifecycle and routes work to specialists. "
                "Verification produces objective evidence before any re-planning occurs."
            ),
        },
    ],
}


def _select_mock_responses(query: str) -> list[dict[str, str]]:
    """Select the most appropriate mock responses for a query."""
    query_lower = query.lower()
    for key in _MOCK_RESPONSES:
        if key != "default" and key in query_lower:
            return _MOCK_RESPONSES[key]
    return _MOCK_RESPONSES["default"]


class MockResearchProvider(ResearchProvider):
    """
    In-memory research provider for development and testing.

    Returns configurable stub evidence items.
    All items are marked UNVERIFIED — they must be validated before use.

    # INTEGRATION POINT
    Replace with a real provider class (e.g., WebSearchProvider, TavilyProvider)
    that inherits from ResearchProvider. Read the API key from:
        settings.research_api_key
    Never hardcode it.
    """

    def __init__(
        self,
        simulate_failure: bool = False,
        simulate_timeout: bool = False,
        empty_results: bool = False,
    ) -> None:
        self._simulate_failure = simulate_failure
        self._simulate_timeout = simulate_timeout
        self._empty_results = empty_results

    def _check_failures(self) -> None:
        if self._simulate_failure:
            raise ResearchProviderError("MockResearchProvider: simulated provider failure")
        if self._simulate_timeout:
            raise ResearchTimeoutError("MockResearchProvider: simulated timeout")

    async def search(self, query: str) -> list[EvidenceItem]:
        self._check_failures()

        if self._empty_results:
            return []

        raw_results = _select_mock_responses(query)
        items: list[EvidenceItem] = []
        for raw in raw_results:
            item = await self.extract_evidence(raw["content"], raw["source"])
            item.title = raw.get("title")
            items.append(item)
        return items

    async def fetch(self, url: str) -> EvidenceItem:
        self._check_failures()
        return EvidenceItem(
            source=url,
            title=f"Fetched: {url}",
            content=f"[Mock content fetched from {url}]",
            retrieved_at=datetime.now(timezone.utc),
            relevance=0.5,
            approval_status=ApprovalStatus.UNVERIFIED,
        )

    async def extract_evidence(self, raw: str, source: str) -> EvidenceItem:
        if not raw or not raw.strip():
            raise InvalidResearchResultError("Cannot extract evidence from empty content.")
        return EvidenceItem(
            id=str(uuid.uuid4()),
            source=source,
            content=raw.strip(),
            retrieved_at=datetime.now(timezone.utc),
            relevance=0.6,
            approval_status=ApprovalStatus.UNVERIFIED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Jina Research Provider (Real External Web & Reader Search)
# ─────────────────────────────────────────────────────────────────────────────


class JinaResearchProvider(ResearchProvider):
    """
    Production Research Provider using Jina Search and Jina Reader.

    - Uses https://s.jina.ai/<query> for live technical web research.
    - Uses https://r.jina.ai/<url> for deep content extraction when needed.
    - Preserves exact source URLs, titles, snippets, and domains.
    - Enforces ApprovalStatus.UNVERIFIED on all returned items.
    - Never logs or exposes the API key.
    - Handles timeouts and error status codes gracefully.
    """

    def __init__(
        self,
        api_key: str,
        search_endpoint: str = "https://s.jina.ai",
        reader_endpoint: str = "https://r.jina.ai",
        timeout_seconds: float = 30.0,
        max_results: int = 5,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ResearchProviderError(
                "JinaResearchProvider requires a non-empty API key. "
                "Set RESEARCH_API_KEY in .env or configure settings."
            )
        self._api_key = api_key.strip()
        self._search_endpoint = search_endpoint.rstrip("/")
        self._reader_endpoint = reader_endpoint.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_results = max_results

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "X-Retain-Images": "none",
        }

    async def search(self, query: str) -> list[EvidenceItem]:
        """
        Search Jina for external technical evidence.

        All returned EvidenceItems have approval_status = ApprovalStatus.UNVERIFIED.
        """
        q_clean = query.strip()
        if not q_clean:
            return []

        import httpx
        import urllib.parse
        import logging
        logger = logging.getLogger(__name__)

        url = f"{self._search_endpoint}/{urllib.parse.quote(q_clean)}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.TimeoutException as exc:
                raise ResearchTimeoutError(
                    f"Jina search timed out after {self._timeout_seconds}s"
                ) from exc
            except httpx.RequestError as exc:
                raise ResearchProviderError(
                    f"Jina network connection failed: {exc}"
                ) from exc

        if response.status_code in (401, 403):
            raise ResearchProviderError(
                f"Jina authentication failed (HTTP {response.status_code}). Check RESEARCH_API_KEY."
            )
        if response.status_code == 429:
            raise ResearchProviderError("Jina rate limit exceeded (HTTP 429).")
        if response.status_code >= 500:
            raise ResearchProviderError(
                f"Jina search server error (HTTP {response.status_code})."
            )
        if response.status_code != 200:
            raise ResearchProviderError(
                f"Jina search failed with unexpected status HTTP {response.status_code}."
            )

        try:
            data = response.json()
        except Exception as exc:
            raise InvalidResearchResultError(
                f"Failed to parse Jina search response as JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise InvalidResearchResultError("Jina search response is not a valid JSON object.")

        raw_results = data.get("data", [])
        if not isinstance(raw_results, list):
            return []

        items: list[EvidenceItem] = []
        for raw in raw_results[: self._max_results]:
            if not isinstance(raw, dict):
                continue
            content = (raw.get("content") or raw.get("description") or "").strip()
            if not content:
                continue

            raw_url = (raw.get("url") or "").strip()
            title = (raw.get("title") or "").strip() or None
            source = raw_url if raw_url else f"jina://search?q={urllib.parse.quote(q_clean)}"

            evidence = EvidenceItem(
                id=str(uuid.uuid4()),
                source=source,
                title=title,
                content=content,
                retrieved_at=datetime.now(timezone.utc),
                relevance=0.85 if raw_url else 0.5,
                approval_status=ApprovalStatus.UNVERIFIED,
            )
            items.append(evidence)

        return items

    async def fetch(self, url: str) -> EvidenceItem:
        """
        Fetch full page content using Jina Reader (r.jina.ai/<url>).

        Returns an EvidenceItem marked UNVERIFIED.
        """
        clean_url = url.strip()
        if not clean_url:
            raise ResearchProviderError("Cannot fetch empty URL.")

        import httpx
        target = f"{self._reader_endpoint}/{clean_url}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            try:
                response = await client.get(target, headers=headers)
            except httpx.TimeoutException as exc:
                raise ResearchTimeoutError(
                    f"Jina Reader fetch timed out after {self._timeout_seconds}s for {clean_url}"
                ) from exc
            except httpx.RequestError as exc:
                raise ResearchProviderError(
                    f"Jina Reader network error for {clean_url}: {exc}"
                ) from exc

        if response.status_code in (401, 403):
            raise ResearchProviderError(
                f"Jina Reader authentication failed (HTTP {response.status_code})."
            )
        if response.status_code != 200:
            raise ResearchProviderError(
                f"Jina Reader failed to fetch {clean_url} (HTTP {response.status_code})."
            )

        content = ""
        title = None
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                data = response.json()
                if isinstance(data, dict):
                    inner = data.get("data", {})
                    content = inner.get("content", "") if isinstance(inner, dict) else ""
                    title = inner.get("title") if isinstance(inner, dict) else None
            except Exception:
                content = response.text
        else:
            content = response.text

        if not content.strip():
            raise InvalidResearchResultError(f"Jina Reader returned empty content for {clean_url}.")

        return EvidenceItem(
            id=str(uuid.uuid4()),
            source=clean_url,
            title=title or f"Fetched: {clean_url}",
            content=content.strip(),
            retrieved_at=datetime.now(timezone.utc),
            relevance=0.85,
            approval_status=ApprovalStatus.UNVERIFIED,
        )

    async def extract_evidence(self, raw: str, source: str) -> EvidenceItem:
        """Parse raw content into an EvidenceItem marked UNVERIFIED."""
        if not raw or not raw.strip():
            raise InvalidResearchResultError("Cannot extract evidence from empty content.")
        return EvidenceItem(
            id=str(uuid.uuid4()),
            source=source,
            content=raw.strip(),
            retrieved_at=datetime.now(timezone.utc),
            relevance=0.7,
            approval_status=ApprovalStatus.UNVERIFIED,
        )
