"""
Memory Agent — Canonical Data Models

These are the shared data contracts for the Memory Agent service.
They define the trust hierarchy and information flow:

  retrieved   → directly read from Obsidian (highest internal trust)
  unverified  → raw external research (never auto-promoted)
  validated   → passed evidence rules but not yet written
  approved    → written to Obsidian as trusted company knowledge
  rejected    → failed validation (never stored)
  pending     → validation is in progress
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


# ─────────────────────────────────────────────────────────────────────────────
# Base model: camelCase serialisation for all API-facing models
# ─────────────────────────────────────────────────────────────────────────────


class CamelModel(BaseModel):
    """
    Base model that serialises fields as camelCase in JSON responses.
    Internal Python code uses snake_case; the HTTP API surface uses camelCase.
    Fields can still be set using snake_case in Python (populate_by_name=True).
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
        "use_enum_values": True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Trust Hierarchy
# ─────────────────────────────────────────────────────────────────────────────


class ApprovalStatus(str, Enum):
    """
    Strict trust levels for memory items.

    Order of promotion (one-way only):
      unverified → validated → approved
    External research may NEVER skip directly to 'approved'.
    """

    PENDING = "pending"
    UNVERIFIED = "unverified"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETRIEVED = "retrieved"  # Directly from Obsidian — highest internal trust


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PENDING = "pending"


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceItem(CamelModel):
    """
    A single piece of evidence from external research.

    Source provenance is always preserved — it is never discarded
    after content extraction.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field(..., description="Source identifier (URL, DOI, file path, etc.)")
    title: str | None = Field(None, description="Title of the source document/page")
    content: str = Field(..., description="Extracted content from the source")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of retrieval",
    )
    relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance score 0.0–1.0",
    )
    validation_status: ValidationStatus = Field(
        default=ValidationStatus.PENDING,
        description="Validation result for this individual evidence item",
    )
    approval_status: ApprovalStatus = Field(
        default=ApprovalStatus.UNVERIFIED,
        description="Trust level — always starts as unverified",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Memory Result
# ─────────────────────────────────────────────────────────────────────────────


class MemoryResult(CamelModel):
    """
    A unit of memory — may be Obsidian-retrieved or research-derived.

    approval_status determines whether this can be trusted as company knowledge.
    source_note identifies the Obsidian note this came from (if applicable).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str = Field(..., description="The query that produced this result")
    content: str = Field(..., description="Retrieved or researched content")
    sources: list[str] = Field(
        default_factory=list,
        description="Source references (Obsidian note IDs, URLs, etc.)",
    )
    evidence_refs: list[EvidenceItem] = Field(
        default_factory=list,
        description="Evidence items preserved from research (empty for Obsidian-retrieved)",
    )
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    target_note: str | None = Field(
        None, description="Obsidian note ID/path that this was written to (post-approval)"
    )
    task_id: str | None = Field(
        None, description="Correlation ID linking this result to an orchestrator task"
    )
    source_note: str | None = Field(
        None, description="Obsidian note path this was retrieved from"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Validation Result
# ─────────────────────────────────────────────────────────────────────────────


class ValidationResult(CamelModel):
    """
    Output of the validation pipeline.

    A model saying "I believe this is correct" is NOT sufficient for approval.
    This object is produced by deterministic rule evaluation.
    """

    status: ApprovalStatus
    reason: str = Field(..., description="Human-readable explanation of the decision")
    approved: bool
    assessment: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed breakdown of each validation rule and its result",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Memory Write Audit Record
# ─────────────────────────────────────────────────────────────────────────────


class MemoryWriteAudit(CamelModel):
    """Immutable audit record created on every write attempt."""

    note_id: str | None = None
    target_note: str
    task_id: str | None = None
    approval_status: ApprovalStatus
    written_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_count: int = 0
    sources: list[str] = Field(default_factory=list)
    write_status: str  # "written" | "rejected"
    rejection_reason: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# API Request / Response Models
# ─────────────────────────────────────────────────────────────────────────────


class SearchRequest(CamelModel):
    """POST /api/v1/memory/search"""

    query: str = Field(..., min_length=1, description="Search query")
    task_id: str | None = Field(None, description="Optional task correlation ID")
    context: str | None = Field(None, description="Additional context for the search")
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Optional metadata filters"
    )


class SearchResponse(CamelModel):
    """Response for POST /api/v1/memory/search"""

    results: list[MemoryResult]
    found: bool
    count: int


class ResearchRequest(CamelModel):
    """POST /api/v1/memory/research"""

    query: str = Field(..., min_length=1)
    task_id: str | None = Field(None, description="Optional task correlation ID")


class ResearchResponse(CamelModel):
    """Response for POST /api/v1/memory/research"""

    evidence: list[EvidenceItem]
    sources: list[str]
    count: int


class ValidateRequest(CamelModel):
    """POST /api/v1/memory/validate"""

    evidence: list[EvidenceItem]
    query: str = Field(..., min_length=1)
    context: str | None = None


class ValidateResponse(CamelModel):
    """Response for POST /api/v1/memory/validate"""

    status: ApprovalStatus
    reason: str
    approved: bool
    assessment: dict[str, Any]


class WriteRequest(CamelModel):
    """POST /api/v1/memory/write"""

    content: str = Field(..., min_length=1)
    evidence_refs: list[EvidenceItem] = Field(default_factory=list)
    approval_status: ApprovalStatus = Field(...)
    target_note: str = Field(..., min_length=1)
    task_id: str | None = None


class WriteResponse(CamelModel):
    """Response for POST /api/v1/memory/write"""

    note_id: str | None = None
    status: str  # "written" | "rejected"
    timestamp: datetime
    metadata: dict[str, Any]


class ContextResponse(CamelModel):
    """Response for GET /api/v1/memory/context/{taskId}"""

    task_id: str
    context: list[MemoryResult]
    sources: list[str]
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Error Model
# ─────────────────────────────────────────────────────────────────────────────


class ErrorResponse(CamelModel):
    """Structured error body returned by all error responses."""

    error: str
    detail: str
    task_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
