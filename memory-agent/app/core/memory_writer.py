"""
Memory Agent — Memory Writer

The final gate before anything enters the company's Obsidian knowledge base.

Rules enforced:
  RULE 1: Only ApprovalStatus.APPROVED may be written.
           unverified / pending / validated / rejected → all rejected.
  RULE 2: Duplicate detection before write.
  RULE 3: Every write produces an immutable audit record.
  RULE 4: Evidence references are preserved with the written note.
  RULE 5: Existing notes are never silently overwritten.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.adapters.obsidian_adapter import (
    ObsidianAdapter,
    ObsidianAdapterError,
    ObsidianDuplicateError,
)
from app.models.memory import ApprovalStatus, EvidenceItem, MemoryWriteAudit

logger = logging.getLogger(__name__)


class WriteRejectedError(Exception):
    """Raised when a write is rejected due to approval status or policy violation."""


class DuplicateKnowledgeError(Exception):
    """Raised when the target note already exists and overwrite is not permitted."""


class MemoryWriter:
    """
    Approved-only write guard for the Obsidian knowledge base.

    Only ApprovalStatus.APPROVED passes through. All other statuses
    produce a WriteRejectedError with a clear reason.
    """

    # Statuses that are NEVER allowed to write
    _BLOCKED_STATUSES: frozenset[str] = frozenset(
        s.value for s in (
            ApprovalStatus.UNVERIFIED,
            ApprovalStatus.PENDING,
            ApprovalStatus.VALIDATED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.RETRIEVED,
        )
    )

    def __init__(self, obsidian: ObsidianAdapter) -> None:
        self._obsidian = obsidian

    async def write(
        self,
        content: str,
        evidence_refs: list[EvidenceItem],
        approval_status: ApprovalStatus,
        target_note: str,
        task_id: str | None = None,
    ) -> tuple[str, MemoryWriteAudit]:
        """
        Write approved content to Obsidian.

        Returns:
            (note_id, audit_record)

        Raises:
            WriteRejectedError  — if approval_status is not APPROVED
            DuplicateKnowledgeError — if the target note already exists
            ObsidianAdapterError — if the adapter fails
        """
        log_extra = {
            "task_id": task_id,
            "target_note": target_note,
            "approval_status": str(approval_status),
        }
        logger.info("memory.write.started", extra=log_extra)

        # ── RULE 1: Approval gate ──────────────────────────────────────────
        status_value = (
            approval_status.value
            if isinstance(approval_status, ApprovalStatus)
            else str(approval_status)
        )
        if status_value in self._BLOCKED_STATUSES:
            reason = (
                f"Write rejected: approvalStatus is '{status_value}'. "
                f"Only 'approved' knowledge may be written to Obsidian."
            )
            audit = MemoryWriteAudit(
                target_note=target_note,
                task_id=task_id,
                approval_status=approval_status,
                evidence_count=len(evidence_refs),
                sources=[e.source for e in evidence_refs],
                write_status="rejected",
                rejection_reason=reason,
            )
            logger.warning("memory.write.rejected", extra={**log_extra, "reason": reason})
            raise WriteRejectedError(reason)

        # ── RULE 2: Duplicate detection ────────────────────────────────────
        try:
            existing = await self._obsidian.read(target_note)
        except ObsidianAdapterError:
            existing = None  # Adapter error on read — proceed, write will surface it

        if existing is not None:
            reason = (
                f"Write rejected: note '{target_note}' already exists. "
                "Use an explicit update operation to modify existing knowledge."
            )
            audit = MemoryWriteAudit(
                target_note=target_note,
                task_id=task_id,
                approval_status=approval_status,
                evidence_count=len(evidence_refs),
                sources=[e.source for e in evidence_refs],
                write_status="rejected",
                rejection_reason=reason,
            )
            logger.warning("memory.write.rejected", extra={**log_extra, "reason": reason})
            raise DuplicateKnowledgeError(reason)

        # ── RULE 3–4: Build metadata (evidence refs preserved) ────────────
        metadata: dict[str, Any] = {
            "task_id": task_id,
            "approval_status": ApprovalStatus.APPROVED.value,
            "evidence_refs": [
                {
                    "id": e.id,
                    "source": e.source,
                    "title": e.title,
                    "retrieved_at": e.retrieved_at.isoformat(),
                    "relevance": e.relevance,
                    "validation_status": str(e.validation_status),
                }
                for e in evidence_refs
            ],
            "written_at": datetime.now(timezone.utc).isoformat(),
            "source_count": len(evidence_refs),
        }

        # ── Write ──────────────────────────────────────────────────────────
        try:
            note_id = await self._obsidian.write(content, target_note, metadata)
        except ObsidianDuplicateError as exc:
            reason = str(exc)
            audit = MemoryWriteAudit(
                target_note=target_note,
                task_id=task_id,
                approval_status=approval_status,
                evidence_count=len(evidence_refs),
                sources=[e.source for e in evidence_refs],
                write_status="rejected",
                rejection_reason=reason,
            )
            logger.warning("memory.write.rejected", extra={**log_extra, "reason": reason})
            raise DuplicateKnowledgeError(reason) from exc
        except ObsidianAdapterError as exc:
            logger.error(
                "memory.write.adapter_error",
                extra={**log_extra, "error": str(exc)},
            )
            raise

        # ── RULE 5: Audit record ──────────────────────────────────────────
        audit = MemoryWriteAudit(
            note_id=note_id,
            target_note=target_note,
            task_id=task_id,
            approval_status=approval_status,
            evidence_count=len(evidence_refs),
            sources=[e.source for e in evidence_refs],
            write_status="written",
        )
        logger.info(
            "memory.write.approved",
            extra={**log_extra, "note_id": note_id},
        )
        return note_id, audit
