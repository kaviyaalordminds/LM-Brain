"""
Memory Agent — API Integration Tests + End-to-End Pipeline Test

Tests:
  - All 5 API endpoints (contract verification)
  - Full E2E pipeline: query → Obsidian miss → research → validate → write → confirm
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.obsidian_adapter import MockObsidianAdapter
from app.adapters.research_provider import MockResearchProvider
from app.core.memory_agent import MemoryAgent
from app.core.memory_writer import MemoryWriter
from app.core.research import ResearchService
from app.core.retrieval import RetrievalService
from app.core.validation import ValidationLayer
from app.models.memory import ApprovalStatus


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/search
# ─────────────────────────────────────────────────────────────────────────────


def test_api_search_found(test_client: TestClient) -> None:
    """Search for a term present in seeded notes returns HTTP 200 with results."""
    resp = test_client.post(
        "/api/v1/memory/search",
        json={"query": "architecture overview"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "found" in data
    assert "count" in data
    assert data["found"] is True
    assert data["count"] > 0
    # Verify result structure
    first = data["results"][0]
    assert "id" in first
    assert "content" in first
    assert "approvalStatus" in first
    assert "sources" in first
    assert first["approvalStatus"] == ApprovalStatus.RETRIEVED.value


def test_api_search_not_found(test_client: TestClient) -> None:
    """Search for an unknown term returns HTTP 200 with found=False."""
    resp = test_client.post(
        "/api/v1/memory/search",
        json={"query": "xylophone quantum refrigerator"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is False
    assert data["count"] == 0


def test_api_search_with_task_id(test_client: TestClient) -> None:
    """Search with a taskId passes the correlation ID through."""
    resp = test_client.post(
        "/api/v1/memory/search",
        json={"query": "security", "taskId": "task-123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # Results for a known topic should be found
    assert data["found"] is True


def test_api_search_empty_query_rejected(test_client: TestClient) -> None:
    """Empty query string must be rejected with HTTP 422."""
    resp = test_client.post(
        "/api/v1/memory/search",
        json={"query": ""},
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/research
# ─────────────────────────────────────────────────────────────────────────────


def test_api_research_returns_evidence(test_client: TestClient) -> None:
    """Research endpoint returns evidence items marked UNVERIFIED."""
    resp = test_client.post(
        "/api/v1/memory/research",
        json={"query": "AI memory systems"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "evidence" in data
    assert "sources" in data
    assert "count" in data
    assert data["count"] > 0
    # All evidence must be UNVERIFIED
    for item in data["evidence"]:
        assert item["approvalStatus"] == ApprovalStatus.UNVERIFIED.value, (
            f"Evidence from {item['source']} was not UNVERIFIED"
        )


def test_api_research_preserves_sources(test_client: TestClient) -> None:
    """Research results must include source URLs."""
    resp = test_client.post(
        "/api/v1/memory/research",
        json={"query": "knowledge validation"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sources"]) > 0
    for src in data["sources"]:
        assert src.startswith("http")


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/validate
# ─────────────────────────────────────────────────────────────────────────────


def test_api_validate_approves_good_evidence(test_client: TestClient) -> None:
    """Good evidence passes validation and returns approved=True."""
    evidence = [
        {
            "source": "https://example.com/ref1",
            "title": "Source One",
            "content": "This is substantial content from source one. " * 3,
            "relevance": 0.8,
            "approvalStatus": "unverified",
        },
        {
            "source": "https://another-domain.org/ref2",
            "title": "Source Two",
            "content": "This is substantial content from source two. " * 3,
            "relevance": 0.7,
            "approvalStatus": "unverified",
        },
    ]
    resp = test_client.post(
        "/api/v1/memory/validate",
        json={"evidence": evidence, "query": "AI systems"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "approved" in data
    assert "status" in data
    assert "reason" in data
    assert "assessment" in data
    assert data["approved"] is True
    assert data["status"] == ApprovalStatus.APPROVED.value


def test_api_validate_rejects_empty_evidence(test_client: TestClient) -> None:
    """No evidence results in rejection."""
    resp = test_client.post(
        "/api/v1/memory/validate",
        json={"evidence": [], "query": "anything"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["approved"] is False
    assert data["status"] == ApprovalStatus.REJECTED.value


def test_api_validate_rejects_short_content(test_client: TestClient) -> None:
    """Evidence with very short content fails R4."""
    evidence = [
        {
            "source": "https://example.com/short",
            "title": "Short",
            "content": "Tiny.",
            "relevance": 0.5,
            "approvalStatus": "unverified",
        }
    ]
    resp = test_client.post(
        "/api/v1/memory/validate",
        json={"evidence": evidence, "query": "test"},
    )
    assert resp.status_code == 200
    assert resp.json()["approved"] is False


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/memory/write
# ─────────────────────────────────────────────────────────────────────────────


def test_api_write_approved_succeeds(test_client: TestClient) -> None:
    """Writing approved content returns status=written and a noteId."""
    resp = test_client.post(
        "/api/v1/memory/write",
        json={
            "content": "Approved knowledge content from research pipeline.",
            "evidenceRefs": [],
            "approvalStatus": "approved",
            "targetNote": "research/api-write-test",
            "taskId": "task-write-001",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "written"
    assert data["noteId"] == "research/api-write-test"
    assert "timestamp" in data
    assert "metadata" in data


def test_api_write_unverified_is_rejected(test_client: TestClient) -> None:
    """Writing unverified content returns status=rejected."""
    resp = test_client.post(
        "/api/v1/memory/write",
        json={
            "content": "Unverified content that must not be stored.",
            "evidenceRefs": [],
            "approvalStatus": "unverified",
            "targetNote": "research/unverified-test",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["noteId"] is None


def test_api_write_pending_is_rejected(test_client: TestClient) -> None:
    """Writing pending content returns status=rejected."""
    resp = test_client.post(
        "/api/v1/memory/write",
        json={
            "content": "Pending content.",
            "evidenceRefs": [],
            "approvalStatus": "pending",
            "targetNote": "research/pending-test",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_api_write_validated_is_rejected(test_client: TestClient) -> None:
    """Writing validated-but-not-approved content returns status=rejected."""
    resp = test_client.post(
        "/api/v1/memory/write",
        json={
            "content": "Validated content.",
            "evidenceRefs": [],
            "approvalStatus": "validated",
            "targetNote": "research/validated-test",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_api_write_invalid_status_rejected(test_client: TestClient) -> None:
    """Invalid approvalStatus value returns HTTP 422."""
    resp = test_client.post(
        "/api/v1/memory/write",
        json={
            "content": "Some content.",
            "evidenceRefs": [],
            "approvalStatus": "TRUST_ME",
            "targetNote": "research/invalid-status",
        },
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/memory/context/{taskId}
# ─────────────────────────────────────────────────────────────────────────────


def test_api_context_returns_empty_for_unknown_task(test_client: TestClient) -> None:
    """Context endpoint returns empty for unknown task — never fabricates."""
    resp = test_client.get("/api/v1/memory/context/nonexistent-task-xyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["taskId"] == "nonexistent-task-xyz"
    assert data["context"] == []
    assert data["sources"] == []


def test_api_context_after_search(test_client: TestClient) -> None:
    """After a search with taskId, context endpoint returns those results."""
    task_id = "task-context-api-test"

    # Prime context
    test_client.post(
        "/api/v1/memory/search",
        json={"query": "engineering standards", "taskId": task_id},
    )

    # Retrieve context
    resp = test_client.get(f"/api/v1/memory/context/{task_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["taskId"] == task_id
    assert isinstance(data["context"], list)
    assert isinstance(data["sources"], list)


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────


def test_health_endpoint(test_client: TestClient) -> None:
    resp = test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# END-TO-END TEST
# Full pipeline: query → Obsidian miss → research → validate → write → confirm
# ─────────────────────────────────────────────────────────────────────────────


def test_e2e_full_pipeline(test_client: TestClient) -> None:
    """
    E2E test demonstrating the complete Memory Agent pipeline:

    1. Search Obsidian for an unknown topic → found=False
    2. Call /research → get UNVERIFIED evidence
    3. Call /validate → evidence approved
    4. Call /write with approved status → written to Obsidian
    5. Search Obsidian again → knowledge is now found
    """
    unique_topic = "quantum-memory-architecture-e2e-test"
    task_id = "e2e-task-001"
    target_note = f"research/{unique_topic}"

    # ── Step 1: Search — expect miss ──────────────────────────────────────
    search_resp = test_client.post(
        "/api/v1/memory/search",
        json={"query": unique_topic, "taskId": task_id},
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["found"] is False, "Expected a miss on the first search"

    # ── Step 2: Research — collect evidence ───────────────────────────────
    research_resp = test_client.post(
        "/api/v1/memory/research",
        json={"query": unique_topic, "taskId": task_id},
    )
    assert research_resp.status_code == 200
    research_data = research_resp.json()
    assert research_data["count"] > 0, "Expected at least one evidence item"

    # Verify all evidence is UNVERIFIED
    for item in research_data["evidence"]:
        assert item["approvalStatus"] == "unverified", (
            f"Evidence from '{item['source']}' was not UNVERIFIED"
        )

    # ── Step 3: Validate — approve the evidence ───────────────────────────
    validate_resp = test_client.post(
        "/api/v1/memory/validate",
        json={
            "evidence": research_data["evidence"],
            "query": unique_topic,
        },
    )
    assert validate_resp.status_code == 200
    validate_data = validate_resp.json()
    assert validate_data["approved"] is True, (
        f"Validation failed unexpectedly: {validate_data['reason']}"
    )

    # ── Step 4: Write — only now with approved status ─────────────────────
    content_to_write = "\n\n".join(
        f"Source: {e['source']}\n{e['content']}"
        for e in research_data["evidence"]
    )
    write_resp = test_client.post(
        "/api/v1/memory/write",
        json={
            "content": content_to_write,
            "evidenceRefs": research_data["evidence"],
            "approvalStatus": "approved",
            "targetNote": target_note,
            "taskId": task_id,
        },
    )
    assert write_resp.status_code == 200
    write_data = write_resp.json()
    assert write_data["status"] == "written", (
        f"Write failed: {write_data}"
    )
    assert write_data["noteId"] == target_note

    # ── Step 5: Search again — knowledge must now be found ────────────────
    search_again_resp = test_client.post(
        "/api/v1/memory/search",
        json={"query": unique_topic, "taskId": task_id},
    )
    assert search_again_resp.status_code == 200
    final_data = search_again_resp.json()
    assert final_data["found"] is True, (
        "After approved write, the knowledge should be retrievable from Obsidian"
    )
    assert final_data["count"] > 0

    # The written note must have RETRIEVED status (it's now in Obsidian)
    written_result = next(
        (r for r in final_data["results"] if r.get("sourceNote") == target_note),
        None,
    )
    assert written_result is not None, (
        f"Could not find written note '{target_note}' in search results"
    )
    assert written_result["approvalStatus"] == ApprovalStatus.RETRIEVED.value
