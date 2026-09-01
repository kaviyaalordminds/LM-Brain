"""
Unit and Trust-Hierarchy Tests for JinaResearchProvider

Mocks all HTTP responses to ensure deterministic testing without consuming
external API credits.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.adapters.obsidian_adapter import MockObsidianAdapter
from app.adapters.research_provider import (
    InvalidResearchResultError,
    JinaResearchProvider,
    MockResearchProvider,
    ResearchProviderError,
    ResearchTimeoutError,
)
from app.core.memory_writer import MemoryWriter, WriteRejectedError
from app.core.research import ResearchService
from app.core.validation import ValidationLayer
from app.main import build_research_provider
from app.models.memory import ApprovalStatus, EvidenceItem


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def jina_provider() -> JinaResearchProvider:
    return JinaResearchProvider(
        api_key="test_jina_token_mocked_12345",
        timeout_seconds=5.0,
        max_results=5,
    )


@pytest.fixture
def mock_jina_search_response() -> dict:
    return {
        "code": 200,
        "status": 20000,
        "data": [
            {
                "title": "Next.js Authentication Guide",
                "url": "https://nextjs.org/docs/authentication",
                "content": (
                    "Authentication in Next.js involves verifying user identities. "
                    "Use server-side session management with HttpOnly cookies, "
                    "JWT verification in middleware, and secure OAuth2 flows."
                ),
                "description": "Comprehensive guide to authentication patterns in Next.js",
            },
            {
                "title": "OWASP REST Security Best Practices",
                "url": "https://owasp.org/www-project-rest-security/",
                "content": (
                    "REST API security requires TLS 1.3 encryption, rate limiting, "
                    "proper token expiration, input sanitization, and structured error responses."
                ),
                "description": "OWASP guidance on securing REST APIs",
            },
            {
                "title": "OAuth 2.0 Security Architecture",
                "url": "https://datatracker.ietf.org/doc/html/rfc6749",
                "content": (
                    "The OAuth 2.0 authorization framework enables a third-party application "
                    "to obtain limited access to an HTTP service on behalf of a resource owner."
                ),
                "description": "RFC 6749 specification for OAuth 2.0",
            },
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Provider Initialization & Key Safety Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_jina_provider_requires_non_empty_api_key() -> None:
    with pytest.raises(ResearchProviderError, match="requires a non-empty API key"):
        JinaResearchProvider(api_key="")

    with pytest.raises(ResearchProviderError, match="requires a non-empty API key"):
        JinaResearchProvider(api_key="   ")


def test_jina_provider_headers_use_bearer_token(jina_provider: JinaResearchProvider) -> None:
    headers = jina_provider._get_headers()
    assert headers["Authorization"] == "Bearer test_jina_token_mocked_12345"
    assert headers["Accept"] == "application/json"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Search & EvidenceItem Mapping Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_jina_search_success_and_mapping(
    jina_provider: JinaResearchProvider,
    mock_jina_search_response: dict,
) -> None:
    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps(mock_jina_search_response).encode("utf-8"),
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        items = await jina_provider.search("Next.js authentication best practices")

    assert len(items) == 3
    # Check Result 1
    assert items[0].title == "Next.js Authentication Guide"
    assert items[0].source == "https://nextjs.org/docs/authentication"
    assert "session management" in items[0].content
    assert items[0].approval_status == ApprovalStatus.UNVERIFIED
    assert items[0].relevance > 0.0

    # Check Result 2
    assert items[1].title == "OWASP REST Security Best Practices"
    assert items[1].source == "https://owasp.org/www-project-rest-security/"
    assert items[1].approval_status == ApprovalStatus.UNVERIFIED


@pytest.mark.asyncio
async def test_jina_search_empty_query_returns_empty(
    jina_provider: JinaResearchProvider,
) -> None:
    items = await jina_provider.search("   ")
    assert items == []


@pytest.mark.asyncio
async def test_jina_search_empty_data_returns_empty(
    jina_provider: JinaResearchProvider,
) -> None:
    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps({"data": []}).encode("utf-8"),
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        items = await jina_provider.search("unknown obscure topic")

    assert items == []


# ─────────────────────────────────────────────────────────────────────────────
# 3. HTTP Error & Failure Handling Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_jina_search_http_401_auth_error(jina_provider: JinaResearchProvider) -> None:
    mock_resp = httpx.Response(
        status_code=401,
        content=b'{"error": "Unauthorized"}',
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(ResearchProviderError, match="Jina authentication failed"):
            await jina_provider.search("test query")


@pytest.mark.asyncio
async def test_jina_search_http_429_rate_limit(jina_provider: JinaResearchProvider) -> None:
    mock_resp = httpx.Response(
        status_code=429,
        content=b'{"error": "Rate limit exceeded"}',
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(ResearchProviderError, match="Jina rate limit exceeded"):
            await jina_provider.search("test query")


@pytest.mark.asyncio
async def test_jina_search_http_500_server_error(jina_provider: JinaResearchProvider) -> None:
    mock_resp = httpx.Response(
        status_code=500,
        content=b"Internal Server Error",
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(ResearchProviderError, match="Jina search server error"):
            await jina_provider.search("test query")


@pytest.mark.asyncio
async def test_jina_search_timeout_error(jina_provider: JinaResearchProvider) -> None:
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Read timed out")
        with pytest.raises(ResearchTimeoutError, match="timed out"):
            await jina_provider.search("test query")


@pytest.mark.asyncio
async def test_jina_search_malformed_json(jina_provider: JinaResearchProvider) -> None:
    mock_resp = httpx.Response(
        status_code=200,
        content=b"This is not valid json <xml>",
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(InvalidResearchResultError):
            await jina_provider.search("test query")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Jina Reader Fetch Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_jina_reader_fetch_success(jina_provider: JinaResearchProvider) -> None:
    reader_payload = {
        "code": 200,
        "data": {
            "title": "Detailed Security Architecture Guide",
            "content": "# Security Architecture\nDetailed documentation on zero-trust models...",
        },
    }
    mock_resp = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=json.dumps(reader_payload).encode("utf-8"),
        request=httpx.Request("GET", "https://r.jina.ai/https://example.com/sec"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        item = await jina_provider.fetch("https://example.com/sec")

    assert item.source == "https://example.com/sec"
    assert item.title == "Detailed Security Architecture Guide"
    assert "zero-trust" in item.content
    assert item.approval_status == ApprovalStatus.UNVERIFIED


@pytest.mark.asyncio
async def test_jina_reader_fetch_empty_url_error(
    jina_provider: JinaResearchProvider,
) -> None:
    with pytest.raises(ResearchProviderError, match="Cannot fetch empty URL"):
        await jina_provider.fetch("   ")


@pytest.mark.asyncio
async def test_jina_reader_fetch_http_error(
    jina_provider: JinaResearchProvider,
) -> None:
    mock_resp = httpx.Response(
        status_code=404,
        content=b"Not Found",
        request=httpx.Request("GET", "https://r.jina.ai/https://badurl.com"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(ResearchProviderError, match="Jina Reader failed to fetch"):
            await jina_provider.fetch("https://badurl.com")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Strict Trust Hierarchy & Validation Integration Tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trust_hierarchy_jina_unverified_cannot_write_directly(
    jina_provider: JinaResearchProvider,
    mock_jina_search_response: dict,
) -> None:
    """
    CRITICAL TRUST TEST:
    Jina results are UNVERIFIED. Attempting to write them directly into Obsidian
    without validation MUST be rejected with MemoryWriterError.
    """
    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps(mock_jina_search_response).encode("utf-8"),
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        items = await jina_provider.search("Next.js auth")

    assert len(items) > 0
    unverified_item = items[0]
    assert unverified_item.approval_status == ApprovalStatus.UNVERIFIED

    obsidian = MockObsidianAdapter()
    writer = MemoryWriter(obsidian=obsidian)

    # Direct write of unverified item MUST fail
    with pytest.raises(WriteRejectedError, match="Write rejected"):
        await writer.write(
            content=unverified_item.content,
            evidence_refs=[unverified_item],
            approval_status=unverified_item.approval_status,
            target_note="Software-Web-Common-Knowledge-Base/Security/NextJS-Auth.md",
        )


@pytest.mark.asyncio
async def test_trust_hierarchy_jina_full_pipeline_validation_to_approved_write(
    jina_provider: JinaResearchProvider,
    mock_jina_search_response: dict,
) -> None:
    """
    Full pipeline test:
    Jina Search → UNVERIFIED Evidence → ValidationLayer → APPROVED → MemoryWriter → Obsidian
    """
    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps(mock_jina_search_response).encode("utf-8"),
        request=httpx.Request("GET", "https://s.jina.ai/test"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        items = await jina_provider.search("Next.js auth")

    # 1. Check all items start UNVERIFIED
    for it in items:
        assert it.approval_status == ApprovalStatus.UNVERIFIED

    # 2. Run through existing deterministic ValidationLayer
    validator = ValidationLayer()
    v_result = validator.validate(evidence=items, query="Next.js authentication best practices")
    assert v_result.status == ApprovalStatus.APPROVED
    assert v_result.approved is True

    # 3. MemoryWriter successfully persists APPROVED evidence
    obsidian = MockObsidianAdapter()
    writer = MemoryWriter(obsidian=obsidian)

    note_id, audit = await writer.write(
        content="Next.js authentication requires HttpOnly cookies and secure session tokens.",
        evidence_refs=items,
        approval_status=ApprovalStatus.APPROVED,
        target_note="Software-Web-Common-Knowledge-Base/Security/NextJS-Auth.md",
    )

    assert note_id is not None
    assert audit.write_status == "written"
    assert audit.approval_status == ApprovalStatus.APPROVED
    assert audit.evidence_count >= 2


# ─────────────────────────────────────────────────────────────────────────────
# 6. Provider Factory Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_build_research_provider_mock() -> None:
    with patch("app.main.settings.research_provider", "mock"):
        provider = build_research_provider()
        assert isinstance(provider, MockResearchProvider)


def test_build_research_provider_jina_with_key() -> None:
    with patch("app.main.settings.research_provider", "jina"), patch(
        "app.main.settings.research_api_key", "test_key_abc_123"
    ):
        provider = build_research_provider()
        assert isinstance(provider, JinaResearchProvider)


def test_build_research_provider_jina_missing_key_raises_error() -> None:
    with patch("app.main.settings.research_provider", "jina"), patch(
        "app.main.settings.research_api_key", ""
    ):
        with pytest.raises(ValueError, match="RESEARCH_API_KEY is required"):
            build_research_provider()


def test_build_research_provider_unsupported_type_raises_error() -> None:
    with patch("app.main.settings.research_provider", "unknown_provider_xyz"):
        with pytest.raises(ValueError, match="Unsupported RESEARCH_PROVIDER"):
            build_research_provider()
