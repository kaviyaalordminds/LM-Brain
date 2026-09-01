"""
Memory Agent — Local Obsidian Vault Retrieval Tests & Evaluation

Tests real retrieval against the actual 555 Markdown notes in the local vault:
  - Exact topic queries
  - Partial / semantic keywords queries
  - Multi-document retrieval
  - Nested folder retrieval
  - Metadata & tag filtering
  - Unknown queries (ensuring found=False and no hallucinations)
  - Source attribution integrity
  - MemoryAgent integration with LocalObsidianAdapter
  - Precision@1, Precision@3, and Latency evaluation metrics
"""

from __future__ import annotations

import time
from pathlib import Path
import pytest

from app.adapters.obsidian_adapter import LocalObsidianAdapter
from app.core.memory_agent import MemoryAgent
from app.core.memory_writer import MemoryWriter
from app.core.research import ResearchService
from app.core.retrieval import RetrievalService
from app.core.validation import ValidationLayer
from app.adapters.research_provider import MockResearchProvider
from app.models.memory import ApprovalStatus


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def local_adapter() -> LocalObsidianAdapter:
    """Instantiate LocalObsidianAdapter pointing to the real local vault."""
    vault_path = Path("C:/Lordminds/Multiagent/memory-agent/obsedian")
    adapter = LocalObsidianAdapter(vault_path=vault_path)
    return adapter


@pytest.fixture(scope="module")
def local_memory_agent(local_adapter: LocalObsidianAdapter) -> MemoryAgent:
    """Instantiate MemoryAgent wired with LocalObsidianAdapter."""
    retrieval = RetrievalService()
    research_provider = MockResearchProvider()
    research_svc = ResearchService(provider=research_provider)
    validation = ValidationLayer()
    writer = MemoryWriter(obsidian=local_adapter)
    return MemoryAgent(
        obsidian=local_adapter,
        retrieval=retrieval,
        research_svc=research_svc,
        validation=validation,
        writer=writer,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Exact Topic Queries
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query, expected_in_title, expected_folder",
    [
        ("Intelligent Agents", "Intelligent Agents", "01-AI-Fundamentals"),
        ("Convolutional Neural Networks", "Convolutional Neural Networks", "04-Deep-Learning"),
        ("Adapter Pattern", "Adapter Pattern", "08-Design-Patterns"),
        ("A* Search", "A* Search", "01-AI-Fundamentals"),
        ("Reinforcement Learning", "Reinforcement Learning", "02-Machine-Learning"),
        ("Supervised Learning", "Supervised Learning", "02-Machine-Learning"),
    ],
)
async def test_exact_topic_query(
    local_adapter: LocalObsidianAdapter,
    query: str,
    expected_in_title: str,
    expected_folder: str,
) -> None:
    """Exact topic queries retrieve the targeted document at Top-1."""
    results = await local_adapter.search(query)
    assert len(results) > 0, f"No results returned for exact topic query '{query}'"
    top1 = results[0]
    assert top1.approval_status == ApprovalStatus.RETRIEVED
    assert top1.source_note is not None
    assert expected_folder in top1.source_note
    assert expected_in_title.lower() in top1.content.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Partial & Related Keyword Queries
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_partial_keyword_query(local_adapter: LocalObsidianAdapter) -> None:
    """Partial keywords find relevant deep learning & vision topics."""
    results = await local_adapter.search("neural network convolution vision")
    assert len(results) > 0
    top_sources = [r.source_note for r in results[:3] if r.source_note]
    assert any("Convolutional" in s or "Computer-Vision" in s or "Deep-Learning" in s for s in top_sources)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Multiple Document Query
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multiple_document_query(local_adapter: LocalObsidianAdapter) -> None:
    """Broad queries return multiple relevant documents ranked by relevance."""
    results = await local_adapter.search("machine learning algorithms")
    assert len(results) >= 3
    # Check that results are sorted descending by relevance score
    scores = [r.relevance for r in results]
    assert scores == sorted(scores, reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Nested Folder Retrieval
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_nested_folder_retrieval(local_adapter: LocalObsidianAdapter) -> None:
    """Documents from nested folders in both AI and Software vaults are retrievable."""
    ai_results = await local_adapter.search("decision tree", filters={"folder": "AI-Knowledge-Base"})
    assert len(ai_results) > 0
    assert all(r.source_note and r.source_note.startswith("AI-Knowledge-Base") for r in ai_results)

    sw_results = await local_adapter.search("singleton pattern", filters={"folder": "Software-Web-Common-Knowledge-Base"})
    assert len(sw_results) > 0
    assert all(r.source_note and r.source_note.startswith("Software-Web-Common-Knowledge-Base") for r in sw_results)


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Metadata & Tag Aware Filtering
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_metadata_tag_filtering(local_adapter: LocalObsidianAdapter) -> None:
    """Searching with tag filter returns only matching tagged documents."""
    results = await local_adapter.search("pattern", filters={"tags": ["DesignPatterns"]})
    assert len(results) > 0
    for r in results:
        assert r.source_note is not None
        assert "Design-Patterns" in r.source_note or "Patterns" in r.source_note


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Unknown Query Returns Empty (No Hallucination)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unknown_query_returns_empty(local_adapter: LocalObsidianAdapter) -> None:
    """Queries for non-existent concepts return an empty result without hallucination."""
    results = await local_adapter.search("quantum warp tachyon hyperdrive 987654321")
    assert results == []


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Direct Note Read & Flexible Resolution
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_read_note_by_path_and_title(local_adapter: LocalObsidianAdapter) -> None:
    """Can read notes by exact path, relative path, or note title."""
    # 1. Exact path
    note = await local_adapter.read("AI-Knowledge-Base/01-AI-Fundamentals/001-Artificial-Intelligence-Fundamentals.md")
    assert note is not None
    assert "Artificial Intelligence" in note.content
    assert note.approval_status == ApprovalStatus.RETRIEVED

    # 2. Path without .md
    note2 = await local_adapter.read("AI-Knowledge-Base/01-AI-Fundamentals/001-Artificial-Intelligence-Fundamentals")
    assert note2 is not None
    assert note2.content == note.content

    # 3. By Title
    note3 = await local_adapter.read("Artificial Intelligence Fundamentals")
    assert note3 is not None
    assert "Artificial Intelligence" in note3.content


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Source Attribution Integrity
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_source_attribution_integrity(local_adapter: LocalObsidianAdapter) -> None:
    """All returned sources correspond to real, existing files in the vault."""
    results = await local_adapter.search("Docker Containers Kubernetes")
    assert len(results) > 0
    for r in results:
        assert len(r.sources) > 0
        src_path = local_adapter.vault_path / r.sources[0]
        assert src_path.exists(), f"Source file does not exist on disk: {src_path}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: MemoryAgent End-to-End Search & Context Assembly
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_agent_local_search_and_context(local_memory_agent: MemoryAgent) -> None:
    """MemoryAgent uses LocalObsidianAdapter to search and populate task context."""
    task_id = "task-local-eval-001"

    # Search existing topic
    search_resp = await local_memory_agent.search(query="Intelligent Agents", task_id=task_id)
    assert search_resp.found is True
    assert search_resp.count > 0
    assert search_resp.results[0].approval_status == ApprovalStatus.RETRIEVED

    # Retrieve context
    ctx_resp = await local_memory_agent.retrieve_context(task_id=task_id)
    assert ctx_resp.task_id == task_id
    assert len(ctx_resp.context) > 0
    assert len(ctx_resp.sources) > 0
    assert any("Intelligent-Agents" in s for s in ctx_resp.sources)


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: MemoryAgent Fallback on Unknown Topic
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_agent_unknown_topic(local_memory_agent: MemoryAgent) -> None:
    """MemoryAgent returns found=False when query is absent from the vault."""
    resp = await local_memory_agent.search(query="Unobtainium Gravitational Repulsor 999")
    assert resp.found is False
    assert resp.count == 0
    assert resp.results == []


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Benchmark Evaluation Suite (Precision, Recall, Latency)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieval_benchmark_evaluation(local_adapter: LocalObsidianAdapter) -> None:
    """
    Evaluates retrieval quality across 15 representative topics from the real vault.
    Calculates Precision@1, Precision@3, and Average Latency.
    """
    eval_set = [
        {"query": "Artificial Intelligence Fundamentals", "expected": "001-Artificial-Intelligence-Fundamentals"},
        {"query": "Intelligent Agents", "expected": "002-Intelligent-Agents"},
        {"query": "Rational Agents", "expected": "003-Rational-Agents"},
        {"query": "Problem Solving in AI", "expected": "004-Problem-Solving-in-AI"},
        {"query": "State Space Search", "expected": "005-State-Space-Search"},
        {"query": "A* Search", "expected": "008-A-Search"},
        {"query": "Constraint Satisfaction Problems", "expected": "010-Constraint-Satisfaction-Problems"},
        {"query": "Knowledge Representation", "expected": "011-Knowledge-Representation"},
        {"query": "Supervised Learning", "expected": "022-Supervised-Learning"},
        {"query": "Reinforcement Learning", "expected": "026-Reinforcement-Learning"},
        {"query": "Convolutional Neural Networks", "expected": "066-Convolutional-Neural-Networks"},
        {"query": "Adapter Pattern", "expected": "Adapter-Pattern"},
        {"query": "Builder Pattern", "expected": "Builder-Pattern"},
        {"query": "Application Security", "expected": "Application Security"},
        {"query": "Docker", "expected": "Docker"},
    ]

    latencies: list[float] = []
    top1_correct = 0
    top3_correct = 0

    print("\n" + "=" * 70)
    print("LOCAL OBSIDIAN RETRIEVAL BENCHMARK EVALUATION")
    print("=" * 70)

    for item in eval_set:
        t0 = time.perf_counter()
        results = await local_adapter.search(item["query"])
        t1 = time.perf_counter()
        lat_ms = (t1 - t0) * 1000
        latencies.append(lat_ms)

        top1_hit = False
        top3_hit = False

        if results:
            top1_src = results[0].source_note or ""
            if item["expected"] in top1_src:
                top1_hit = True
                top1_correct += 1

            top3_sources = [r.source_note or "" for r in results[:3]]
            if any(item["expected"] in s for s in top3_sources):
                top3_hit = True
                top3_correct += 1

            top1_str = results[0].source_note
        else:
            top1_str = "None"

        status = "PASS" if top1_hit else ("TOP-3 PASS" if top3_hit else "FAIL")
        print(f"Query: '{item['query']}' | Top-1: {top1_str} | Latency: {lat_ms:.2f}ms | [{status}]")

    num_evals = len(eval_set)
    p_at_1 = top1_correct / num_evals
    p_at_3 = top3_correct / num_evals
    avg_latency = sum(latencies) / num_evals

    print("-" * 70)
    print(f"Total Evaluation Queries: {num_evals}")
    print(f"Top-1 Accuracy (Precision@1): {p_at_1 * 100:.1f}% ({top1_correct}/{num_evals})")
    print(f"Top-3 Accuracy (Precision@3): {p_at_3 * 100:.1f}% ({top3_correct}/{num_evals})")
    print(f"Average Search Latency: {avg_latency:.2f} ms")
    print("=" * 70)

    assert p_at_1 >= 0.90, f"Precision@1 ({p_at_1:.2f}) was below 90%"
    assert p_at_3 >= 0.95, f"Precision@3 ({p_at_3:.2f}) was below 95%"
    assert avg_latency < 50.0, f"Average latency ({avg_latency:.2f}ms) exceeded 50ms"
