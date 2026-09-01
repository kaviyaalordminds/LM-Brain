"""
Memory Agent — Validation Layer

Determines whether external research evidence can be promoted to
trusted company knowledge.

IMPORTANT RULES:
1. A model saying "I believe this is correct" is NOT sufficient approval.
2. Validation uses deterministic, auditable rules — not model self-assessment.
3. This layer returns ValidationResult — it does NOT write anything.
4. Only the MemoryWriter performs the actual write, after receiving APPROVED status.

Validation rules evaluated:
  R1  — At least one evidence item present
  R2  — Minimum source count threshold
  R3  — Source diversity (multiple distinct domains)
  R4  — Minimum content length (no trivially empty results)
  R5  — No obviously conflicting evidence detected
  R6  — Minimum average relevance score
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from app.models.memory import ApprovalStatus, EvidenceItem, ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configurable Thresholds
# ─────────────────────────────────────────────────────────────────────────────

_MIN_EVIDENCE_COUNT: int = 1
_MIN_SOURCE_COUNT: int = 1
_MIN_DISTINCT_DOMAINS: int = 1
_MIN_CONTENT_LENGTH: int = 50          # characters per evidence item
_MIN_AVERAGE_RELEVANCE: float = 0.0    # 0.0 = accept any relevance for MVP
_CONFLICT_KEYWORDS: set[str] = {
    "contradicts", "disproves", "false", "incorrect", "invalid",
    "refuted", "debunked",
}


def _extract_domain(url: str) -> str:
    """Return the netloc (domain) of a URL, or the raw value if not a URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc or url
    except Exception:
        return url


class ValidationLayer:
    """
    Deterministic rule-based evidence validator.

    Evaluates a set of EvidenceItems and returns a ValidationResult
    with a clear approval decision and per-rule breakdown.
    """

    def validate(
        self,
        evidence: list[EvidenceItem],
        query: str,
        context: str | None = None,
        task_id: str | None = None,
    ) -> ValidationResult:
        """
        Validate a list of evidence items for a given query.

        Returns a ValidationResult with:
          - status: APPROVED or REJECTED
          - approved: True/False
          - reason: human-readable explanation
          - assessment: per-rule breakdown dict
        """
        log_extra = {"task_id": task_id, "evidence_count": len(evidence)}
        logger.info("memory.validation.started", extra=log_extra)

        assessment: dict[str, object] = {}
        failures: list[str] = []

        # ── R1: Evidence must exist ──────────────────────────────────────
        r1_pass = len(evidence) >= _MIN_EVIDENCE_COUNT
        assessment["R1_evidence_present"] = {
            "passed": r1_pass,
            "expected_min": _MIN_EVIDENCE_COUNT,
            "actual": len(evidence),
        }
        if not r1_pass:
            failures.append("R1: No evidence items provided.")

        # ── R2: Source count ────────────────────────────────────────────
        source_count = len({item.source for item in evidence})
        r2_pass = source_count >= _MIN_SOURCE_COUNT
        assessment["R2_source_count"] = {
            "passed": r2_pass,
            "expected_min": _MIN_SOURCE_COUNT,
            "actual": source_count,
        }
        if not r2_pass:
            failures.append(f"R2: Insufficient sources (found {source_count}, need {_MIN_SOURCE_COUNT}).")

        # ── R3: Domain diversity ────────────────────────────────────────
        domains = {_extract_domain(item.source) for item in evidence}
        r3_pass = len(domains) >= _MIN_DISTINCT_DOMAINS
        assessment["R3_domain_diversity"] = {
            "passed": r3_pass,
            "expected_min": _MIN_DISTINCT_DOMAINS,
            "actual": len(domains),
            "domains": list(domains),
        }
        if not r3_pass:
            failures.append(
                f"R3: Insufficient domain diversity (found {len(domains)}, need {_MIN_DISTINCT_DOMAINS})."
            )

        # ── R4: Content length ──────────────────────────────────────────
        short_items = [
            item.source for item in evidence
            if len(item.content.strip()) < _MIN_CONTENT_LENGTH
        ]
        r4_pass = len(short_items) == 0
        assessment["R4_content_length"] = {
            "passed": r4_pass,
            "min_length": _MIN_CONTENT_LENGTH,
            "short_sources": short_items,
        }
        if not r4_pass:
            failures.append(
                f"R4: {len(short_items)} evidence item(s) have content below "
                f"minimum length ({_MIN_CONTENT_LENGTH} chars)."
            )

        # ── R5: Conflict detection ──────────────────────────────────────
        conflict_sources: list[str] = []
        for item in evidence:
            content_lower = item.content.lower()
            if any(kw in content_lower for kw in _CONFLICT_KEYWORDS):
                conflict_sources.append(item.source)
        r5_pass = len(conflict_sources) == 0
        assessment["R5_no_conflicts"] = {
            "passed": r5_pass,
            "conflict_sources": conflict_sources,
        }
        if not r5_pass:
            failures.append(
                f"R5: Potential conflicting content detected in {len(conflict_sources)} source(s)."
            )

        # ── R6: Minimum average relevance ───────────────────────────────
        avg_relevance = (
            sum(item.relevance for item in evidence) / len(evidence) if evidence else 0.0
        )
        r6_pass = avg_relevance >= _MIN_AVERAGE_RELEVANCE
        assessment["R6_relevance"] = {
            "passed": r6_pass,
            "expected_min": _MIN_AVERAGE_RELEVANCE,
            "actual": round(avg_relevance, 4),
        }
        if not r6_pass:
            failures.append(
                f"R6: Average relevance {avg_relevance:.4f} below threshold "
                f"{_MIN_AVERAGE_RELEVANCE}."
            )

        # ── Decision ─────────────────────────────────────────────────────
        approved = len(failures) == 0
        status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        reason = (
            "All validation rules passed. Evidence is approved for memory write."
            if approved
            else "Validation failed: " + " | ".join(failures)
        )

        # Mark individual evidence items
        for item in evidence:
            item.validation_status = (
                ValidationStatus.PASSED if approved else ValidationStatus.FAILED
            )
            item.approval_status = (
                ApprovalStatus.VALIDATED if approved else ApprovalStatus.REJECTED
            )

        result = ValidationResult(
            status=status,
            reason=reason,
            approved=approved,
            assessment=assessment,
        )

        logger.info(
            "memory.validation.completed",
            extra={
                **log_extra,
                "approved": approved,
                "reason": reason,
                "failure_count": len(failures),
            },
        )
        return result
