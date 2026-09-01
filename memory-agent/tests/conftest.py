"""
Shared test fixtures for the Memory Agent test suite.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.adapters.obsidian_adapter import MockObsidianAdapter
from app.adapters.research_provider import MockResearchProvider
from app.core.memory_agent import MemoryAgent
from app.core.memory_writer import MemoryWriter
from app.core.research import ResearchService
from app.core.retrieval import RetrievalService
from app.core.validation import ValidationLayer
from app.main import create_app
from app.models.memory import ApprovalStatus, EvidenceItem


# ─────────────────────────────────────────────────────────────────────────────
# Adapter fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def obsidian() -> MockObsidianAdapter:
    """Fresh MockObsidianAdapter seeded with default notes."""
    return MockObsidianAdapter()


@pytest.fixture
def failing_obsidian() -> MockObsidianAdapter:
    """MockObsidianAdapter configured to simulate failures."""
    return MockObsidianAdapter(simulate_failure=True)


@pytest.fixture
def research_provider() -> MockResearchProvider:
    """Standard MockResearchProvider."""
    return MockResearchProvider()


@pytest.fixture
def failing_research_provider() -> MockResearchProvider:
    """MockResearchProvider that simulates provider failure."""
    return MockResearchProvider(simulate_failure=True)


@pytest.fixture
def timeout_research_provider() -> MockResearchProvider:
    """MockResearchProvider that simulates timeout."""
    return MockResearchProvider(simulate_timeout=True)


@pytest.fixture
def empty_research_provider() -> MockResearchProvider:
    """MockResearchProvider that returns no results."""
    return MockResearchProvider(empty_results=True)


# ─────────────────────────────────────────────────────────────────────────────
# Service fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def retrieval() -> RetrievalService:
    return RetrievalService()


@pytest.fixture
def validation() -> ValidationLayer:
    return ValidationLayer()


@pytest.fixture
def research_svc(research_provider: MockResearchProvider) -> ResearchService:
    return ResearchService(provider=research_provider)


@pytest.fixture
def failing_research_svc(failing_research_provider: MockResearchProvider) -> ResearchService:
    return ResearchService(provider=failing_research_provider)


@pytest.fixture
def writer(obsidian: MockObsidianAdapter) -> MemoryWriter:
    return MemoryWriter(obsidian=obsidian)


# ─────────────────────────────────────────────────────────────────────────────
# MemoryAgent fixture
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def memory_agent(
    obsidian: MockObsidianAdapter,
    retrieval: RetrievalService,
    research_svc: ResearchService,
    validation: ValidationLayer,
    writer: MemoryWriter,
) -> MemoryAgent:
    return MemoryAgent(
        obsidian=obsidian,
        retrieval=retrieval,
        research_svc=research_svc,
        validation=validation,
        writer=writer,
    )


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI test client fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def app_with_mock_agent(memory_agent: MemoryAgent):
    """FastAPI app with a pre-built MemoryAgent in app state."""
    application = create_app()
    application.state.memory_agent = memory_agent
    return application


@pytest.fixture
def test_client(app_with_mock_agent) -> TestClient:
    """Synchronous test client."""
    return TestClient(app_with_mock_agent, raise_server_exceptions=True)


@pytest_asyncio.fixture
async def async_client(app_with_mock_agent) -> AsyncClient:
    """Async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_mock_agent),
        base_url="http://test",
    ) as client:
        yield client


# ─────────────────────────────────────────────────────────────────────────────
# Sample data helpers
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def good_evidence() -> list[EvidenceItem]:
    """A list of evidence items that should pass validation."""
    return [
        EvidenceItem(
            source="https://example.com/article-1",
            title="Article One",
            content=(
                "This is a well-sourced article with substantial content about "
                "the topic in question. It contains more than fifty characters of "
                "useful information derived from primary sources."
            ),
            relevance=0.85,
            approval_status=ApprovalStatus.UNVERIFIED,
        ),
        EvidenceItem(
            source="https://other-domain.org/reference-2",
            title="Reference Two",
            content=(
                "A second independent source corroborating the findings. "
                "Providing additional context and evidence from a different domain "
                "to support multi-source validation requirements."
            ),
            relevance=0.75,
            approval_status=ApprovalStatus.UNVERIFIED,
        ),
    ]


@pytest.fixture
def weak_evidence() -> list[EvidenceItem]:
    """A list of evidence items that should fail validation (too short)."""
    return [
        EvidenceItem(
            source="https://example.com/short",
            title="Short",
            content="Too short.",  # less than 50 chars
            relevance=0.1,
            approval_status=ApprovalStatus.UNVERIFIED,
        ),
    ]
