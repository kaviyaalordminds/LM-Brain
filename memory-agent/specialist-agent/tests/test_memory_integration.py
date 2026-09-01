"""
Tests for Memory Agent integration client.

Covers:
  - MemoryClient.is_available() when Memory Agent is down
  - Trust levels are preserved (RETRIEVED vs UNVERIFIED)
  - Research results always UNVERIFIED
  - Trust escalation is NOT performed silently
  - MemoryContext data structure
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from specialist_agent.integration.memory_client import (
    MemoryClient,
    MemoryClientError,
    TRUST_RETRIEVED,
    TRUST_UNVERIFIED,
)


class TestMemoryClientAvailability:
    def test_is_available_returns_false_when_unreachable(self):
        """Memory client reports unavailable when service is down."""
        client = MemoryClient(base_url="http://localhost:9999", timeout=1)
        # Port 9999 should not have the Memory Agent running
        result = client.is_available()
        assert result is False

    def test_is_available_returns_true_on_success(self):
        """Mock a successful health check response."""
        client = MemoryClient(base_url="http://localhost:8001")

        with patch.object(client, "_get", return_value={"status": "ok"}):
            assert client.is_available() is True


class TestMemoryClientTrustLevels:
    """
    Verify that trust levels are ALWAYS preserved correctly.

    RETRIEVED — from Obsidian search
    UNVERIFIED — from external research
    """

    def test_search_returns_retrieved_trust(self):
        """Search results must be tagged RETRIEVED."""
        client = MemoryClient()
        mock_response = {
            "results": [{"content": "Some knowledge", "sourceNote": "/notes/test.md"}],
            "found": True,
            "count": 1,
        }

        with patch.object(client, "_post", return_value=mock_response):
            import asyncio
            ctx = asyncio.run(client.search("test query", task_id="t1"))

        assert ctx.trust_level == TRUST_RETRIEVED
        assert ctx.found is True
        assert ctx.count == 1

    def test_research_returns_unverified_trust(self):
        """Research results must ALWAYS be tagged UNVERIFIED — never RETRIEVED."""
        client = MemoryClient()
        mock_response = {
            "evidence": [{"content": "External research", "source": "https://example.com"}],
            "sources": ["https://example.com"],
            "count": 1,
        }

        with patch.object(client, "_post", return_value=mock_response):
            import asyncio
            ctx = asyncio.run(client.research("test query", task_id="t1"))

        assert ctx.trust_level == TRUST_UNVERIFIED
        assert ctx.found is True

    def test_research_never_returns_retrieved_trust(self):
        """Verify trust escalation is NOT performed."""
        client = MemoryClient()
        mock_response = {
            "evidence": [{"content": "Evidence", "source": "https://example.com"}],
            "sources": [],
            "count": 1,
        }

        with patch.object(client, "_post", return_value=mock_response):
            import asyncio
            ctx = asyncio.run(client.research("query"))

        # Must NEVER be RETRIEVED — even if content looks trusted
        assert ctx.trust_level != TRUST_RETRIEVED
        assert ctx.trust_level == TRUST_UNVERIFIED

    def test_empty_search_result_found_false(self):
        client = MemoryClient()
        mock_response = {"results": [], "found": False, "count": 0}

        with patch.object(client, "_post", return_value=mock_response):
            import asyncio
            ctx = asyncio.run(client.search("unknown topic"))

        assert ctx.found is False
        assert ctx.count == 0
        assert ctx.results == []

    def test_search_error_raises_memory_client_error(self):
        client = MemoryClient()
        with patch.object(client, "_post", side_effect=Exception("Connection refused")):
            with pytest.raises(MemoryClientError):
                import asyncio
                asyncio.run(client.search("test"))


class TestContextTrustIntegrity:
    """Ensure trust level constants match expected values."""

    def test_retrieved_trust_constant(self):
        assert TRUST_RETRIEVED == "RETRIEVED"

    def test_unverified_trust_constant(self):
        assert TRUST_UNVERIFIED == "UNVERIFIED"

    def test_retrieved_and_unverified_are_different(self):
        assert TRUST_RETRIEVED != TRUST_UNVERIFIED
