"""
Memory Agent — Retrieval Service

Responsible for assembling coherent task context from raw Obsidian search
results. Does NOT perform the search itself — that is the adapter's job.

Responsibilities:
- Rank results by relevance
- Deduplicate by source note
- Assess knowledge gaps against task requirements with core domain term gating
- Preserve source metadata and approval status
- Return structured list and gap analysis
"""

from __future__ import annotations

import logging
import re

from app.models.memory import ApprovalStatus, KnowledgeGapItem, MemoryResult, TaskScope

logger = logging.getLogger(__name__)

# Minimum relevance score to include a result in context
_MIN_RELEVANCE: float = 0.15

# Maximum results to return in a single context assembly
_MAX_RESULTS: int = 20

_STOPWORDS = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "what", "which", "who", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "have", "has", "had", "do", "does", "did",
    "a", "an", "the", "and", "but", "if", "or", "because", "as", "of", "at",
    "by", "for", "with", "about", "to", "from", "in", "out", "on", "off",
    "over", "under", "then", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "can", "will", "just", "should", "now", "want", "need", "build", "create",
    "make", "implement", "application", "system", "platform", "solution", "project",
    "instructions", "guide", "details", "information", "overview"
}

_GENERIC_REQ_TOKENS = {
    "operations", "design", "architecture", "standards", "patterns", "practices",
    "guidelines", "workflow", "management", "system", "structure", "principles",
    "specs", "specifications", "case", "study", "studies", "overview", "rules",
    "integration", "format", "formats", "dimensions", "duration", "strategy"
}


class RetrievalService:
    """
    Assembles, ranks, and assesses Obsidian search results into coherent task context.
    """

    def assemble_context(
        self,
        results: list[MemoryResult],
        task_id: str | None = None,
    ) -> list[MemoryResult]:
        """
        Given raw search results, return a ranked, deduplicated context list.
        """
        if not results:
            logger.debug(
                "retrieval.assemble_context: no results to assemble",
                extra={"task_id": task_id},
            )
            return []

        # Filter by minimum relevance
        filtered = [r for r in results if r.relevance >= _MIN_RELEVANCE]

        # Stable deduplication: preserve intent-aware ordering produced by adapter
        seen_notes: set[str] = set()
        deduped: list[MemoryResult] = []
        for result in filtered:
            key = result.source_note or result.id
            if key not in seen_notes:
                seen_notes.add(key)
                deduped.append(result)

        # Stamp task_id if provided
        if task_id:
            for result in deduped:
                result.task_id = task_id

        return deduped[:_MAX_RESULTS]

    def assess_knowledge_gaps(
        self,
        results: list[MemoryResult],
        task_scope: TaskScope | None,
    ) -> list[KnowledgeGapItem]:
        """
        Evaluate each requirement in task_scope against assembled results.
        Enforces that core domain tokens must match for a requirement to be satisfied.
        """
        if not task_scope or not task_scope.requirements:
            return []

        gaps: list[KnowledgeGapItem] = []
        for req in task_scope.requirements:
            req_clean = req.lower()
            tokens = re.findall(r"[a-zA-Z0-9]+", req_clean)
            req_tokens = [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]
            if not req_tokens:
                req_tokens = [t for t in tokens if len(t) > 1]

            core_domain_tokens = [t for t in req_tokens if t not in _GENERIC_REQ_TOKENS]

            matched_note: str | None = None
            best_rel = 0.0

            for res in results:
                content_lower = (res.content or "").lower()
                source_lower = (res.source_note or "").lower()
                doc_text = f"{source_lower} {content_lower}"

                # Enforce core domain term match
                if core_domain_tokens:
                    core_matched = sum(1 for ct in core_domain_tokens if ct in doc_text)
                    if core_matched == 0:
                        continue

                matches = sum(1 for t in req_tokens if t in doc_text)
                rel = matches / max(len(req_tokens), 1)

                if rel > best_rel:
                    best_rel = rel
                    matched_note = res.source_note or (res.sources[0] if res.sources else None)

            if best_rel >= 0.40:
                gaps.append(
                    KnowledgeGapItem(
                        requirement=req,
                        status="satisfied",
                        matched_note=matched_note,
                        relevance=round(best_rel, 2),
                        reason=f"Satisfied by vault note '{matched_note}' (match confidence: {int(best_rel * 100)}%)",
                    )
                )
            elif best_rel >= 0.20:
                gaps.append(
                    KnowledgeGapItem(
                        requirement=req,
                        status="partial",
                        matched_note=matched_note,
                        relevance=round(best_rel, 2),
                        reason=f"Partially mentioned in '{matched_note}', but lacks dedicated in-depth coverage",
                    )
                )
            else:
                gaps.append(
                    KnowledgeGapItem(
                        requirement=req,
                        status="missing",
                        matched_note=None,
                        relevance=0.0,
                        reason="No relevant knowledge found in Obsidian vault for this requirement",
                    )
                )

        return gaps

    def collect_sources(self, results: list[MemoryResult]) -> list[str]:
        """Extract unique source references from a list of results."""
        seen: set[str] = set()
        sources: list[str] = []
        for result in results:
            for src in result.sources:
                if src not in seen:
                    seen.add(src)
                    sources.append(src)
        return sources

    def has_sufficient_knowledge(
        self,
        results: list[MemoryResult],
        knowledge_gaps: list[KnowledgeGapItem] | None = None,
    ) -> bool:
        """
        Return True if results contain trusted knowledge and adequate domain coverage.
        """
        if not results:
            return False

        trusted_statuses = {ApprovalStatus.RETRIEVED, ApprovalStatus.APPROVED}
        trusted_results = [
            r for r in results
            if r.approval_status in trusted_statuses and len(r.content.strip()) > 10 and r.relevance >= _MIN_RELEVANCE
        ]
        if not trusted_results:
            return False

        if knowledge_gaps:
            satisfied = sum(1 for g in knowledge_gaps if g.status == "satisfied")
            partial = sum(1 for g in knowledge_gaps if g.status == "partial")
            missing = sum(1 for g in knowledge_gaps if g.status == "missing")

            # If requirements are tracked and none are satisfied or partial, knowledge is insufficient
            if missing > 0 and satisfied == 0 and partial == 0:
                # Unless there is an exact note match with high confidence
                if not any(r.relevance >= 0.60 for r in trusted_results):
                    return False

        return True
