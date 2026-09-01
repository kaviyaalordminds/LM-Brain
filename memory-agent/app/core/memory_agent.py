"""
Memory Agent — Central Orchestrator

Coordinates all memory operations:
  search()          → query Obsidian, return retrieved results
  retrieve_context()→ assemble ranked context for a task
  research()        → external research (always returns UNVERIFIED)
  validate()        → deterministic evidence validation
  write()           → approved-only write to Obsidian

The MemoryAgent delegates to:
  RetrievalService  — context assembly and ranking
  ResearchService   — controlled external research
  ValidationLayer   — deterministic evidence validation
  MemoryWriter      — approved-only write guard
  ObsidianAdapter   — knowledge base operations

Architecture rule:
  UNVERIFIED → (validate) → VALIDATED → (write with APPROVED status) → APPROVED
  This pipeline can never be skipped or collapsed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.adapters.obsidian_adapter import ObsidianAdapter, ObsidianAdapterError
from app.core.memory_writer import DuplicateKnowledgeError, MemoryWriter, WriteRejectedError
from app.core.research import ResearchError, ResearchService
from app.core.retrieval import RetrievalService
from app.core.validation import ValidationLayer
from app.models.memory import (
    ApprovalStatus,
    ContextResponse,
    EvidenceItem,
    MemoryResult,
    MemoryWriteAudit,
    ResearchResponse,
    SearchResponse,
    ValidationResult,
    WriteResponse,
)

logger = logging.getLogger(__name__)


class MemoryAgentError(Exception):
    """General Memory Agent error."""


class KnowledgeNotFoundError(Exception):
    """Raised when information is explicitly unavailable."""


class MemoryAgent:
    """
    Central Memory Agent.

    All memory operations flow through this class.
    It coordinates sub-services but contains no low-level implementation.
    """

    def __init__(
        self,
        obsidian: ObsidianAdapter,
        retrieval: RetrievalService,
        research_svc: ResearchService,
        validation: ValidationLayer,
        writer: MemoryWriter,
    ) -> None:
        self._obsidian = obsidian
        self._retrieval = retrieval
        self._research_svc = research_svc
        self._validation = validation
        self._writer = writer

        # In-memory task context store: task_id → list[MemoryResult]
        # In production this would be backed by a cache/DB
        self._task_contexts: dict[str, list[MemoryResult]] = {}

    # ─────────────────────────────────────────────────────────────────────
    # search()
    # ─────────────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        task_id: str | None = None,
        context: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> SearchResponse:
        """
        Search Obsidian for knowledge relevant to *query*.

        Returns a SearchResponse with found=True/False.
        If found=False, the caller should invoke research().

        RULE 6: Never hallucinate a retrieved note. If the adapter returns
        nothing, found=False is returned explicitly.
        """
        log_extra = {"task_id": task_id, "query": query[:100]}
        logger.info("memory.search.started", extra=log_extra)

        try:
            raw_results = await self._obsidian.search(query, filters)
        except ObsidianAdapterError as exc:
            logger.error(
                "memory.search.adapter_error",
                extra={**log_extra, "error": str(exc)},
            )
            raise MemoryAgentError(f"Obsidian unavailable: {exc}") from exc

        assembled = self._retrieval.assemble_context(raw_results, task_id)
        found = self._retrieval.has_sufficient_knowledge(assembled)

        # Cache the context for this task
        if task_id and assembled:
            if task_id not in self._task_contexts:
                self._task_contexts[task_id] = []
            self._task_contexts[task_id].extend(assembled)

        logger.info(
            "memory.search.completed",
            extra={**log_extra, "result_count": len(assembled), "found": found},
        )
        return SearchResponse(results=assembled, found=found, count=len(assembled))

    # ─────────────────────────────────────────────────────────────────────
    # retrieve_context()
    # ─────────────────────────────────────────────────────────────────────

    async def retrieve_context(self, task_id: str) -> ContextResponse:
        """
        Return all cached memory context for a task.

        RULE 7: If context is unavailable, return an explicit empty response.
        Never fabricate context.
        """
        results = self._task_contexts.get(task_id, [])
        sources = self._retrieval.collect_sources(results)
        return ContextResponse(
            task_id=task_id,
            context=results,
            sources=sources,
            timestamp=datetime.now(timezone.utc),
        )

    # ─────────────────────────────────────────────────────────────────────
    # research()
    # ─────────────────────────────────────────────────────────────────────

    async def research(
        self,
        query: str,
        task_id: str | None = None,
    ) -> ResearchResponse:
        """
        Perform controlled external research.

        ALL returned evidence is marked UNVERIFIED.
        Never auto-promote to approved.
        """
        try:
            evidence = await self._research_svc.research(query, task_id)
        except ResearchError:
            raise
        except Exception as exc:
            raise MemoryAgentError(f"Research pipeline error: {exc}") from exc

        sources = self._research_svc.collect_source_urls(evidence)
        return ResearchResponse(evidence=evidence, sources=sources, count=len(evidence))

    # ─────────────────────────────────────────────────────────────────────
    # validate()
    # ─────────────────────────────────────────────────────────────────────

    def validate(
        self,
        evidence: list[EvidenceItem],
        query: str,
        context: str | None = None,
        task_id: str | None = None,
    ) -> ValidationResult:
        """
        Run deterministic validation on a list of evidence items.

        Returns a ValidationResult. Does NOT write anything.
        """
        return self._validation.validate(evidence, query, context, task_id)

    # ─────────────────────────────────────────────────────────────────────
    # write()
    # ─────────────────────────────────────────────────────────────────────

    async def write(
        self,
        content: str,
        evidence_refs: list[EvidenceItem],
        approval_status: ApprovalStatus,
        target_note: str,
        task_id: str | None = None,
    ) -> WriteResponse:
        """
        Write approved content to Obsidian.

        Only ApprovalStatus.APPROVED is accepted.
        All other statuses raise WriteRejectedError.
        """
        try:
            note_id, audit = await self._writer.write(
                content=content,
                evidence_refs=evidence_refs,
                approval_status=approval_status,
                target_note=target_note,
                task_id=task_id,
            )
        except WriteRejectedError:
            return WriteResponse(
                note_id=None,
                status="rejected",
                timestamp=datetime.now(timezone.utc),
                metadata={"reason": "Write rejected: approval status not approved"},
            )
        except DuplicateKnowledgeError as exc:
            return WriteResponse(
                note_id=None,
                status="rejected",
                timestamp=datetime.now(timezone.utc),
                metadata={"reason": str(exc)},
            )

        # If approved write succeeded, cache the result as trusted context
        if task_id:
            approved_result = MemoryResult(
                query=target_note,
                content=content,
                sources=[note_id],
                evidence_refs=evidence_refs,
                relevance=1.0,
                approval_status=ApprovalStatus.APPROVED,
                target_note=note_id,
                task_id=task_id,
                source_note=note_id,
            )
            if task_id not in self._task_contexts:
                self._task_contexts[task_id] = []
            self._task_contexts[task_id].append(approved_result)

        return WriteResponse(
            note_id=note_id,
            status="written",
            timestamp=audit.written_at,
            metadata={
                "target_note": target_note,
                "evidence_count": len(evidence_refs),
                "sources": [e.source for e in evidence_refs],
                "task_id": task_id,
                "approval_status": ApprovalStatus.APPROVED.value,
            },
        )

    # ─────────────────────────────────────────────────────────────────────
    # Full pipeline: search → research → validate → write
    # ─────────────────────────────────────────────────────────────────────

    async def search_or_research(
        self,
        query: str,
        task_id: str | None = None,
        target_note: str | None = None,
    ) -> SearchResponse:
        """
        Full pipeline:
          1. Search Obsidian
          2. If found → return retrieved results
          3. If not found → research → validate → if approved → write → return

        Returns a SearchResponse. Results are marked with appropriate
        ApprovalStatus at each stage.
        """
        # Step 1: Search Obsidian
        search_resp = await self.search(query, task_id)
        if search_resp.found:
            return search_resp

        # Step 2: External research
        try:
            research_resp = await self.research(query, task_id)
        except ResearchError as exc:
            raise MemoryAgentError(f"Research failed: {exc}") from exc

        if not research_resp.evidence:
            # Return empty — explicitly unavailable
            return SearchResponse(results=[], found=False, count=0)

        # Step 3: Validate
        validation = self.validate(research_resp.evidence, query, task_id=task_id)

        if not validation.approved:
            # Research rejected — do not store
            rejected_results = [
                MemoryResult(
                    query=query,
                    content=item.content,
                    sources=[item.source],
                    evidence_refs=[item],
                    relevance=item.relevance,
                    approval_status=ApprovalStatus.REJECTED,
                    task_id=task_id,
                )
                for item in research_resp.evidence
            ]
            return SearchResponse(results=rejected_results, found=False, count=0)

        # Step 4: Write approved knowledge to Obsidian
        note_path = target_note or f"research/{query[:40].replace(' ', '-').lower()}"
        content_to_write = "\n\n".join(
            f"## Source: {item.source}\n{item.content}"
            for item in research_resp.evidence
        )

        write_resp = await self.write(
            content=content_to_write,
            evidence_refs=research_resp.evidence,
            approval_status=ApprovalStatus.APPROVED,
            target_note=note_path,
            task_id=task_id,
        )

        if write_resp.status == "written":
            approved_result = MemoryResult(
                query=query,
                content=content_to_write,
                sources=research_resp.sources,
                evidence_refs=research_resp.evidence,
                relevance=max(i.relevance for i in research_resp.evidence),
                approval_status=ApprovalStatus.APPROVED,
                target_note=write_resp.note_id,
                task_id=task_id,
                source_note=write_resp.note_id,
            )
            return SearchResponse(results=[approved_result], found=True, count=1)

        # Write was rejected for some reason
        return SearchResponse(results=[], found=False, count=0)
