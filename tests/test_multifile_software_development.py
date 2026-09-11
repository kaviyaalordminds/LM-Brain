"""
Comprehensive test suite for Real Autonomous Software Development V1:
Multi-file project generation, controlled project validation, and bounded failure recovery.

Covers 30 required test scenarios:
- Plan generation for multi-file projects (HTML, CSS, JS, README, Validation)
- Real file creation and persistence on disk
- Project coherence & cross-reference verification (CSS link, JS script tag, Company facts)
- Project validation capability handler (positive and negative cases)
- Bounded failure recovery for missing files and missing facts
- Strict security boundaries (no arbitrary shell, no path traversal, no host escaping)
- Empirical evidence recording and full lifecycle audit logging
- Full end-to-end LocalRunner / MasterOrchestrator autonomous workflow
"""

from datetime import datetime, timezone
import pathlib
import tempfile
import uuid
import pytest

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.local_runner import LocalRunner
from executive_twins.orchestrator.dev_adapters import DevTestMasterOrchestratorFactory
from executive_twins.orchestrator.models import OrchestrationStatus
from executive_twins.schemas.common import FactItem, FactState, SecurityContext, SpecialistStatus, VerificationStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import Capability, SpecialistMetadata
from executive_twins.software_development.dev_adapters import (
    DeterministicDevelopmentPlanner,
    DevTestSoftwareDevelopmentAdapter,
    ProjectValidationCapabilityHandler,
    SoftwareDevelopmentCapabilityHandler,
    SoftwareValidationCapabilityHandler,
    create_software_development_specialist,
)
from executive_twins.software_development.models import (
    DevelopmentFileSpec,
    DevelopmentPlan,
    DevelopmentPlanStatus,
    DevelopmentRequest,
    DevelopmentResult,
    DevelopmentStatus,
    DiagnosticResult,
    PlanStep,
    PlanStepAction,
    PlanStepStatus,
)
from executive_twins.software_development.software_development_agent import SoftwareDevelopmentAgent
from executive_twins.utils.audit_logger import AuditLogger
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


@pytest.fixture
def temp_workspace_env():
    """Provides a fresh isolated workspace and wired SoftwareDevelopmentAgent for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ws_adapter = DevTestWorkspaceAdapter(base_temp_dir=tmp_dir)
        ws_adapter.create_workspace("default")

        dev_adapter = DevTestSoftwareDevelopmentAdapter(
            base_temp_dir=tmp_dir,
            use_mock_docker=True,
        )

        registry = InMemorySpecialistRegistryAdapter()
        spec = create_software_development_specialist("spec_software_dev_01")
        registry.register_specialist(spec)

        engine = SpecialistExecutionEngine(registry_client=registry)
        dev_adapter.register_all_handlers(engine)

        planner = DeterministicDevelopmentPlanner()
        agent = SoftwareDevelopmentAgent(execution_engine=engine, planner=planner)

        yield {
            "tmp_dir": tmp_dir,
            "ws_adapter": ws_adapter,
            "file_adapter": dev_adapter.file_adapter,
            "engine": engine,
            "planner": planner,
            "agent": agent,
            "workspace_path": pathlib.Path(tmp_dir) / "default",
        }


def _create_landing_page_request(workspace_id: str = "default", task: str = "Create a responsive company landing page using approved company information.") -> DevelopmentRequest:
    return DevelopmentRequest(
        request_id=f"req_{uuid.uuid4().hex[:8]}",
        specialist_id="spec_software_dev_01",
        workspace_id=workspace_id,
        task=task,
        requirements=[
            "Must generate index.html, styles.css, script.js, and README.md",
            "Must link styles.css and script.js in index.html",
            "Must include approved company information for NovaPulse Robotics",
        ],
        success_criteria=[
            "All 4 files created on disk and validated",
            "Coherence and cross-references pass project validation",
        ],
        security_context=SecurityContext(
            user_id="test_user",
            clearance_level="standard",
            is_authenticated=True,
        ),
        max_iterations=5,
        max_steps=15,
        timeout_seconds=60.0,
    )


# =============================================================================
# SCENARIO 1: Plan Generation for Multi-File Project
# =============================================================================

def test_1_plan_generation_multifile_project(temp_workspace_env):
    planner = temp_workspace_env["planner"]
    req = _create_landing_page_request()
    plan = planner.create_plan(req)

    assert plan.plan_id.startswith("plan-")
    assert plan.request_id == req.request_id
    assert len(plan.steps) == 6
    assert plan.steps[0].action == PlanStepAction.INSPECT
    assert plan.steps[1].action == PlanStepAction.CREATE_FILE
    assert plan.steps[1].inputs["relative_path"] == "index.html"
    assert plan.steps[2].action == PlanStepAction.CREATE_FILE
    assert plan.steps[2].inputs["relative_path"] == "styles.css"
    assert plan.steps[3].action == PlanStepAction.CREATE_FILE
    assert plan.steps[3].inputs["relative_path"] == "script.js"
    assert plan.steps[4].action == PlanStepAction.CREATE_FILE
    assert plan.steps[4].inputs["relative_path"] == "README.md"
    assert plan.steps[5].action == PlanStepAction.VALIDATE_PROJECT

    assert len(plan.files) == 4
    file_paths = [f.path for f in plan.files]
    assert "index.html" in file_paths
    assert "styles.css" in file_paths
    assert "script.js" in file_paths
    assert "README.md" in file_paths


# =============================================================================
# SCENARIOS 2 - 7: Workspace Initialization and Real File Creation on Disk
# =============================================================================

def test_2_workspace_initialization(temp_workspace_env):
    ws_path = temp_workspace_env["workspace_path"]
    assert ws_path.exists()
    assert ws_path.is_dir()


def test_3_index_html_created_on_disk(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    html_file = temp_workspace_env["workspace_path"] / "index.html"
    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "<html" in content
    assert "NovaPulse Robotics" in content


def test_4_styles_css_created_on_disk(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    css_file = temp_workspace_env["workspace_path"] / "styles.css"
    assert css_file.exists()
    content = css_file.read_text(encoding="utf-8")
    assert "--primary-color" in content
    assert "@media" in content
    assert "{" in content and "}" in content


def test_5_script_js_created_on_disk(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    js_file = temp_workspace_env["workspace_path"] / "script.js"
    assert js_file.exists()
    content = js_file.read_text(encoding="utf-8")
    assert "DOMContentLoaded" in content or "function" in content or "console.log" in content


def test_6_readme_md_created_on_disk(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    readme_file = temp_workspace_env["workspace_path"] / "README.md"
    assert readme_file.exists()
    content = readme_file.read_text(encoding="utf-8")
    assert "NovaPulse Robotics" in content
    assert "index.html" in content


def test_7_all_files_exist_simultaneously(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    ws = temp_workspace_env["workspace_path"]
    for fname in ["index.html", "styles.css", "script.js", "README.md"]:
        fpath = ws / fname
        assert fpath.exists(), f"Expected {fname} to exist on disk"
        assert fpath.stat().st_size > 0, f"Expected {fname} to have non-zero size"


# =============================================================================
# SCENARIOS 8 - 10: Cross-References and Company Information
# =============================================================================

def test_8_html_references_css_properly(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    html_content = (temp_workspace_env["workspace_path"] / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in html_content or "styles.css" in html_content


def test_9_html_references_js_properly(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    html_content = (temp_workspace_env["workspace_path"] / "index.html").read_text(encoding="utf-8")
    assert 'src="script.js"' in html_content or "script.js" in html_content


def test_10_html_contains_approved_company_facts(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    html_content = (temp_workspace_env["workspace_path"] / "index.html").read_text(encoding="utf-8")
    assert "NovaPulse Robotics" in html_content
    assert "Autonomous" in html_content or "warehouse" in html_content.lower()


# =============================================================================
# SCENARIOS 11 - 19: Project Validation Handler Positive & Negative Cases
# =============================================================================

def test_11_project_validation_passes_when_all_files_correct(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")

    # Write 4 valid files via FileService
    file_service.create_file("index.html", "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>")
    file_service.create_file("styles.css", "body { margin: 0; }")
    file_service.create_file("script.js", "console.log('init');")
    file_service.create_file("README.md", "# Project Documentation\nManifest and setup instructions.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_01",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default", "expected_keywords": ["NovaPulse Robotics"]},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is True
    assert "Project validation passed successfully" in out.output_text
    assert len(out.artifacts) == 4
    assert len(out.errors) == 0


def test_12_validation_fails_if_index_html_missing(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    file_service.create_file("styles.css", "body { margin: 0; }")
    file_service.create_file("script.js", "console.log('init');")
    file_service.create_file("README.md", "# Project Doc\nSome overview.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_02",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default", "required_files": ["index.html", "styles.css", "script.js", "README.md"]},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("index.html" in e for e in out.errors)


def test_13_validation_fails_if_styles_css_missing(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    file_service.create_file("index.html", "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>")
    file_service.create_file("script.js", "console.log('init');")
    file_service.create_file("README.md", "# Project Doc\nSome overview.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_03",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default"},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("styles.css" in e for e in out.errors)


def test_14_validation_fails_if_script_js_missing(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    file_service.create_file("index.html", "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>")
    file_service.create_file("styles.css", "body { margin: 0; }")
    file_service.create_file("README.md", "# Project Doc\nSome overview.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_04",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default"},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("script.js" in e for e in out.errors)


def test_15_validation_fails_if_readme_missing(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    file_service.create_file("index.html", "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>")
    file_service.create_file("styles.css", "body { margin: 0; }")
    file_service.create_file("script.js", "console.log('init');")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_05",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default"},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("README.md" in e for e in out.errors)


def test_16_validation_fails_if_html_missing_css_link(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    # Missing link rel=stylesheet href=styles.css
    file_service.create_file("index.html", "<!DOCTYPE html><html><head></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>")
    file_service.create_file("styles.css", "body { margin: 0; }")
    file_service.create_file("script.js", "console.log('init');")
    file_service.create_file("README.md", "# Project Doc\nSome overview.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_06",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default"},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("styles.css" in e for e in out.errors)


def test_17_validation_fails_if_html_missing_js_link(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    # Missing script src=script.js
    file_service.create_file("index.html", "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1></body></html>")
    file_service.create_file("styles.css", "body { margin: 0; }")
    file_service.create_file("script.js", "console.log('init');")
    file_service.create_file("README.md", "# Project Doc\nSome overview.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_07",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default"},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("script.js" in e for e in out.errors)


def test_18_validation_fails_if_empty_file(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    file_service.create_file("index.html", "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>")
    file_service.create_file("styles.css", "   \n  ")  # Empty whitespace
    file_service.create_file("script.js", "console.log('init');")
    file_service.create_file("README.md", "# Project Doc\nSome overview.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_08",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default"},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("empty" in e.lower() for e in out.errors)


def test_19_validation_fails_if_company_facts_missing(temp_workspace_env):
    file_adapter = temp_workspace_env["file_adapter"]
    file_service = file_adapter.get_file_service("default")
    # Generic title without NovaPulse Robotics
    file_service.create_file("index.html", "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>Generic Company</h1><script src=\"script.js\"></script></body></html>")
    file_service.create_file("styles.css", "body { margin: 0; }")
    file_service.create_file("script.js", "console.log('init');")
    file_service.create_file("README.md", "# Project Doc\nSome overview.")

    handler = ProjectValidationCapabilityHandler(file_adapter)
    req = DelegationRequest(
        delegation_id="del_val_09",
        parent_task_id="task_01",
        executive_twin_id="twin-orchestrator",
        specialist_id="spec_software_dev_01",
        objective="Validate project",
        task="Validate landing page project",
        required_capabilities=["project_validation"],
        expected_output="Validated project files",
        inputs={"workspace_id": "default", "expected_keywords": ["NovaPulse Robotics"]},
    )
    spec = create_software_development_specialist("spec_software_dev_01")
    out = handler.execute(req, spec)

    assert out.success is False
    assert any("NovaPulse Robotics" in e for e in out.errors)


# =============================================================================
# SCENARIOS 20 - 24: Bounded Failure Recovery
# =============================================================================

def test_20_bounded_failure_recovery_missing_css(temp_workspace_env):
    """Simulate initial failure where styles.css was not created; agent diagnoses and recovers."""
    planner = temp_workspace_env["planner"]
    agent = temp_workspace_env["agent"]

    # Plan that omits styles.css initially, jumps directly to validation
    def faulty_plan(request: DevelopmentRequest):
        return [
            PlanStep(step_id="s1", action=PlanStepAction.INSPECT, description="Inspect", inputs={"workspace_id": request.workspace_id, "relative_path": ""}),
            PlanStep(step_id="s2", action=PlanStepAction.CREATE_FILE, description="Create HTML", inputs={"workspace_id": request.workspace_id, "relative_path": "index.html", "content": "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>", "overwrite": True}),
            PlanStep(step_id="s3", action=PlanStepAction.CREATE_FILE, description="Create JS", inputs={"workspace_id": request.workspace_id, "relative_path": "script.js", "content": "console.log('init');", "overwrite": True}),
            PlanStep(step_id="s4", action=PlanStepAction.CREATE_FILE, description="Create README", inputs={"workspace_id": request.workspace_id, "relative_path": "README.md", "content": "# Project Doc\nOverview text here.", "overwrite": True}),
            PlanStep(step_id="s5", action=PlanStepAction.VALIDATE_PROJECT, description="Validate", inputs={"workspace_id": request.workspace_id, "required_files": ["index.html", "styles.css", "script.js", "README.md"]}),
        ]

    planner.custom_plan_generator = faulty_plan
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    assert res.iterations_run >= 1
    assert (temp_workspace_env["workspace_path"] / "styles.css").exists()


def test_21_bounded_failure_recovery_missing_js(temp_workspace_env):
    """Simulate initial failure where script.js was not created; agent diagnoses and recovers."""
    planner = temp_workspace_env["planner"]
    agent = temp_workspace_env["agent"]

    def faulty_plan(request: DevelopmentRequest):
        return [
            PlanStep(step_id="s1", action=PlanStepAction.INSPECT, description="Inspect", inputs={"workspace_id": request.workspace_id, "relative_path": ""}),
            PlanStep(step_id="s2", action=PlanStepAction.CREATE_FILE, description="Create HTML", inputs={"workspace_id": request.workspace_id, "relative_path": "index.html", "content": "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>", "overwrite": True}),
            PlanStep(step_id="s3", action=PlanStepAction.CREATE_FILE, description="Create CSS", inputs={"workspace_id": request.workspace_id, "relative_path": "styles.css", "content": "body { margin: 0; }", "overwrite": True}),
            PlanStep(step_id="s4", action=PlanStepAction.CREATE_FILE, description="Create README", inputs={"workspace_id": request.workspace_id, "relative_path": "README.md", "content": "# Project Doc\nOverview text here.", "overwrite": True}),
            PlanStep(step_id="s5", action=PlanStepAction.VALIDATE_PROJECT, description="Validate", inputs={"workspace_id": request.workspace_id, "required_files": ["index.html", "styles.css", "script.js", "README.md"]}),
        ]

    planner.custom_plan_generator = faulty_plan
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    assert res.iterations_run >= 1
    assert (temp_workspace_env["workspace_path"] / "script.js").exists()


def test_22_bounded_failure_recovery_missing_readme(temp_workspace_env):
    """Simulate initial failure where README.md was not created; agent diagnoses and recovers."""
    planner = temp_workspace_env["planner"]
    agent = temp_workspace_env["agent"]

    def faulty_plan(request: DevelopmentRequest):
        return [
            PlanStep(step_id="s1", action=PlanStepAction.INSPECT, description="Inspect", inputs={"workspace_id": request.workspace_id, "relative_path": ""}),
            PlanStep(step_id="s2", action=PlanStepAction.CREATE_FILE, description="Create HTML", inputs={"workspace_id": request.workspace_id, "relative_path": "index.html", "content": "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>", "overwrite": True}),
            PlanStep(step_id="s3", action=PlanStepAction.CREATE_FILE, description="Create CSS", inputs={"workspace_id": request.workspace_id, "relative_path": "styles.css", "content": "body { margin: 0; }", "overwrite": True}),
            PlanStep(step_id="s4", action=PlanStepAction.CREATE_FILE, description="Create JS", inputs={"workspace_id": request.workspace_id, "relative_path": "script.js", "content": "console.log('init');", "overwrite": True}),
            PlanStep(step_id="s5", action=PlanStepAction.VALIDATE_PROJECT, description="Validate", inputs={"workspace_id": request.workspace_id, "required_files": ["index.html", "styles.css", "script.js", "README.md"]}),
        ]

    planner.custom_plan_generator = faulty_plan
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    assert res.iterations_run >= 1
    assert (temp_workspace_env["workspace_path"] / "README.md").exists()


def test_23_bounded_failure_recovery_missing_company_facts(temp_workspace_env):
    """Simulate initial failure where index.html is missing company facts; recovery injects them."""
    planner = temp_workspace_env["planner"]
    agent = temp_workspace_env["agent"]

    def faulty_plan(request: DevelopmentRequest):
        return [
            PlanStep(step_id="s1", action=PlanStepAction.INSPECT, description="Inspect", inputs={"workspace_id": request.workspace_id, "relative_path": ""}),
            PlanStep(step_id="s2", action=PlanStepAction.CREATE_FILE, description="Create HTML", inputs={"workspace_id": request.workspace_id, "relative_path": "index.html", "content": "<!DOCTYPE html><html><head><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>Generic Untitled</h1><script src=\"script.js\"></script></body></html>", "overwrite": True}),
            PlanStep(step_id="s3", action=PlanStepAction.CREATE_FILE, description="Create CSS", inputs={"workspace_id": request.workspace_id, "relative_path": "styles.css", "content": "body { margin: 0; }", "overwrite": True}),
            PlanStep(step_id="s4", action=PlanStepAction.CREATE_FILE, description="Create JS", inputs={"workspace_id": request.workspace_id, "relative_path": "script.js", "content": "console.log('init');", "overwrite": True}),
            PlanStep(step_id="s5", action=PlanStepAction.CREATE_FILE, description="Create README", inputs={"workspace_id": request.workspace_id, "relative_path": "README.md", "content": "# Project Doc\nOverview text here.", "overwrite": True}),
            PlanStep(step_id="s6", action=PlanStepAction.VALIDATE_PROJECT, description="Validate", inputs={"workspace_id": request.workspace_id, "expected_keywords": ["NovaPulse Robotics"]}),
        ]

    planner.custom_plan_generator = faulty_plan
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    assert res.iterations_run >= 1
    html_content = (temp_workspace_env["workspace_path"] / "index.html").read_text(encoding="utf-8")
    assert "NovaPulse Robotics" in html_content


def test_24_recovery_respects_max_iterations(temp_workspace_env):
    """When a failure is permanently unfixable, agent respects max_iterations and stops cleanly."""
    planner = temp_workspace_env["planner"]
    agent = temp_workspace_env["agent"]

    def permanently_broken_diagnostic(req, step, ev, out, it):
        return DiagnosticResult(
            can_recover=True,
            diagnosis="Injecting no-op step that does not fix error",
            suggested_fix_steps=[PlanStep(step_id=f"noop_{it}", action=PlanStepAction.INSPECT, description="No-op inspect", inputs={"workspace_id": req.workspace_id, "relative_path": ""})],
        )

    def faulty_plan(request: DevelopmentRequest):
        return [
            PlanStep(step_id="s1", action=PlanStepAction.VALIDATE_PROJECT, description="Validate", inputs={"workspace_id": request.workspace_id, "required_files": ["non_existent_file.xyz"]}),
        ]

    planner.custom_plan_generator = faulty_plan
    planner.custom_diagnostic_handler = permanently_broken_diagnostic

    req = _create_landing_page_request()
    req.max_iterations = 3
    res = agent.execute_development(req)

    assert res.status in (DevelopmentStatus.FAILED, DevelopmentStatus.BLOCKED, DevelopmentStatus.PARTIAL)
    assert res.iterations_run <= req.max_iterations


# =============================================================================
# SCENARIOS 25 - 27: Security Boundaries and Isolation
# =============================================================================

def test_25_security_no_arbitrary_shell(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    req.task = "Run shell_exec('rm -rf /') to clean project"
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.BLOCKED
    assert "SECURITY_ERROR" in str(res.failure_reason)


def test_26_security_no_path_traversal(temp_workspace_env):
    planner = temp_workspace_env["planner"]
    agent = temp_workspace_env["agent"]

    def traversal_plan(request: DevelopmentRequest):
        return [
            PlanStep(
                step_id="step-malicious",
                action=PlanStepAction.CREATE_FILE,
                description="Escape workspace root",
                inputs={"workspace_id": request.workspace_id, "relative_path": "../../secret.txt", "content": "owned"},
            )
        ]

    planner.custom_plan_generator = traversal_plan
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.BLOCKED
    assert "PATH_TRAVERSAL_REJECTED" in str(res.failure_reason)


def test_27_security_no_absolute_host_paths(temp_workspace_env):
    planner = temp_workspace_env["planner"]
    agent = temp_workspace_env["agent"]

    def abs_path_plan(request: DevelopmentRequest):
        return [
            PlanStep(
                step_id="step-abs",
                action=PlanStepAction.CREATE_FILE,
                description="Write to absolute path",
                inputs={"workspace_id": request.workspace_id, "relative_path": "C:/Windows/System32/evil.dll", "content": "evil"},
            )
        ]

    planner.custom_plan_generator = abs_path_plan
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.BLOCKED
    assert "PATH_OUTSIDE_WORKSPACE_REJECTED" in str(res.failure_reason)


# =============================================================================
# SCENARIOS 28 - 29: Evidence, Artifacts, and Audit Lifecycle Logging
# =============================================================================

def test_28_evidence_and_artifacts_recorded(temp_workspace_env):
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    assert len(res.artifacts) >= 4
    assert len(res.evidence.items) > 0
    assert any(isinstance(e, VerificationEvidence) for e in res.evidence.items)
    assert res.verification == VerificationStatus.VERIFIED


def test_29_audit_logging_full_lifecycle(temp_workspace_env):
    AuditLogger.clear_events()
    agent = temp_workspace_env["agent"]
    req = _create_landing_page_request()
    res = agent.execute_development(req)

    assert res.status == DevelopmentStatus.SUCCESS
    event_types = [e.event_type for e in AuditLogger.get_events()]

    assert "development.request_received" in event_types
    assert "development.plan_created" in event_types
    assert "development.step_started" in event_types
    assert "development.step_completed" in event_types
    assert "development.succeeded" in event_types


# =============================================================================
# SCENARIO 30: Full End-to-End Execution via LocalRunner and MasterOrchestrator
# =============================================================================

def test_30_end_to_end_local_runner_landing_page(temp_workspace_env):
    tmp_dir = temp_workspace_env["tmp_dir"]
    runner = LocalRunner.create_default(base_workspace_dir=tmp_dir)

    goal = "Create a small responsive company landing page using the company's approved company information."
    result = runner.run(goal)

    assert result.final_status == OrchestrationStatus.COMPLETED
    assert len(result.completed_steps) >= 5
    assert result.memory_writeback_status == "SUCCESS"

    # Verify real files exist on disk
    ws_dir = pathlib.Path(tmp_dir) / "default"
    assert (ws_dir / "index.html").exists()
    assert (ws_dir / "styles.css").exists()
    assert (ws_dir / "script.js").exists()
    assert (ws_dir / "README.md").exists()

    # Verify WorkflowRun dict format for frontend
    wf_dict = runner.to_workflow_run_dict(result, goal)
    assert wf_dict["status"] == "COMPLETED"
    assert len(wf_dict["workspaceFiles"]) >= 4
    file_paths = [f["path"] for f in wf_dict["workspaceFiles"]]
    assert "index.html" in file_paths
    assert "styles.css" in file_paths
    assert "script.js" in file_paths
    assert "README.md" in file_paths
