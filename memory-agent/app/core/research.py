"""
Memory Agent — Research Service

Drives the controlled external research pipeline.

Responsibilities:
- Query the ResearchProvider
- Collect and return EvidenceItems
- Tag ALL results as UNVERIFIED — they are NEVER auto-promoted
- Handle provider errors and timeouts with structured exceptions

This service does NOT perform validation.
Validation is a separate layer (ValidationLayer).
"""

from __future__ import annotations

import logging

from app.adapters.research_provider import (
    InvalidResearchResultError,
    ResearchProvider,
    ResearchProviderError,
    ResearchTimeoutError,
)
from app.models.memory import ApprovalStatus, EvidenceItem

logger = logging.getLogger(__name__)


class ResearchError(Exception):
    """Raised when the research pipeline fails."""


class ResearchService:
    """
    Manages controlled external research.

    All results are returned with approval_status=UNVERIFIED.
    The caller is responsible for routing them through validation.
    """

    def __init__(self, provider: ResearchProvider) -> None:
        self._provider = provider

    async def research(
        self,
        query: str,
        task_id: str | None = None,
    ) -> list[EvidenceItem]:
        """
        Perform external research for *query*.

        Returns a list of EvidenceItems, ALL marked UNVERIFIED.
        Raises ResearchError wrapping the underlying provider exception.
        """
        log_extra = {"task_id": task_id, "query": query[:100]}
        logger.info("memory.research.started", extra=log_extra)

        try:
            items = await self._provider.search(query)
        except ResearchTimeoutError as exc:
            logger.warning(
                "memory.research.timeout",
                extra={**log_extra, "error": str(exc)},
            )
            raise ResearchError(f"Research timed out: {exc}") from exc
        except ResearchProviderError as exc:
            logger.error(
                "memory.research.provider_error",
                extra={**log_extra, "error": str(exc)},
            )
            raise ResearchError(f"Research provider unavailable: {exc}") from exc
        except InvalidResearchResultError as exc:
            logger.error(
                "memory.research.invalid_result",
                extra={**log_extra, "error": str(exc)},
            )
            raise ResearchError(f"Invalid research result: {exc}") from exc
        except Exception as exc:
            logger.exception("memory.research.unexpected_error", extra=log_extra)
            raise ResearchError(f"Unexpected research error: {exc}") from exc

        # Enforce: all items must be UNVERIFIED
        for item in items:
            item.approval_status = ApprovalStatus.UNVERIFIED
            if task_id:
                # Store task_id in source for traceability
                pass  # EvidenceItem doesn't carry task_id; logged at service level

        logger.info(
            "memory.research.completed",
            extra={**log_extra, "evidence_count": len(items)},
        )
        return items

    def collect_source_urls(self, items: list[EvidenceItem]) -> list[str]:
        """Extract unique source URLs from a list of evidence items."""
        seen: set[str] = set()
        sources: list[str] = []
        for item in items:
            if item.source not in seen:
                seen.add(item.source)
                sources.append(item.source)
        return sources
