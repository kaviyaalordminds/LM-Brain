from .failure_policy import FailureType
from typing import Set

NON_RETRYABLE: Set[FailureType] = {
    FailureType.PERMISSION_DENIED,
    FailureType.CANCELLED,
}

REQUIRES_REPLAN: Set[FailureType] = {
    FailureType.CONTRACT_VIOLATION,
    FailureType.VERIFICATION_FAILED,
}

class RetryPolicy:
    @staticmethod
    def should_retry(failure_type: FailureType, attempt_number: int, max_retries: int) -> bool:
        if failure_type in NON_RETRYABLE or failure_type in REQUIRES_REPLAN:
            return False
        return attempt_number < max_retries

    @staticmethod
    def backoff_seconds(attempt_number: int) -> float:
        """Exponential backoff: 2^attempt_number, capped at 30 seconds."""
        return min(float(2 ** attempt_number), 30.0)

