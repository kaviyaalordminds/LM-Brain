"""
Memory Agent — Central Orchestrator

Coordinates all memory operations:
  search()          → query Obsidian, return retrieved results
  retrieve_context()→ assemble ranked context for a task
  research()        → external research (always returns UNVERIFIED)
  validate()        → deterministic evidence validation
  write()           → approved-only write to Obsidian

The MemoryAgent delegates to:
  TaskAnalyzer      — parses tasks into domain, entity, platform, requirements
  RetrievalService  — context assembly, ranking, and gap assessment
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
from app.core.task_analyzer import TaskAnalyzer
from app.core.validation import ValidationLayer
from app.models.memory import (
    ApprovalStatus,
    ContextResponse,
    EvidenceItem,
    KnowledgeGapItem,
    MemoryResult,
    MemoryWriteAudit,
    ResearchResponse,
    SearchResponse,
    TaskScope,
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
        self._task_contexts: dict[str, list[MemoryResult]] = {}
        self._task_scopes: dict[str, TaskScope] = {}
        self._task_gaps: dict[str, list[KnowledgeGapItem]] = {}

    # ─────────────────────────────────────────────────────────────────────
    # search()
    # ─────────────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        task_id: str | None = None,
        context: str | None = None,
        filters: dict[str, Any] | None = None,
        task_scope: TaskScope | None = None,
    ) -> SearchResponse:
        """
        Search Obsidian for knowledge relevant to *query*.

        Returns a SearchResponse with found=True/False, taskScope, and knowledgeGaps.
        """
        log_extra = {"task_id": task_id, "query": query[:100]}
        logger.info("memory.search.started", extra=log_extra)

        if not task_scope:
            task_scope = TaskAnalyzer.analyze(query, context)

        try:
            raw_results = await self._obsidian.search(query, filters, task_scope=task_scope)
        except ObsidianAdapterError as exc:
            logger.error(
                "memory.search.adapter_error",
                extra={**log_extra, "error": str(exc)},
            )
            raise MemoryAgentError(f"Obsidian unavailable: {exc}") from exc

        assembled = self._retrieval.assemble_context(raw_results, task_id)
        gaps = self._retrieval.assess_knowledge_gaps(assembled, task_scope)
        found = self._retrieval.has_sufficient_knowledge(assembled, gaps)

        # Cache the context and metadata for this task
        if task_id:
            if task_id not in self._task_contexts:
                self._task_contexts[task_id] = []
            if assembled:
                self._task_contexts[task_id].extend(assembled)
            self._task_scopes[task_id] = task_scope
            self._task_gaps[task_id] = gaps

        debug_info: dict[str, Any] = {
            "raw_count": len(raw_results),
            "assembled_count": len(assembled),
            "domain": task_scope.domain,
            "entity": task_scope.entity,
            "platform": task_scope.platform,
            "task_type": task_scope.task_type,
            "missing_gaps": sum(1 for g in gaps if g.status == "missing"),
            "satisfied_gaps": sum(1 for g in gaps if g.status == "satisfied"),
        }

        rejected_candidates = getattr(self._obsidian, "last_rejected_candidates", [])
        vault_scan_stats = getattr(self._obsidian, "last_scan_stats", None)

        logger.info(
            "memory.search.completed",
            extra={**log_extra, "result_count": len(assembled), "found": found},
        )
        return SearchResponse(
            results=assembled,
            found=found,
            count=len(assembled),
            task_scope=task_scope,
            knowledge_gaps=gaps,
            rejected_candidates=rejected_candidates,
            vault_scan_stats=vault_scan_stats,
            debug_info=debug_info,
        )

    # ─────────────────────────────────────────────────────────────────────
    # retrieve_context()
    # ─────────────────────────────────────────────────────────────────────

    async def retrieve_context(self, task_id: str) -> ContextResponse:
        """
        Return all cached memory context for a task.
        """
        results = self._task_contexts.get(task_id, [])
        sources = self._retrieval.collect_sources(results)
        task_scope = self._task_scopes.get(task_id)
        knowledge_gaps = self._task_gaps.get(task_id, [])
        return ContextResponse(
            task_id=task_id,
            context=results,
            sources=sources,
            timestamp=datetime.now(timezone.utc),
            task_scope=task_scope,
            knowledge_gaps=knowledge_gaps,
        )

    # ─────────────────────────────────────────────────────────────────────
    # research()
    # ─────────────────────────────────────────────────────────────────────

    async def research(
        self,
        query: str,
        task_id: str | None = None,
        task_scope: TaskScope | None = None,
    ) -> ResearchResponse:
        """
        Perform controlled external research.
        """
        if not task_scope:
            task_scope = TaskAnalyzer.analyze(query)

        try:
            evidence = await self._research_svc.research(query, task_id)
        except ResearchError:
            raise
        except Exception as exc:
            raise MemoryAgentError(f"Research pipeline error: {exc}") from exc

        sources = self._research_svc.collect_source_urls(evidence)
        return ResearchResponse(
            evidence=evidence,
            sources=sources,
            count=len(evidence),
            task_scope=task_scope,
        )

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

    def _determine_target_note(self, query: str, task_scope: TaskScope | None) -> str:
        """Auto-route note to proper Obsidian folder based on task domain/type."""
        if task_scope:
            if task_scope.domain == "e-commerce":
                return "domains/ecommerce/architecture-guidelines"
            elif task_scope.domain == "social_media_advertising" or task_scope.platform == "Instagram":
                return "marketing/social-media/instagram-ad-specs"
            elif task_scope.domain == "healthcare":
                return "domains/healthcare/compliance-architecture"
            elif task_scope.domain == "quantum_computing":
                # Route to AI-Knowledge-Base, NOT research/ (which is raw-scrape blocked)
                return "AI-Knowledge-Base/quantum-computing-fundamentals"
            elif task_scope.domain == "fintech":
                return "domains/fintech/payment-architecture"

        slug = "".join(c if c.isalnum() else "-" for c in query.lower()[:40]).strip("-")
        return f"research/{slug}"

    async def search_or_research(
        self,
        query: str,
        task_id: str | None = None,
        target_note: str | None = None,
    ) -> SearchResponse:
        """
        Full automated pipeline:
          1. Search Obsidian.
          2. If found and no critical missing gaps -> return retrieved results.
          3. If not found or missing gaps exist -> research via Jina -> validate -> write approved -> re-search Obsidian.
        """
        task_scope = TaskAnalyzer.analyze(query)

        # Step 1: Search Obsidian
        search_resp = await self.search(query, task_id=task_id, task_scope=task_scope)
        has_missing = any(g.status == "missing" for g in search_resp.knowledge_gaps)
        if search_resp.found and not has_missing:
            return search_resp

        # Step 2: External research
        try:
            research_resp = await self.research(query, task_id=task_id, task_scope=task_scope)
        except ResearchError as exc:
            raise MemoryAgentError(f"Research failed: {exc}") from exc

        if not research_resp.evidence:
            return search_resp

        # Step 3: Validate
        validation = self.validate(research_resp.evidence, query, task_id=task_id)

        if not validation.approved:
            return search_resp

        # Step 4: Write approved knowledge to Obsidian
        note_path = target_note or self._determine_target_note(query, task_scope)
        domain_heading = (task_scope.domain or query).replace("_", " ").title()
        evidence_blocks = [f"## {item.title or 'Evidence'}\nSource: {item.source}\n\n{item.content}" for item in research_resp.evidence]
        content_to_write = f"# {domain_heading}\n\n" + "\n\n".join(evidence_blocks)

        write_resp = await self.write(
            content=content_to_write,
            evidence_refs=research_resp.evidence,
            approval_status=ApprovalStatus.APPROVED,
            target_note=note_path,
            task_id=task_id,
        )

        if write_resp.status == "written":
            # Re-run search against updated Obsidian
            return await self.search(query, task_id=task_id, task_scope=task_scope)

        # If write was rejected because the note already exists (duplicate),
        # the knowledge is already in the vault — re-search to find it.
        reject_reason = (write_resp.metadata or {}).get("reason", "")
        if "already exists" in reject_reason:
            return await self.search(query, task_id=task_id, task_scope=task_scope)

        return search_resp
