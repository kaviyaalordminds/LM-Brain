import random
from typing import Set, Tuple
from .failure_policy import FailureType

NON_RETRYABLE: Set[FailureType] = {
    FailureType.PERMISSION_DENIED,
    FailureType.CANCELLED,
}

REQUIRES_REPLAN: Set[FailureType] = {
    FailureType.CONTRACT_VIOLATION,
    FailureType.DEPENDENCY_FAILED,
}

# Maximum allowed retries per specific failure type to prevent infinite retry loops
FAILURE_TYPE_MAX_RETRIES = {
    FailureType.MODEL_UNAVAILABLE: 2,  # Bounded attempt for model availability
    FailureType.TIMEOUT: 3,
    FailureType.SERVICE_UNAVAILABLE: 3,
    FailureType.VERIFICATION_FAILED: 2,
    FailureType.RESOURCE_EXHAUSTED: 2,
}

class RetryPolicy:
    """
    Deterministic, bounded, and observable retry policy.
    Computes exponential backoff with optional jitter.
    """

    @staticmethod
    def evaluate(
        failure_type: FailureType,
        attempt_number: int,
        max_retries: int = 3
    ) -> Tuple[bool, float, str]:
        """
        Evaluate whether a failed step should retry.
        Returns:
            (should_retry, backoff_seconds, reason)
        """
        if failure_type in NON_RETRYABLE:
            return False, 0.0, f"Failure type {failure_type.value} is strictly non-retryable"

        if failure_type in REQUIRES_REPLAN:
            return False, 0.0, f"Failure type {failure_type.value} requires workflow replanning, not simple retry"

        type_limit = FAILURE_TYPE_MAX_RETRIES.get(failure_type, max_retries)
        effective_max = min(max_retries, type_limit)

        if attempt_number >= effective_max:
            return False, 0.0, f"Retry budget exhausted ({attempt_number}/{effective_max} attempts) for {failure_type.value}"

        backoff = RetryPolicy.backoff_seconds(attempt_number)
        return True, backoff, f"Scheduled retry {attempt_number + 1}/{effective_max} after {backoff:.1f}s backoff"

    @staticmethod
    def should_retry(failure_type: FailureType, attempt_number: int, max_retries: int = 3) -> bool:
        should, _, _ = RetryPolicy.evaluate(failure_type, attempt_number, max_retries)
        return should

    @staticmethod
    def backoff_seconds(attempt_number: int, base: float = 1.5, max_backoff: float = 30.0) -> float:
        """Exponential backoff: base^attempt, capped at max_backoff with slight jitter."""
        calculated = min(float(base ** attempt_number), max_backoff)
        jitter = random.uniform(0.0, 0.2)
        return round(calculated + jitter, 2)


