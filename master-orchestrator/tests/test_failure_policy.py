"""
Tests for FailurePolicy — all 13 failure types, keyword classifier accuracy, exception handling.
"""
from __future__ import annotations

import pytest

from app.policies.failure_policy import FailureClassifier, FailureType


class TestFailureTypeEnum:
    def test_all_13_types_exist(self):
        expected = {
            "MODEL_UNAVAILABLE", "TOOL_UNAVAILABLE", "TIMEOUT", "VALIDATION_FAILED",
            "VERIFICATION_FAILED", "DEPENDENCY_FAILED", "PERMISSION_DENIED",
            "CONTRACT_VIOLATION", "RESOURCE_EXHAUSTED", "SERVICE_UNAVAILABLE",
            "INVALID_OUTPUT", "CANCELLED", "UNKNOWN",
        }
        actual = {f.value for f in FailureType}
        assert actual == expected


class TestFailureClassifierKeywords:
    def test_timeout_keyword(self):
        assert FailureClassifier.classify("timeout") == FailureType.TIMEOUT

    def test_timed_out_keyword(self):
        assert FailureClassifier.classify("operation timed out") == FailureType.TIMEOUT

    def test_permission_denied_keyword(self):
        assert FailureClassifier.classify("permission denied by policy") == FailureType.PERMISSION_DENIED

    def test_403_maps_to_permission_denied(self):
        assert FailureClassifier.classify("HTTP 403 Forbidden") == FailureType.PERMISSION_DENIED

    def test_cancelled(self):
        assert FailureClassifier.classify("task cancelled by user") == FailureType.CANCELLED

    def test_verification_failed(self):
        assert FailureClassifier.classify("verification failed: verdict FAIL") == FailureType.VERIFICATION_FAILED

    def test_validation_failed(self):
        assert FailureClassifier.classify("validation failed: missing required field") == FailureType.VALIDATION_FAILED

    def test_dependency_failed(self):
        assert FailureClassifier.classify("dependency failed for step-2") == FailureType.DEPENDENCY_FAILED

    def test_contract_violation(self):
        assert FailureClassifier.classify("contract violation: schema mismatch") == FailureType.CONTRACT_VIOLATION

    def test_service_unavailable_503(self):
        assert FailureClassifier.classify("HTTP 503 service unavailable") == FailureType.SERVICE_UNAVAILABLE

    def test_connection_refused(self):
        assert FailureClassifier.classify("connection refused to planner service") == FailureType.SERVICE_UNAVAILABLE

    def test_model_unavailable(self):
        assert FailureClassifier.classify("model unavailable for inference") == FailureType.MODEL_UNAVAILABLE

    def test_resource_exhausted_rate_limit(self):
        assert FailureClassifier.classify("HTTP 429 rate limit exceeded") == FailureType.RESOURCE_EXHAUSTED

    def test_resource_exhausted_quota(self):
        assert FailureClassifier.classify("quota exceeded for token usage") == FailureType.RESOURCE_EXHAUSTED

    def test_invalid_output(self):
        assert FailureClassifier.classify("malformed JSON in specialist output") == FailureType.INVALID_OUTPUT

    def test_unknown_for_unrecognized_error(self):
        assert FailureClassifier.classify("something completely unexpected happened") == FailureType.UNKNOWN

    def test_case_insensitive(self):
        assert FailureClassifier.classify("TIMEOUT ERROR OCCURRED") == FailureType.TIMEOUT

    def test_error_code_takes_precedence(self):
        """error_code appended to message for classification."""
        result = FailureClassifier.classify("generic error", error_code="permission_denied")
        assert result == FailureType.PERMISSION_DENIED

    def test_exception_input_classified(self):
        """Exception objects are coerced to str for classification."""
        exc = TimeoutError("request timed out")
        assert FailureClassifier.classify(exc) == FailureType.TIMEOUT


class TestClassifyException:
    def test_classify_exception_method(self):
        exc = ConnectionRefusedError("connection refused")
        result = FailureClassifier.classify_exception(exc)
        assert result == FailureType.SERVICE_UNAVAILABLE

    def test_classify_exception_timeout(self):
        exc = TimeoutError("deadline exceeded")
        result = FailureClassifier.classify_exception(exc)
        assert result == FailureType.TIMEOUT

    def test_classify_exception_generic(self):
        exc = RuntimeError("some unexpected thing")
        result = FailureClassifier.classify_exception(exc)
        assert result == FailureType.UNKNOWN

