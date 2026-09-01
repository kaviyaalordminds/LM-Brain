"""
Memory Agent — Unit Tests

Tests:
  1.  Internal search returns relevant knowledge
  2.  Internal search returns empty for unknown query
  3.  Research returns evidence items
  4.  Research results are always marked UNVERIFIED
  5.  Strong evidence passes validation
  6.  Weak/conflicting evidence fails validation
  7.  Unverified memory write is rejected
  8.  Pending memory write is rejected
  9.  Validated-but-not-approved write is rejected
  10. Approved memory write succeeds
  11. Evidence references survive the write
  12. Obsidian adapter failure is handled
  13. Research provider failure is handled
  14. Duplicate/conflicting note write is handled
  15. Context retrieval works
"""

from __future__ import annotations

import pytest

from app.adapters.obsidian_adapter import MockObsidianAdapter, ObsidianAdapterError
from app.adapters.research_provider import MockResearchProvider
from app.core.memory_agent import MemoryAgent, MemoryAgentError
from app.core.memory_writer import DuplicateKnowledgeError, MemoryWriter, WriteRejectedError
from app.core.research import ResearchError, ResearchService
from app.core.retrieval import RetrievalService
from app.core.validation import ValidationLayer
from app.models.memory import ApprovalStatus, EvidenceItem


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Internal search returns relevant knowledge
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_returns_relevant_knowledge(memory_agent: MemoryAgent) -> None:
    """Searching for a term present in seeded notes returns results."""
    resp = await memory_agent.search(query="architecture overview")
    assert resp.found is True
    assert resp.count > 0
    assert all(r.approval_status == ApprovalStatus.RETRIEVED for r in resp.results)
    # Every result must carry a source note
    assert all(r.source_note is not None for r in resp.results)


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Internal search returns empty for unknown query
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_returns_empty_for_unknown_query(memory_agent: MemoryAgent) -> None:
    """Searching for a term not present in Obsidian returns found=False."""
    resp = await memory_agent.search(query="quantum entanglement photon spin")
    assert resp.found is False
    assert resp.count == 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Research returns evidence items
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_research_returns_evidence(memory_agent: MemoryAgent) -> None:
    """External research returns at least one evidence item."""
    resp = await memory_agent.research(query="AI memory systems")
    assert resp.count > 0
    assert len(resp.evidence) > 0
    assert len(resp.sources) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Research results are ALWAYS marked UNVERIFIED
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_research_results_are_unverified(memory_agent: MemoryAgent) -> None:
    """All evidence returned by research must be UNVERIFIED — never auto-promoted."""
    resp = await memory_agent.research(query="knowledge validation")
    for item in resp.evidence:
        assert item.approval_status == ApprovalStatus.UNVERIFIED, (
            f"Evidence from '{item.source}' has status '{item.approval_status}' "
            f"instead of UNVERIFIED"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Strong evidence passes validation
# ─────────────────────────────────────────────────────────────────────────────


def test_strong_evidence_passes_validation(
    validation: ValidationLayer,
    good_evidence: list[EvidenceItem],
) -> None:
    """Well-sourced evidence with sufficient content passes all validation rules."""
    result = validation.validate(evidence=good_evidence, query="test query")
    assert result.approved is True
    assert result.status == ApprovalStatus.APPROVED
    assert "passed" in result.reason.lower()
    # All evidence items should be promoted to VALIDATED
    for item in good_evidence:
        assert item.approval_status == ApprovalStatus.VALIDATED


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Weak/insufficient evidence fails validation
# ─────────────────────────────────────────────────────────────────────────────


def test_weak_evidence_fails_validation(
    validation: ValidationLayer,
    weak_evidence: list[EvidenceItem],
) -> None:
    """Evidence with content below the minimum length fails validation."""
    result = validation.validate(evidence=weak_evidence, query="test query")
    assert result.approved is False
    assert result.status == ApprovalStatus.REJECTED
    # All evidence items should be marked REJECTED
    for item in weak_evidence:
        assert item.approval_status == ApprovalStatus.REJECTED


def test_empty_evidence_fails_validation(validation: ValidationLayer) -> None:
    """No evidence at all must be rejected."""
    result = validation.validate(evidence=[], query="test query")
    assert result.approved is False
    assert result.status == ApprovalStatus.REJECTED


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Unverified memory write is rejected
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unverified_write_is_rejected(writer: MemoryWriter) -> None:
    """Writing with UNVERIFIED status must raise WriteRejectedError."""
    with pytest.raises(WriteRejectedError) as exc_info:
        await writer.write(
            content="Some content",
            evidence_refs=[],
            approval_status=ApprovalStatus.UNVERIFIED,
            target_note="test/unverified-note",
        )
    assert "unverified" in str(exc_info.value).lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Pending memory write is rejected
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pending_write_is_rejected(writer: MemoryWriter) -> None:
    """Writing with PENDING status must raise WriteRejectedError."""
    with pytest.raises(WriteRejectedError):
        await writer.write(
            content="Some content",
            evidence_refs=[],
            approval_status=ApprovalStatus.PENDING,
            target_note="test/pending-note",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Validated-but-not-approved write is rejected
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_validated_not_approved_write_is_rejected(writer: MemoryWriter) -> None:
    """VALIDATED status is not sufficient — only APPROVED may be written."""
    with pytest.raises(WriteRejectedError) as exc_info:
        await writer.write(
            content="Validated but not approved content",
            evidence_refs=[],
            approval_status=ApprovalStatus.VALIDATED,
            target_note="test/validated-note",
        )
    assert "validated" in str(exc_info.value).lower() or "approved" in str(exc_info.value).lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: Approved memory write succeeds
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_approved_write_succeeds(writer: MemoryWriter) -> None:
    """APPROVED content is successfully written to Obsidian."""
    note_id, audit = await writer.write(
        content="Approved trusted knowledge about our product.",
        evidence_refs=[],
        approval_status=ApprovalStatus.APPROVED,
        target_note="research/approved-knowledge",
        task_id="task-001",
    )
    assert note_id == "research/approved-knowledge"
    assert audit.write_status == "written"
    assert audit.task_id == "task-001"


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Evidence references survive the write
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_evidence_references_preserved_on_write(
    writer: MemoryWriter,
    good_evidence: list[EvidenceItem],
) -> None:
    """Evidence source references must be preserved in the audit record."""
    note_id, audit = await writer.write(
        content="Content with preserved evidence.",
        evidence_refs=good_evidence,
        approval_status=ApprovalStatus.APPROVED,
        target_note="research/evidence-preserved",
    )
    assert audit.evidence_count == len(good_evidence)
    assert len(audit.sources) == len(good_evidence)
    for item in good_evidence:
        assert item.source in audit.sources


# ─────────────────────────────────────────────────────────────────────────────
# Test 12: Obsidian adapter failure is handled
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_obsidian_failure_raises_agent_error(
    failing_obsidian: MockObsidianAdapter,
    retrieval: RetrievalService,
    research_svc: ResearchService,
    validation: ValidationLayer,
) -> None:
    """When Obsidian is unavailable, MemoryAgent raises MemoryAgentError."""
    failing_writer = MemoryWriter(obsidian=failing_obsidian)
    agent = MemoryAgent(
        obsidian=failing_obsidian,
        retrieval=retrieval,
        research_svc=research_svc,
        validation=validation,
        writer=failing_writer,
    )
    with pytest.raises(MemoryAgentError) as exc_info:
        await agent.search(query="architecture")
    assert "obsidian unavailable" in str(exc_info.value).lower()


# ─────────────────────────────────────────────────────────────────────────────
# Test 13: Research provider failure is handled
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_research_provider_failure_raises_research_error(
    obsidian: MockObsidianAdapter,
    failing_research_svc: ResearchService,
    retrieval: RetrievalService,
    validation: ValidationLayer,
) -> None:
    """When the research provider fails, ResearchError is raised."""
    writer = MemoryWriter(obsidian=obsidian)
    agent = MemoryAgent(
        obsidian=obsidian,
        retrieval=retrieval,
        research_svc=failing_research_svc,
        validation=validation,
        writer=writer,
    )
    with pytest.raises(ResearchError):
        await agent.research(query="anything")


# ─────────────────────────────────────────────────────────────────────────────
# Test 14: Duplicate/conflicting note write is handled
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duplicate_write_is_rejected(writer: MemoryWriter) -> None:
    """Writing to a note that already exists raises DuplicateKnowledgeError."""
    # First write should succeed
    await writer.write(
        content="Original content.",
        evidence_refs=[],
        approval_status=ApprovalStatus.APPROVED,
        target_note="research/duplicate-test",
    )
    # Second write to the same note must be rejected
    with pytest.raises(DuplicateKnowledgeError):
        await writer.write(
            content="Attempting to overwrite.",
            evidence_refs=[],
            approval_status=ApprovalStatus.APPROVED,
            target_note="research/duplicate-test",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 15: Context retrieval works
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_context_retrieval_works(memory_agent: MemoryAgent) -> None:
    """Context retrieval returns cached results for a task."""
    task_id = "task-context-test"

    # Prime context by searching
    await memory_agent.search(query="security guidelines", task_id=task_id)

    # Retrieve context
    ctx = await memory_agent.retrieve_context(task_id)
    assert ctx.task_id == task_id
    assert isinstance(ctx.context, list)
    assert isinstance(ctx.sources, list)


@pytest.mark.asyncio
async def test_context_retrieval_empty_for_unknown_task(memory_agent: MemoryAgent) -> None:
    """Context retrieval returns empty list for unknown task ID — no hallucination."""
    ctx = await memory_agent.retrieve_context("nonexistent-task-id")
    assert ctx.context == []
    assert ctx.sources == []
