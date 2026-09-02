"""
Master Orchestrator — Failure Policy

Explicit failure type taxonomy and deterministic failure classifier.
Never uses bare except — all failures are classified before retry decisions are made.
"""
from __future__ import annotations

from enum import Enum


class FailureType(str, Enum):
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    CONTRACT_VIOLATION = "CONTRACT_VIOLATION"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


# Keyword → FailureType priority-ordered mapping
_KEYWORD_MAP: list[tuple[list[str], FailureType]] = [
    (["cancelled", "cancel"], FailureType.CANCELLED),
    (["permission denied", "permission_denied", "403", "unauthorized", "forbidden"], FailureType.PERMISSION_DENIED),
    (["contract_violation", "contract violation", "contract"], FailureType.CONTRACT_VIOLATION),
    (["timeout", "timed out", "deadline exceeded"], FailureType.TIMEOUT),
    (["model unavailable", "model_unavailable", "no model"], FailureType.MODEL_UNAVAILABLE),
    (["tool unavailable", "tool_unavailable", "tool not found"], FailureType.TOOL_UNAVAILABLE),
    (["service unavailable", "service_unavailable", "503", "connection refused", "connecterror"], FailureType.SERVICE_UNAVAILABLE),
    (["verification failed", "verification_failed", "verify failed"], FailureType.VERIFICATION_FAILED),
    (["validation failed", "validation_failed", "invalid input"], FailureType.VALIDATION_FAILED),
    (["dependency failed", "dependency_failed"], FailureType.DEPENDENCY_FAILED),
    (["resource exhausted", "resource_exhausted", "429", "rate limit", "quota"], FailureType.RESOURCE_EXHAUSTED),
    (["invalid output", "invalid_output", "malformed", "unexpected output"], FailureType.INVALID_OUTPUT),
]


class FailureClassifier:
    """Deterministic failure classifier. No LLM involved."""

    @staticmethod
    def classify(error: Exception | str, error_code: str = "") -> FailureType:
        """
        Classify an error into an explicit FailureType.

        Priority: error_code keywords > error message keywords > UNKNOWN.
        """
        err_str = str(error) if error is not None else ""
        code_str = str(error_code) if error_code is not None else ""
        combined = (err_str + " " + code_str).lower()

        for keywords, failure_type in _KEYWORD_MAP:
            if any(kw in combined for kw in keywords):
                return failure_type

        return FailureType.UNKNOWN


    @staticmethod
    def classify_exception(exc: Exception) -> FailureType:
        """Classify a Python exception by type name and message."""
        type_name = type(exc).__name__.lower()
        msg = str(exc).lower()
        combined = type_name + " " + msg
        return FailureClassifier.classify(combined)

