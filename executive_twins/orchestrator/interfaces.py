"""
Abstract interfaces for Master Orchestrator and Autonomous Control Loop.
Decouples high-level coordination from specialist execution and persistence infrastructure.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from executive_twins.orchestrator.models import (
    OrchestrationConfig,
    OrchestrationRequest,
    OrchestrationResult,
)
from executive_twins.schemas.common import SecurityContext


class IPerceptionEngine(ABC):
    """
    Interface for normalizing, validating, and extracting intent from incoming requests.
    """

    @abstractmethod
    def perceive(
        self, request: OrchestrationRequest
    ) -> Tuple[bool, OrchestrationRequest, Optional[str]]:
        """
        Normalize and validate the incoming request.
        Returns (is_valid, normalized_request, error_message).
        """
        pass


class IMemoryWritebackHandler(ABC):
    """
    Interface for persisting approved workflow states and facts to Company Obsidian.
    """

    @abstractmethod
    def writeback(
        self, result: OrchestrationResult, security_context: SecurityContext
    ) -> Tuple[bool, Optional[str]]:
        """
        Persist approved execution results to Company Knowledge Layer.
        Returns (success, message).
        """
        pass


class IControlLoop(ABC):
    """
    Interface for executing the bounded autonomous control loop.
    """

    @abstractmethod
    def run(
        self, request: OrchestrationRequest, config: OrchestrationConfig
    ) -> OrchestrationResult:
        """
        Execute the Perception -> Planning -> Capability Selection -> Execution -> QA -> Recovery loop.
        """
        pass


class IMasterOrchestrator(ABC):
    """
    Primary interface for the Master Orchestrator service.
    """

    @abstractmethod
    def orchestrate(
        self, request: OrchestrationRequest
    ) -> OrchestrationResult:
        """
        Orchestrate an incoming autonomous workforce request end-to-end.
        """
        pass
