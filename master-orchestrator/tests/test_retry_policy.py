"""
Tests for RetryPolicy — retryable vs non-retryable, backoff calculation, replan detection.
"""
from __future__ import annotations

import pytest

from app.policies.failure_policy import FailureType
from app.policies.retry_policy import NON_RETRYABLE, REQUIRES_REPLAN, RetryPolicy


class TestRetryability:
    def test_timeout_is_retryable(self):
        assert RetryPolicy.should_retry(FailureType.TIMEOUT, attempt_number=0, max_retries=3) is True

    def test_service_unavailable_is_retryable(self):
        assert RetryPolicy.should_retry(FailureType.SERVICE_UNAVAILABLE, attempt_number=1, max_retries=3) is True

    def test_model_unavailable_is_retryable(self):
        assert RetryPolicy.should_retry(FailureType.MODEL_UNAVAILABLE, attempt_number=0, max_retries=2) is True

    def test_unknown_is_retryable_within_budget(self):
        assert RetryPolicy.should_retry(FailureType.UNKNOWN, attempt_number=0, max_retries=2) is True


class TestNonRetryable:
    def test_permission_denied_not_retryable(self):
        assert RetryPolicy.should_retry(FailureType.PERMISSION_DENIED, attempt_number=0, max_retries=10) is False

    def test_cancelled_not_retryable(self):
        assert RetryPolicy.should_retry(FailureType.CANCELLED, attempt_number=0, max_retries=10) is False

    def test_non_retryable_set_contents(self):
        assert FailureType.PERMISSION_DENIED in NON_RETRYABLE
        assert FailureType.CANCELLED in NON_RETRYABLE


class TestRequiresReplan:
    def test_contract_violation_requires_replan(self):
        assert RetryPolicy.should_retry(FailureType.CONTRACT_VIOLATION, attempt_number=0, max_retries=10) is False
        assert FailureType.CONTRACT_VIOLATION in REQUIRES_REPLAN

    def test_verification_failed_requires_replan(self):
        assert RetryPolicy.should_retry(FailureType.VERIFICATION_FAILED, attempt_number=0, max_retries=10) is False
        assert FailureType.VERIFICATION_FAILED in REQUIRES_REPLAN


class TestBudgetExhaustion:
    def test_budget_exhausted_returns_false(self):
        assert RetryPolicy.should_retry(FailureType.TIMEOUT, attempt_number=3, max_retries=3) is False

    def test_budget_at_limit_is_exhausted(self):
        assert RetryPolicy.should_retry(FailureType.SERVICE_UNAVAILABLE, attempt_number=2, max_retries=2) is False

    def test_budget_one_remaining(self):
        assert RetryPolicy.should_retry(FailureType.TIMEOUT, attempt_number=1, max_retries=2) is True


class TestBackoffCalculation:
    def test_attempt_0_backoff_is_1(self):
        assert RetryPolicy.backoff_seconds(0) == 1.0

    def test_attempt_1_backoff_is_2(self):
        assert RetryPolicy.backoff_seconds(1) == 2.0

    def test_attempt_2_backoff_is_4(self):
        assert RetryPolicy.backoff_seconds(2) == 4.0

    def test_attempt_3_backoff_is_8(self):
        assert RetryPolicy.backoff_seconds(3) == 8.0

    def test_backoff_capped_at_30(self):
        # 2^10 = 1024, must be capped at 30
        assert RetryPolicy.backoff_seconds(10) == 30.0

    def test_backoff_returns_float(self):
        assert isinstance(RetryPolicy.backoff_seconds(1), float)
