from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from executive_twins.schemas.common import VerificationStatus
from executive_twins.schemas.twin import ExecutiveRecommendation


class IMasterOrchestratorAdapter(ABC):
    """
    Interface for integrating the Executive Twin layer into the platform Master Orchestrator workflow.
    Executive Twin is a bounded component inside the overall Autonomous AI Workforce lifecycle.
    """

    @abstractmethod
    def route_executive_request(
        self, request_text: str, context: Optional[Dict[str, Any]] = None
    ) -> ExecutiveRecommendation:
        """Route user request through Executive Twin layer when strategic reasoning is required."""
        pass

    @abstractmethod
    def notify_verification(self, recommendation_id: str, status: VerificationStatus) -> None:
        """Notify platform lifecycle of recommendation verification status."""
        pass


class MockMasterOrchestratorAdapter(IMasterOrchestratorAdapter):
    """DEV_TEST_ONLY_ADAPTER: Mock Master Orchestrator adapter for testing."""

    def __init__(self, orchestrator_instance: Any) -> None:
        self.orchestrator = orchestrator_instance
        self.verification_notifications: Dict[str, VerificationStatus] = {}

    def route_executive_request(
        self, request_text: str, context: Optional[Dict[str, Any]] = None
    ) -> ExecutiveRecommendation:
        return self.orchestrator.process_request(request_text, context)

    def notify_verification(self, recommendation_id: str, status: VerificationStatus) -> None:
        self.verification_notifications[recommendation_id] = status
