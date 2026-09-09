"""
Interfaces and abstract protocols for Software Development Agent and planning systems.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from executive_twins.schemas.evidence import EvidenceSet
from executive_twins.software_development.models import (
    DevelopmentPlan,
    DevelopmentRequest,
    DevelopmentResult,
    DiagnosticResult,
    PlanStep,
)


class IDevelopmentPlanner(ABC):
    """
    Abstract interface for development planning and failure reasoning.
    Designed so that a future reasoning model or deterministic test planner can be attached
    without altering execution, capability, or security layers.
    """

    @abstractmethod
    def create_plan(self, request: DevelopmentRequest) -> DevelopmentPlan:
        """Construct a bounded development plan from request requirements."""
        pass

    @abstractmethod
    def diagnose_failure(
        self,
        request: DevelopmentRequest,
        failed_step: PlanStep,
        failure_evidence: EvidenceSet,
        failure_output: str,
        iteration: int,
    ) -> DiagnosticResult:
        """Diagnose a failure using empirical evidence and generate bounded recovery steps."""
        pass

    @abstractmethod
    def refine_plan(
        self,
        request: DevelopmentRequest,
        plan: DevelopmentPlan,
        diagnostic: DiagnosticResult,
    ) -> DevelopmentPlan:
        """Refine or inject recovery steps into an active plan."""
        pass


class ISoftwareDevelopmentAgent(ABC):
    """
    Controlled Software Development Agent Interface.
    Orchestrates bounded software development workflows using SpecialistExecutionEngine.
    Must enforce path isolation, bounded execution limits, empirical verification, and zero shell escapes.
    """

    @abstractmethod
    def execute_development(self, request: DevelopmentRequest) -> DevelopmentResult:
        """Execute a complete, bounded software development lifecycle."""
        pass

    @abstractmethod
    def validate_request(self, request: DevelopmentRequest) -> Tuple[bool, Optional[str]]:
        """Validate request against security boundaries and limits."""
        pass
