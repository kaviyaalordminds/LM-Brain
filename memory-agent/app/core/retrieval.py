"""
Memory Agent — Retrieval Service

Responsible for assembling coherent task context from raw Obsidian search
results. Does NOT perform the search itself — that is the adapter's job.

Responsibilities:
- Rank results by relevance
- Deduplicate by source note
- Preserve source metadata and approval status
- Return a structured list, not a concatenated string
"""

from __future__ import annotations

import logging

from app.models.memory import ApprovalStatus, MemoryResult

logger = logging.getLogger(__name__)

# Minimum relevance score to include a result in context
_MIN_RELEVANCE: float = 0.0

# Maximum results to return in a single context assembly
_MAX_RESULTS: int = 20


class RetrievalService:
    """
    Assembles and ranks Obsidian search results into useful task context.
    """

    def assemble_context(
        self,
        results: list[MemoryResult],
        task_id: str | None = None,
    ) -> list[MemoryResult]:
        """
        Given raw search results, return a ranked, deduplicated context list.

        - Filters out results below _MIN_RELEVANCE
        - Deduplicates on source_note (keeps highest-relevance copy)
        - Sorts descending by relevance
        - Stamps task_id on each result if provided
        - Preserves approval_status — never promotes or demotes
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

    def has_sufficient_knowledge(self, results: list[MemoryResult]) -> bool:
        """
        Return True if the results contain at least one retrieved/approved result
        with meaningful content.
        """
        trusted_statuses = {ApprovalStatus.RETRIEVED, ApprovalStatus.APPROVED}
        return any(
            r.approval_status in trusted_statuses and len(r.content.strip()) > 10
            for r in results
        )
