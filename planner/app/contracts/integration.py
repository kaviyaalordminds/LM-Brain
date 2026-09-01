"""
Planner Agent — Integration Contracts

Abstract interfaces and contracts for future integration with:
  1. Master Orchestrator (consumes validated Plan objects)
  2. Memory Agent (pre-execution context provider)
  3. Specialist Agent (task execution worker)

The Planner does NOT implement these integrations; it defines the boundaries
so the Master Orchestrator can cleanly orchestrate between components.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.plan import Plan, PlanStep


class OrchestratorPlanConsumer(ABC):
    """
    Interface that the future Master Orchestrator implements to consume Plans.

    Flow:
      User Request → Planner.create_plan() → Plan (READY) → OrchestratorPlanConsumer.execute_plan()
    """

    @abstractmethod
    async def execute_plan(self, plan: Plan) -> dict[str, Any]:
        """Execute all steps in the plan according to parallel_groups and dependencies."""

    @abstractmethod
    async def get_execution_progress(self, plan_id: str) -> dict[str, Any]:
        """Return the current execution progress of the plan."""


class MemoryContextAdapter(ABC):
    """
    Interface for the Orchestrator to query the Memory Agent for a PlanStep
    that has memory_required=True.
    """

    @abstractmethod
    async def fetch_step_context(self, step: PlanStep) -> list[dict[str, Any]]:
        """Retrieve pre-execution memory items from the Memory Agent."""


class SpecialistTaskAdapter(ABC):
    """
    Interface for the Orchestrator to dispatch a PlanStep to the appropriate
    Specialist Agent runtime.
    """

    @abstractmethod
    async def dispatch_step(self, step: PlanStep, context: list[dict[str, Any]]) -> dict[str, Any]:
        """Dispatch a PlanStep to a Specialist Agent and await TaskResult."""
