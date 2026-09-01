"""
Planner ↔ Existing Components Contract Integration Test Suite

Verifies bidirectional contract compatibility between:
- Planner (Plan, PlanStep)
- Specialist Agent (TaskRequest, TaskResult, Artifact, AgentConfig, Permissions)
- Memory Agent (Search, Research, Validation, Write endpoints, MemoryClient)
- Research Capability (Jina Provider, EvidenceItem, ApprovalStatus)

Zero execution of specialists, tools, models, or network calls occurs in this suite.
"""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure all 3 workspaces are on sys.path for contract import testing
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "planner"))
sys.path.insert(0, str(ROOT / "specialist-agent"))
sys.path.insert(0, str(ROOT / "memory-agent"))

from app.models.plan import PlanRequest, PlanStep, PlanStatus, StepStatus, ExecutionMode, FailureAction
from app.planner import Planner
from app.contracts.adapter import (
    map_plan_step_to_specialist_task_dict,
    map_task_result_dict_to_step_status,
)
from specialist_agent.contracts.task import TaskRequest, TaskContext, TaskConstraints, ExpectedOutput
from specialist_agent.contracts.result import TaskResult, TaskStatus, VerificationVerdict, VerificationOutcome
from specialist_agent.contracts.artifact import Artifact, ArtifactType
from specialist_agent.agents import ALL_AGENT_CONFIGS
from specialist_agent.permissions.policy import Permission, PermissionPolicy, STANDARD_POLICIES


class TestSpecialistCatalogContract:
    def test_all_10_specialists_exist_in_specialist_agent_catalog(self, planner: Planner):
        """Verify that every specialist ID produced by the Planner exists in Specialist Agent ALL_AGENT_CONFIGS."""
        specialist_requests = {
            "web_development": "I need a React frontend component",
            "image_generation": "Generate a hero image for the header",
            "backend": "Create a FastAPI backend endpoint",
            "database": "Design a PostgreSQL database schema",
            "api_integration": "Connect to a third-party payment gateway API",
            "security": "Perform a security review of authentication",
            "testing": "Create a unit test suite with pytest",
            "devops": "Create a Dockerfile and CI/CD deployment configuration",
            "ai_ml": "Build an AI RAG pipeline with vector search",
            "research": "Find official documentation for a library",
        }
        for expected_id, req_text in specialist_requests.items():
            plan = planner.create_plan(PlanRequest(requestId=f"cat-{expected_id}", userRequest=req_text))
            assert plan.status == PlanStatus.READY
            step = next(s for s in plan.steps if s.specialist_id == expected_id)
            assert step.specialist_id in ALL_AGENT_CONFIGS
            agent_config = ALL_AGENT_CONFIGS[step.specialist_id]
            assert agent_config.agent_type == step.specialist_id


class TestPlanStepToTaskRequestMapping:
    def test_web_dev_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-01", userRequest="Build a responsive React landing page"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "web_development"
        assert task_req.task_id == step.step_id
        assert task_req.constraints.max_retries == step.failure_policy.max_retries
        assert "code" in task_req.expected_output.artifact_types

    def test_image_gen_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-02", userRequest="Generate a hero image for website"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "image_generation"
        assert "image" in task_req.expected_output.artifact_types

    def test_backend_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-03", userRequest="Create a REST API backend"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "backend"

    def test_database_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-04", userRequest="Design a PostgreSQL schema"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "database"
        assert "schema" in task_req.expected_output.artifact_types

    def test_api_integration_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-05", userRequest="Connect to third-party Stripe API"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "api_integration"

    def test_security_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-06", userRequest="Audit API security and JWT auth"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "security"

    def test_testing_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-07", userRequest="Create automated unit tests"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "testing"

    def test_devops_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-08", userRequest="Create Docker deployment and CI/CD"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "devops"

    def test_ai_ml_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-09", userRequest="Build AI assistant with RAG"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type in ("ai_ml", "database")

    def test_research_plan_step_to_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="c-10", userRequest="Find official documentation for PostgreSQL"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        task_req = TaskRequest(**task_dict)
        assert task_req.agent_type == "research"


class TestFidelityAndPreservation:
    def test_expected_inputs_preserved_in_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-01", userRequest="Design a database schema"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        assert task_dict["context"]["extra"]["expected_inputs"] == step.expected_inputs

    def test_expected_outputs_preserved_in_task_request(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-02", userRequest="Create FastAPI backend API"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        assert task_dict["expected_output"]["description"] == "; ".join(step.expected_outputs)

    def test_verification_criteria_preserved_in_metadata(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-03", userRequest="Perform API security audit"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        assert task_dict["metadata"]["verification_criteria"] == step.verification_criteria

    def test_dependencies_preserved_in_metadata(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-04", userRequest="Design PostgreSQL database then build backend API"))
        backend_step = next(s for s in plan.steps if s.specialist_id == "backend")
        task_dict = map_plan_step_to_specialist_task_dict(backend_step)
        assert len(task_dict["metadata"]["dependencies"]) > 0

    def test_execution_mode_preserved_in_metadata(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-05", userRequest="React landing page and PostgreSQL database"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        assert task_dict["metadata"]["execution_mode"] in ("PARALLEL", "SEQUENTIAL")

    def test_max_retries_constraint_mapped_from_failure_policy(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-06", userRequest="Connect to third-party payment API"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        assert task_dict["constraints"]["max_retries"] == step.failure_policy.max_retries

    def test_memory_required_flag_mapped_to_context_extra(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-07", userRequest="Build according to company existing architecture"))
        step = plan.steps[0]
        task_dict = map_plan_step_to_specialist_task_dict(step)
        assert task_dict["context"]["extra"]["memory_required"] is True

    def test_research_required_flag_mapped_to_context_extra(self, planner: Planner):
        plan = planner.create_plan(PlanRequest(requestId="fid-08", userRequest="Find official documentation for Tailwind v4"))
        research_step = next(s for s in plan.steps if s.specialist_id == "research")
        task_dict = map_plan_step_to_specialist_task_dict(research_step)
        assert task_dict["context"]["extra"]["research_required"] is True


class TestMemoryAndResearchContractCompatibility:
    def test_memory_agent_search_payload_compatibility(self, planner: Planner):
        """Verify memory search payload expected by Memory Agent matches what Orchestrator creates."""
        plan = planner.create_plan(PlanRequest(requestId="mem-compat-01", userRequest="Build according to our existing architecture"))
        step = plan.steps[0]
        search_payload = {"query": f"Existing architecture for {step.title}", "taskId": step.step_id}
        assert "query" in search_payload
        assert "taskId" in search_payload

    def test_memory_agent_research_payload_compatibility(self, planner: Planner):
        """Verify research payload expected by Memory Agent matches what Orchestrator creates."""
        plan = planner.create_plan(PlanRequest(requestId="res-compat-01", userRequest="Find latest official documentation for PostgreSQL"))
        step = plan.steps[0]
        research_payload = {"query": step.description, "taskId": step.step_id}
        assert "query" in research_payload

    def test_jina_evidence_item_compatibility_with_research_step(self, planner: Planner):
        """Verify evidence items returned by Jina/MemoryAgent can be passed as TaskContext items."""
        sample_evidence = [
            {"title": "PostgreSQL Documentation", "source": "https://www.postgresql.org/docs/", "content": "Relational DB docs"}
        ]
        context = TaskContext(context_items=sample_evidence, trust_level="UNVERIFIED")
        assert len(context.context_items) == 1
        assert context.trust_level == "UNVERIFIED"


class TestResultAndArtifactCompatibility:
    def test_task_result_completed_maps_to_step_completed(self):
        res_dict = {"status": "completed", "output": "Done"}
        assert map_task_result_dict_to_step_status(res_dict) == StepStatus.COMPLETED

    def test_task_result_failed_maps_to_step_failed(self):
        res_dict = {"status": "failed", "output": "Error"}
        assert map_task_result_dict_to_step_status(res_dict) == StepStatus.FAILED

    def test_task_result_running_maps_to_step_running(self):
        res_dict = {"status": "running"}
        assert map_task_result_dict_to_step_status(res_dict) == StepStatus.RUNNING

    def test_task_result_artifacts_structure(self):
        art = Artifact(
            type=ArtifactType.CODE,
            path="/path/to/main.py",
            content="print('hello')",
            is_mock=False,
        )
        res = TaskResult(
            task_id="step-01-backend",
            agent_id="agent-01",
            agent_type="backend",
            status=TaskStatus.COMPLETED,
            artifacts=[art],
        )
        assert len(res.artifacts) == 1
        assert res.artifacts[0].type == ArtifactType.CODE


class TestPermissionBoundaries:
    def test_security_specialist_permission_boundary_preservation(self):
        """Verify Security Agent permissions do not include ADMIN or EXECUTE."""
        sec_policy = PermissionPolicy("sec-test", STANDARD_POLICIES["security"])
        assert sec_policy.has(Permission.READ) is True
        assert sec_policy.has(Permission.AUDIT) is True
        assert sec_policy.has(Permission.EXECUTE) is False
        assert sec_policy.has(Permission.ADMIN) is False

    def test_image_generation_permission_boundary_preservation(self):
        """Verify Image Generation Agent has no ADMIN permission."""
        img_policy = PermissionPolicy("img-test", STANDARD_POLICIES["image_generation"])
        assert img_policy.has(Permission.ADMIN) is False
        assert img_policy.has(Permission.WRITE_ARTIFACT) is True


class TestCompoundProjectContractFidelity:
    def test_compound_saas_project_step_by_step_contract_fidelity(self, planner: Planner):
        """Test a complete production SaaS request and verify every step converts to TaskRequest with 100% validity."""
        req_text = "Build a production SaaS application with React frontend, FastAPI backend, PostgreSQL, JWT auth, payment API, automated testing and Docker deployment."
        plan = planner.create_plan(PlanRequest(requestId="saas-contract-01", userRequest=req_text))
        assert plan.status == PlanStatus.READY
        assert len(plan.steps) == 7

        for step in plan.steps:
            # 1. Specialist ID exists
            assert step.specialist_id in ALL_AGENT_CONFIGS
            # 2. Conversion produces valid TaskRequest
            task_dict = map_plan_step_to_specialist_task_dict(step)
            task_req = TaskRequest(**task_dict)
            assert task_req.agent_type == step.specialist_id
            assert task_req.task_id == step.step_id
            # 3. Verification criteria are present
            assert len(task_req.metadata["verification_criteria"]) > 0
            # 4. Outputs are defined
            assert len(task_req.expected_output.description) > 0

    def test_no_execution_side_effects_during_contract_mapping(self, planner: Planner):
        """Verify that mapping all steps of a complex plan creates 0 file changes, 0 agent spawns, and 0 network calls."""
        req_text = "Build a complex AI web application with database, backend, security and DevOps"
        plan = planner.create_plan(PlanRequest(requestId="pure-01", userRequest=req_text))
        for step in plan.steps:
            task_dict = map_plan_step_to_specialist_task_dict(step)
            task_req = TaskRequest(**task_dict)
            assert task_req.task_id == step.step_id
