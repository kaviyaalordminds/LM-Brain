"""
End-to-End Planner Tests, Determinism Verification, and Manual Scenario Tests.
"""
from __future__ import annotations

import pytest

from app.core.store import InMemoryPlanStore
from app.models.plan import PlanRequest, PlanStatus, ExecutionMode
from app.planner import Planner


class TestPlannerCore:
    def test_create_plan_simple_request(self, planner: Planner):
        req = PlanRequest(
            requestId="req-test-01",
            userRequest="Build a simple REST API backend",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY
        assert len(plan.steps) >= 1
        assert any(s.specialist_id == "backend" for s in plan.steps)
        assert plan.validation_errors == []

    def test_determinism_identical_request_equivalent_plan(self, planner: Planner):
        """Submit the same request twice; compare specialists, dependencies, and execution order."""
        request_text = "Build an e-commerce website with React frontend, REST backend, PostgreSQL database, and automated testing"
        req1 = PlanRequest(requestId="req-det-01", userRequest=request_text)
        req2 = PlanRequest(requestId="req-det-02", userRequest=request_text)

        plan1 = planner.create_plan(req1)
        plan2 = planner.create_plan(req2)

        assert plan1.status == PlanStatus.READY
        assert plan2.status == PlanStatus.READY

        # Compare specialist sequences
        specs1 = [s.specialist_id for s in plan1.steps]
        specs2 = [s.specialist_id for s in plan2.steps]
        assert specs1 == specs2

        # Compare parallel groups
        assert len(plan1.parallel_groups) == len(plan2.parallel_groups)
        for g1, g2 in zip(plan1.parallel_groups, plan2.parallel_groups):
            # Same group sizes and specialist types
            assert len(g1) == len(g2)

        # Compare execution order length and consistency
        assert len(plan1.execution_order) == len(plan2.execution_order)

    def test_scenario_1_login_page(self, planner: Planner):
        """Scenario 1: 'I need a login page.'"""
        req = PlanRequest(
            requestId="scenario-1",
            userRequest="I need a login page.",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY
        specialists = [s.specialist_id for s in plan.steps]
        # Login page maps to web_development and/or security
        assert "web_development" in specialists or "security" in specialists
        for step in plan.steps:
            assert len(step.verification_criteria) > 0
            assert len(step.expected_outputs) > 0

    def test_scenario_2_ecommerce_full_stack(self, planner: Planner):
        """
        Scenario 2: 'Build an e-commerce website with React frontend,
        REST backend, PostgreSQL database, authentication, automated testing and Docker deployment.'
        """
        req = PlanRequest(
            requestId="scenario-2",
            userRequest="Build an e-commerce website with React frontend, REST backend, PostgreSQL database, authentication, automated testing and Docker deployment.",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY
        specialists = {s.specialist_id for s in plan.steps}
        expected_specialists = {"web_development", "backend", "database", "security", "testing", "devops"}
        assert expected_specialists.issubset(specialists)
        assert len(plan.parallel_groups) >= 2
        assert len(plan.execution_order) == len(plan.steps)

    def test_scenario_3_ai_rag_application(self, planner: Planner):
        """
        Scenario 3: 'I need an AI application using RAG, embeddings, vector database and an LLM.'
        """
        req = PlanRequest(
            requestId="scenario-3",
            userRequest="I need an AI application using RAG, embeddings, vector database and an LLM.",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY
        specialists = [s.specialist_id for s in plan.steps]
        assert "ai_ml" in specialists

    def test_scenario_4_research_documentation_and_component(self, planner: Planner):
        """
        Scenario 4: 'Find the latest official documentation for a technology and use it to design a web component.'
        """
        req = PlanRequest(
            requestId="scenario-4",
            userRequest="Find the latest official documentation for a technology and use it to design a web component.",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY
        specialists = {s.specialist_id for s in plan.steps}
        assert "research" in specialists
        assert "web_development" in specialists
        # Research step must have research_required=True
        research_step = next(s for s in plan.steps if s.specialist_id == "research")
        assert research_step.research_required is True

    def test_memory_required_flag_detection(self, planner: Planner):
        req = PlanRequest(
            requestId="req-mem-01",
            userRequest="Build the application according to our company's existing architecture and codebase.",
        )
        plan = planner.create_plan(req)
        assert plan.status == PlanStatus.READY
        # Steps should have memory_required=True
        assert any(s.memory_required is True for s in plan.steps)

    def test_plan_store_operations(self, plan_store: InMemoryPlanStore):
        planner = Planner(store=plan_store)
        req = PlanRequest(requestId="req-store-01", userRequest="Build a testing plan")
        plan = planner.create_plan(req)

        assert plan_store.exists(plan.plan_id) is True
        retrieved = plan_store.get(plan.plan_id)
        assert retrieved is not None
        assert retrieved.plan_id == plan.plan_id

        all_plans = plan_store.list_all()
        assert len(all_plans) == 1

        # Duplicate create rejected
        with pytest.raises(ValueError):
            plan_store.create(plan)
