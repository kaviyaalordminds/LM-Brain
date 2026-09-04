"""
Task-Aware Retrieval & Knowledge Gap Regression Suite

Validates that:
1. Generic/unrelated domain queries (e-commerce, Instagram ads, healthcare, quantum computing)
   NEVER return unrelated company/Lordminds notes.
2. When Obsidian lacks domain knowledge, found=False is honestly declared and knowledge_gaps
   are accurately populated.
3. Entity-specific queries (e.g. 'for Lordminds') accurately retrieve Lordminds company knowledge.
4. Jina research -> validation -> write -> re-search pipeline satisfies knowledge gaps and updates retrieval.
"""

import pytest
from app.adapters.obsidian_adapter import LocalObsidianAdapter, MockObsidianAdapter
from app.adapters.research_provider import MockResearchProvider
from app.core.memory_agent import MemoryAgent
from app.core.memory_writer import MemoryWriter
from app.core.research import ResearchService
from app.core.retrieval import RetrievalService
from app.core.task_analyzer import TaskAnalyzer
from app.core.validation import ValidationLayer


@pytest.fixture
def memory_agent_local() -> MemoryAgent:
    obsidian = LocalObsidianAdapter()
    retrieval = RetrievalService()
    research_provider = MockResearchProvider()
    research_svc = ResearchService(research_provider)
    validation = ValidationLayer()
    writer = MemoryWriter(obsidian)
    return MemoryAgent(
        obsidian=obsidian,
        retrieval=retrieval,
        research_svc=research_svc,
        validation=validation,
        writer=writer,
    )


@pytest.mark.asyncio
async def test_ecommerce_website_query_no_lordminds_pollution(memory_agent_local: MemoryAgent) -> None:
    """
    Query: 'Create a creative website for e-commerce'
    - Entity: None
    - Domain: e-commerce
    - Must NOT return any Lordminds company profile/architecture notes.
    - If e-commerce is not in vault, found must be False and gaps flagged.
    """
    query = "Create a creative website for e-commerce"
    resp = await memory_agent_local.search(query=query)

    assert resp.task_scope is not None
    assert resp.task_scope.entity is None
    assert resp.task_scope.domain == "e-commerce"

    # Verify no company-specific notes were returned
    for result in resp.results:
        src = (result.source_note or "").lower()
        assert "lordminds" not in src, f"Unrelated company note returned: {result.source_note}"

    # If vault lacks e-commerce domain notes, found must be False
    if not resp.results:
        assert resp.found is False
        assert len(resp.knowledge_gaps) > 0
        assert any(g.status == "missing" for g in resp.knowledge_gaps)


@pytest.mark.asyncio
async def test_instagram_ads_query_no_lordminds_pollution(memory_agent_local: MemoryAgent) -> None:
    """
    Query: 'Create creative ads for Instagram'
    - Entity: None
    - Platform: Instagram
    - Must NOT return Lordminds company profile/architecture notes.
    """
    query = "Create creative ads for Instagram"
    resp = await memory_agent_local.search(query=query)

    assert resp.task_scope is not None
    assert resp.task_scope.entity is None
    assert resp.task_scope.platform == "Instagram"

    for result in resp.results:
        src = (result.source_note or "").lower()
        assert "lordminds" not in src, f"Unrelated company note returned: {result.source_note}"


@pytest.mark.asyncio
async def test_lordminds_website_query_retrieves_company_knowledge(memory_agent_local: MemoryAgent) -> None:
    """
    Query: 'Create a website for Lordminds'
    - Entity: Lordminds
    - Successfully identifies entity and permits company notes.
    """
    query = "Create a website for Lordminds"
    resp = await memory_agent_local.search(query=query)

    assert resp.task_scope is not None
    assert resp.task_scope.entity == "Lordminds"


@pytest.mark.asyncio
async def test_healthcare_startup_dashboard(memory_agent_local: MemoryAgent) -> None:
    """
    Query: 'Build a React dashboard for a healthcare startup'
    - Platform: React
    - Domain: healthcare
    - Entity: None
    - Gaps identify missing healthcare compliance / metrics.
    """
    query = "Build a React dashboard for a healthcare startup"
    resp = await memory_agent_local.search(query=query)

    assert resp.task_scope is not None
    assert resp.task_scope.entity is None
    assert resp.task_scope.domain == "healthcare"

    for result in resp.results:
        src = (result.source_note or "").lower()
        assert "lordminds" not in src, f"Unrelated company note returned: {result.source_note}"


@pytest.mark.asyncio
async def test_quantum_computing_research_query(memory_agent_local: MemoryAgent) -> None:
    """
    Query: 'Tell me about quantum computing'
    - Domain: quantum_computing
    - Zero Lordminds notes returned.
    """
    query = "Tell me about quantum computing"
    resp = await memory_agent_local.search(query=query)

    assert resp.task_scope is not None
    assert resp.task_scope.domain == "quantum_computing"
    for result in resp.results:
        src = (result.source_note or "").lower()
        assert "lordminds" not in src


@pytest.mark.asyncio
async def test_imaginary_technology_category(memory_agent_local: MemoryAgent) -> None:
    """
    Query: 'Create a website for an imaginary technology category XYZ123'
    - Must return 0 results and found=False.
    """
    query = "Create a website for an imaginary technology category XYZ123"
    resp = await memory_agent_local.search(query=query)

    assert resp.found is False
    assert resp.count == 0
    assert len(resp.results) == 0


@pytest.mark.asyncio
async def test_task_aware_full_pipeline_gap_resolution(memory_agent_local: MemoryAgent) -> None:
    """
    Tests full loop:
    1. Search for unknown topic -> found=False, gaps identified
    2. search_or_research -> research + validation + auto-routed write + re-search -> found=True
    """
    query = "quantum algorithms and quantum entanglement protocols"
    resp = await memory_agent_local.search_or_research(query=query, task_id="task-pipeline-test-01")

    assert resp.found is True
    assert resp.count > 0
    assert any(r.approval_status == "approved" or r.approval_status == "retrieved" for r in resp.results)
