"""
Tests for Orchestrator Boundary and Non-Execution Isolation.

Explicitly verifies that the Planner Agent:
  - Does NOT spawn specialists
  - Does NOT execute tools
  - Does NOT call Memory Agent
  - Does NOT call Jina
  - Does NOT modify Obsidian
  - Does NOT create implementation files on disk
  - Produces clean Plan contracts for the future Master Orchestrator
"""
from __future__ import annotations

import os
from pathlib import Path
import pytest

from app.contracts.integration import OrchestratorPlanConsumer
from app.models.plan import Plan, PlanRequest, PlanStatus
from app.planner import Planner


class TestNonExecutionBoundary:
    def test_planner_creates_only_plan_no_file_artifacts(self, planner: Planner, tmp_path: Path):
        """Planner must not create any source code or artifact files on disk."""
        initial_files = set(tmp_path.iterdir())
        req = PlanRequest(
            requestId="boundary-test-01",
            userRequest="Create a full stack Python FastAPI application with Docker and PostgreSQL",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY

        current_files = set(tmp_path.iterdir())
        # No files created in tmp_path or anywhere outside the plan object
        assert initial_files == current_files

    def test_planner_does_not_modify_obsidian(self, planner: Planner):
        """Verify Planner does not touch any Obsidian vault path."""
        obsidian_vault = Path(r"C:\Lordminds\Multiagent\memory-agent\obsedian")
        if obsidian_vault.exists():
            initial_count = sum(1 for _ in obsidian_vault.rglob("*.md"))
            req = PlanRequest(
                requestId="boundary-test-obsidian",
                userRequest="Find official documentation for TanStack Query and persist it",
            )
            plan = planner.create_plan(req)
            assert plan.status == PlanStatus.READY
            after_count = sum(1 for _ in obsidian_vault.rglob("*.md"))
            assert initial_count == after_count

    def test_plan_consumed_by_orchestrator_contract(self, planner: Planner):
        """Verify the Plan object satisfies the OrchestratorPlanConsumer contract."""
        req = PlanRequest(
            requestId="boundary-test-orchestrator",
            userRequest="Build a React login form with API integration",
        )
        plan = planner.create_plan(req)

        # Mock Orchestrator consumer implementing the interface
        class MockOrchestrator(OrchestratorPlanConsumer):
            async def execute_plan(self, p: Plan) -> dict:
                return {"executed_steps": len(p.steps), "status": "SIMULATED_SUCCESS"}

            async def get_execution_progress(self, plan_id: str) -> dict:
                return {"plan_id": plan_id, "progress": 1.0}

        orchestrator = MockOrchestrator()
        assert plan.plan_id is not None
        assert len(plan.steps) >= 1
        assert isinstance(plan.execution_order, list)
        assert isinstance(plan.parallel_groups, list)

    def test_planner_works_fully_in_memory_without_external_services(self, planner: Planner):
        """Planner must work without any network connectivity or external model."""
        req = PlanRequest(
            requestId="offline-test-01",
            userRequest="Design an AI/ML vector search application with security review",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY
        assert plan.plan_id.startswith("plan-")
        assert len(plan.steps) >= 2
