"""
Abstract interfaces for Coding / Reasoning Model Integration.
Decouples core orchestration logic from specific model providers and inference engines.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from executive_twins.reasoning.models import (
    ReasoningConfig,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
)
from executive_twins.schemas.evidence import EvidenceSet
from executive_twins.software_development.models import DevelopmentPlan


class IReasoningModel(ABC):
    """
    Provider-agnostic interface for executing reasoning requests.
    Implementations may be local inference engines, development test adapters, or hosted model connectors.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name or identification of the reasoning provider."""
        pass

    @abstractmethod
    def generate_reasoning(
        self,
        request: ReasoningRequest,
        system_prompt: str,
        user_prompt: str,
    ) -> ReasoningResponse:
        """
        Execute reasoning on structured prompt inputs and return a structured response.
        Must NOT perform system calls, shell executions, or network tool execution.
        """
        pass


class IReasoningValidator(ABC):
    """
    Interface for multi-stage validation of reasoning requests and responses.
    """

    @abstractmethod
    def validate_request(
        self, request: ReasoningRequest, config: ReasoningConfig
    ) -> Tuple[bool, Optional[str]]:
        """Validate input reasoning request against limits, security rules, and schemas."""
        pass

    @abstractmethod
    def validate_response(
        self,
        response: ReasoningResponse,
        request: ReasoningRequest,
        config: ReasoningConfig,
    ) -> Tuple[bool, Optional[str]]:
        """Validate returned response against safety rules, capability availability, and schemas."""
        pass


class IReasoningService(ABC):
    """
    Authoritative service interface for reasoning orchestration.
    """

    @abstractmethod
    def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Primary entry point for structured reasoning, planning, and goal decomposition.
        """
        pass

    @abstractmethod
    def replan_from_failure(
        self,
        request: ReasoningRequest,
        failure_evidence: EvidenceSet,
        failure_reason: str,
        current_iteration: int = 1,
    ) -> ReasoningResponse:
        """
        Evidence-driven re-planning when an execution step fails.
        """
        pass


class IPlanTranslator(ABC):
    """
    Interface for translating declarative ReasoningPlans to specialist domain plans.
    """

    @abstractmethod
    def translate_to_development_plan(
        self, plan: ReasoningPlan, request_id: str
    ) -> DevelopmentPlan:
        """
        Convert a ReasoningPlan into a strongly typed Software DevelopmentPlan.
        """
        pass
