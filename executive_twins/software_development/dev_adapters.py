"""
DEV/TEST adapters, deterministic development planners, and capability handlers for Software Development Agent.
Used for deterministic testing and specialist registration.
"""

from typing import Any, Callable, Dict, List, Optional
import uuid

from executive_twins.command_execution.dev_adapters import (
    BuildCapabilityHandler,
    DevCommandExecutorAdapter,
    LintCapabilityHandler,
    TestCapabilityHandler,
    TypecheckCapabilityHandler,
)
from executive_twins.docker.dev_adapters import (
    DevDockerServiceAdapter,
    DockerAvailabilityCapabilityHandler,
    DockerBuildCapabilityHandler,
    DockerInspectCapabilityHandler,
    DockerRemoveCapabilityHandler,
    DockerRunCapabilityHandler,
    DockerStopCapabilityHandler,
)
from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
    SpecialistExecutionEngine,
)
from executive_twins.files.dev_adapters import (
    DevFileServiceAdapter,
    FileCreateCapabilityHandler,
    FileDeleteCapabilityHandler,
    FileListCapabilityHandler,
    FileReadCapabilityHandler,
    FileUpdateCapabilityHandler,
)
from executive_twins.git.dev_adapters import (
    DevGitServiceAdapter,
    GitBranchCapabilityHandler,
    GitCommitCapabilityHandler,
    GitDiffCapabilityHandler,
    GitLogCapabilityHandler,
    GitStageCapabilityHandler,
    GitStatusCapabilityHandler,
    GitUnstageCapabilityHandler,
)
from executive_twins.files.interfaces import IFileService
from executive_twins.schemas.common import FactItem, FactState, SpecialistStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import Capability, RegistryProvenance, SpecialistMetadata
from executive_twins.software_development.interfaces import (
    IDevelopmentPlanner,
    ISoftwareDevelopmentAgent,
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
from executive_twins.software_development.software_development_agent import (
    SoftwareDevelopmentAgent,
)
from executive_twins.workspace.dev_adapters import (
    DevTestWorkspaceAdapter,
    WorkspaceBuildCapabilityHandler,
)


def create_software_development_specialist(
    specialist_id: str = "spec_software_dev_01",
    name: str = "Software Development Specialist",
    status: SpecialistStatus = SpecialistStatus.ACTIVE,
    security_level: str = "standard",
) -> SpecialistMetadata:
    """
    Factory creating authoritative SpecialistMetadata for the Software Development Specialist.
    Declares all supported capabilities and authorized tools.
    """
    capabilities = [
        Capability(name="software_development", description="Full lifecycle software development orchestrator"),
        Capability(name="web_development", description="Web applications and backend service development"),
        Capability(name="code_generation", description="Bounded code creation and generation"),
        Capability(name="code_modification", description="Refactoring, updates, and bugfixes"),
        Capability(name="software_testing", description="Automated test suite execution and validation"),
        Capability(name="software_validation", description="Static analysis, linting, and type checking"),
        Capability(name="project_validation", description="Controlled workspace project structure, file coherence, and semantic validation", required_tools=["file_service"]),
        # Underlying controlled capabilities
        Capability(name="file_create", description="Controlled workspace file creation", required_tools=["file_service"]),
        Capability(name="file_read", description="Controlled workspace file reading", required_tools=["file_service"]),
        Capability(name="file_update", description="Controlled workspace file updating", required_tools=["file_service"]),
        Capability(name="file_delete", description="Controlled workspace file deletion", required_tools=["file_service"]),
        Capability(name="file_list", description="Controlled workspace file listing", required_tools=["file_service"]),
        Capability(name="build_command_execution", description="Controlled build execution", required_tools=["command_executor"]),
        Capability(name="test_command_execution", description="Controlled test execution", required_tools=["command_executor"]),
        Capability(name="lint_command_execution", description="Controlled lint execution", required_tools=["command_executor"]),
        Capability(name="typecheck_command_execution", description="Controlled typecheck execution", required_tools=["command_executor"]),
        Capability(name="workspace_build", description="Controlled project build and artifact recording", required_tools=["workspace_builder"]),
        Capability(name="git_status", description="Controlled git status query", required_tools=["git"]),
        Capability(name="git_diff", description="Controlled git diff inspection", required_tools=["git"]),
        Capability(name="git_stage", description="Controlled git staging", required_tools=["git"]),
        Capability(name="git_commit", description="Controlled git commit", required_tools=["git"]),
        Capability(name="git_branch", description="Controlled git branch operations", required_tools=["git"]),
        Capability(name="git_log", description="Controlled git log query", required_tools=["git"]),
        Capability(name="git_unstage", description="Controlled git unstaging", required_tools=["git"]),
        Capability(name="docker_availability", description="Controlled docker daemon availability check", required_tools=["docker"]),
        Capability(name="docker_build", description="Controlled workspace docker image build", required_tools=["docker"]),
        Capability(name="docker_run", description="Controlled docker container execution", required_tools=["docker"]),
        Capability(name="docker_inspect", description="Controlled docker container inspection", required_tools=["docker"]),
        Capability(name="docker_stop", description="Controlled docker container stop", required_tools=["docker"]),
        Capability(name="docker_remove", description="Controlled docker container removal", required_tools=["docker"]),
    ]

    authorized_tools = [
        "file_service",
        "command_executor",
        "git",
        "docker",
        "workspace_builder",
        "static_analyzer",
        "test_runner",
        "code_generator",
    ]

    return SpecialistMetadata(
        specialist_id=specialist_id,
        name=name,
        capabilities=capabilities,
        status=status,
        authorized_tools=authorized_tools,
        security_level=security_level,
        provenance=RegistryProvenance(
            registry_id="authoritative-specialist-registry",
            snapshot_id="snap-software-dev-v1",
            metadata_version="1.0.0",
            is_authoritative=True,
        ),
    )


class DeterministicDevelopmentPlanner(IDevelopmentPlanner):
    """
    Deterministic Development Planner for DEV/TEST environments.
    Translates requests into structured, typed plan steps and provides deterministic failure diagnostics.
    """

    def __init__(
        self,
        custom_plan_generator: Optional[Callable[[DevelopmentRequest], List[PlanStep]]] = None,
        custom_diagnostic_handler: Optional[Callable[[DevelopmentRequest, PlanStep, EvidenceSet, str, int], DiagnosticResult]] = None,
    ) -> None:
        self.custom_plan_generator = custom_plan_generator
        self.custom_diagnostic_handler = custom_diagnostic_handler
        self._recovery_patches: Dict[str, str] = {}

    def set_recovery_patch(self, file_path: str, content: str) -> None:
        """Configure a patch to be applied if a test fails on that file."""
        self._recovery_patches[file_path] = content

    def create_plan(self, request: DevelopmentRequest) -> DevelopmentPlan:
        """Create structured plan steps."""
        if self.custom_plan_generator:
            steps = self.custom_plan_generator(request)
        else:
            steps = self._default_plan_generator(request)

        task_lower = request.task.lower()
        files: List[DevelopmentFileSpec] = []
        validation_steps: List[str] = []
        if "landing page" in task_lower or "website" in task_lower or "html" in task_lower or "responsive" in task_lower:
            files = [
                DevelopmentFileSpec(path="index.html", purpose="Responsive semantic HTML landing page structure and company content", is_required=True),
                DevelopmentFileSpec(path="styles.css", purpose="Responsive CSS styling, layout, typography, and theme variables", is_required=True),
                DevelopmentFileSpec(path="script.js", purpose="Client-side interaction, events, and dynamic DOM behavior", is_required=True),
                DevelopmentFileSpec(path="README.md", purpose="Project documentation, file manifest, and local inspection instructions", is_required=True),
            ]
            validation_steps = [
                "Verify index.html exists and contains valid HTML structure with company facts",
                "Verify styles.css exists and is referenced by index.html",
                "Verify script.js exists and is referenced by index.html",
                "Verify README.md exists and contains project overview",
                "Perform automated multi-file project coherence validation",
            ]

        return DevelopmentPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
            project_goal=request.task,
            workspace_id=request.workspace_id,
            files=files,
            validation_steps=validation_steps,
            success_criteria=request.success_criteria,
            steps=steps,
            current_step_index=0,
            status=DevelopmentPlanStatus.DRAFT,
        )

    def _default_plan_generator(self, request: DevelopmentRequest) -> List[PlanStep]:
        """Default heuristic plan generation for common tasks."""
        steps: List[PlanStep] = []
        task_lower = request.task.lower()

        # Step 1: Inspect workspace
        steps.append(
            PlanStep(
                step_id="step-1-inspect",
                action=PlanStepAction.INSPECT,
                description="Inspect workspace directory structure",
                inputs={"workspace_id": request.workspace_id, "relative_path": ""},
            )
        )

        # File creation / coding steps based on task keywords
        if "landing page" in task_lower or "website" in task_lower or "html" in task_lower or "responsive" in task_lower:
            html_code = (
                "<!DOCTYPE html>\n"
                "<html lang=\"en\">\n"
                "<head>\n"
                "    <meta charset=\"UTF-8\">\n"
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                "    <title>NovaPulse Robotics - Autonomous Warehouse Solutions</title>\n"
                "    <link rel=\"stylesheet\" href=\"styles.css\">\n"
                "</head>\n"
                "<body>\n"
                "    <header class=\"hero-section\">\n"
                "        <div class=\"container\">\n"
                "            <h1>NovaPulse Robotics</h1>\n"
                "            <p class=\"page-label\">Company Landing Page</p>\n"
                "            <p class=\"tagline\">Autonomous warehouse robotics solutions for modern enterprise logistics.</p>\n"
                "            <button id=\"cta-btn\" class=\"btn-primary\">Explore Fleet</button>\n"
                "        </div>\n"
                "    </header>\n"
                "    <main class=\"main-content container\">\n"
                "        <section class=\"products-section\">\n"
                "            <h2>Core Products & Services</h2>\n"
                "            <div class=\"grid-cards\">\n"
                "                <div class=\"card\">\n"
                "                    <h3>Fleet Orchestrator</h3>\n"
                "                    <p>Real-time autonomous multi-robot task allocation and route optimization.</p>\n"
                "                </div>\n"
                "                <div class=\"card\">\n"
                "                    <h3>Autonomous AMR-500</h3>\n"
                "                    <p>Heavy payload autonomous mobile robot with sub-centimeter LiDAR navigation.</p>\n"
                "                </div>\n"
                "                <div class=\"card\">\n"
                "                    <h3>Cloud Telemetry API</h3>\n"
                "                    <p>High-throughput telemetry and predictive maintenance streaming platform.</p>\n"
                "                </div>\n"
                "            </div>\n"
                "        </section>\n"
                "        <section class=\"contact-section\">\n"
                "            <h2>Contact Us</h2>\n"
                "            <p>Email: <a href=\"mailto:contact@novapulse.io\">contact@novapulse.io</a></p>\n"
                "        </section>\n"
                "    </main>\n"
                "    <script src=\"script.js\"></script>\n"
                "</body>\n"
                "</html>\n"
            )
            css_code = (
                "/* NovaPulse Robotics - Responsive Landing Page Styles */\n"
                ":root {\n"
                "    --primary-color: #0284c7;\n"
                "    --primary-hover: #0369a1;\n"
                "    --bg-color: #0f172a;\n"
                "    --surface-color: #1e293b;\n"
                "    --text-main: #f8fafc;\n"
                "    --text-muted: #94a3b8;\n"
                "}\n\n"
                "* {\n"
                "    box-sizing: border-box;\n"
                "    margin: 0;\n"
                "    padding: 0;\n"
                "}\n\n"
                "body {\n"
                "    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;\n"
                "    background-color: var(--bg-color);\n"
                "    color: var(--text-main);\n"
                "    line-height: 1.6;\n"
                "}\n\n"
                ".container {\n"
                "    max-width: 1200px;\n"
                "    margin: 0 auto;\n"
                "    padding: 2rem;\n"
                "}\n\n"
                ".hero-section {\n"
                "    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);\n"
                "    padding: 4rem 1rem;\n"
                "    text-align: center;\n"
                "    border-bottom: 1px solid #334155;\n"
                "}\n\n"
                ".hero-section h1 {\n"
                "    font-size: 2.75rem;\n"
                "    color: #38bdf8;\n"
                "    margin-bottom: 1rem;\n"
                "}\n\n"
                ".tagline {\n"
                "    font-size: 1.25rem;\n"
                "    color: var(--text-muted);\n"
                "    margin-bottom: 2rem;\n"
                "}\n\n"
                ".btn-primary {\n"
                "    background-color: var(--primary-color);\n"
                "    color: white;\n"
                "    padding: 0.75rem 1.75rem;\n"
                "    border: none;\n"
                "    border-radius: 6px;\n"
                "    font-size: 1rem;\n"
                "    font-weight: 600;\n"
                "    cursor: pointer;\n"
                "    transition: background 0.2s ease;\n"
                "}\n\n"
                ".btn-primary:hover {\n"
                "    background-color: var(--primary-hover);\n"
                "}\n\n"
                ".grid-cards {\n"
                "    display: grid;\n"
                "    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));\n"
                "    gap: 1.5rem;\n"
                "    margin-top: 1.5rem;\n"
                "}\n\n"
                ".card {\n"
                "    background-color: var(--surface-color);\n"
                "    border: 1px solid #334155;\n"
                "    border-radius: 8px;\n"
                "    padding: 1.5rem;\n"
                "}\n\n"
                ".card h3 {\n"
                "    color: #38bdf8;\n"
                "    margin-bottom: 0.5rem;\n"
                "}\n\n"
                "@media (max-width: 768px) {\n"
                "    .hero-section h1 { font-size: 2rem; }\n"
                "    .container { padding: 1rem; }\n"
                "}\n"
            )
            js_code = (
                "// NovaPulse Robotics - Interactive Landing Page Logic\n"
                "document.addEventListener('DOMContentLoaded', () => {\n"
                "    console.log('NovaPulse Robotics Landing Page Initialized.');\n"
                "    const ctaBtn = document.getElementById('cta-btn');\n"
                "    if (ctaBtn) {\n"
                "        ctaBtn.addEventListener('click', () => {\n"
                "            alert('Explore Fleet: Connecting to NovaPulse Fleet Orchestrator...');\n"
                "        });\n"
                "    }\n"
                "});\n"
            )
            readme_code = (
                "# NovaPulse Robotics - Company Landing Page\n\n"
                "Autonomous warehouse robotics solutions landing page project.\n\n"
                "## Project Files\n"
                "- `index.html`: Responsive landing page HTML structure with semantic tags and company information.\n"
                "- `styles.css`: Modern responsive styles with CSS variables, flex/grid layouts, and media queries.\n"
                "- `script.js`: Interactive client-side JavaScript.\n"
                "- `README.md`: Project documentation and file manifest.\n\n"
                "## Local Inspection\n"
                "Open `index.html` in any modern web browser to view the page.\n"
            )

            steps.append(
                PlanStep(
                    step_id="step-2-create-html",
                    action=PlanStepAction.CREATE_FILE,
                    description="Create semantic index.html landing page",
                    inputs={"workspace_id": request.workspace_id, "relative_path": "index.html", "content": html_code, "overwrite": True},
                )
            )
            steps.append(
                PlanStep(
                    step_id="step-3-create-css",
                    action=PlanStepAction.CREATE_FILE,
                    description="Create responsive stylesheet styles.css",
                    inputs={"workspace_id": request.workspace_id, "relative_path": "styles.css", "content": css_code, "overwrite": True},
                )
            )
            steps.append(
                PlanStep(
                    step_id="step-4-create-js",
                    action=PlanStepAction.CREATE_FILE,
                    description="Create client-side interaction logic script.js",
                    inputs={"workspace_id": request.workspace_id, "relative_path": "script.js", "content": js_code, "overwrite": True},
                )
            )
            steps.append(
                PlanStep(
                    step_id="step-5-create-readme",
                    action=PlanStepAction.CREATE_FILE,
                    description="Create project README.md documentation",
                    inputs={"workspace_id": request.workspace_id, "relative_path": "README.md", "content": readme_code, "overwrite": True},
                )
            )
            steps.append(
                PlanStep(
                    step_id="step-6-validate-project",
                    action=PlanStepAction.VALIDATE_PROJECT,
                    description="Perform controlled multi-file project validation",
                    inputs={
                        "workspace_id": request.workspace_id,
                        "required_files": ["index.html", "styles.css", "script.js", "README.md"],
                        "expected_keywords": ["NovaPulse Robotics"],
                    },
                )
            )
        elif "fastapi" in task_lower or "backend" in task_lower or "api" in task_lower:
            main_code = (
                "from fastapi import FastAPI\n\n"
                "app = FastAPI(title='Student Management System')\n\n"
                "@app.get('/')\n"
                "def root():\n"
                "    return {'status': 'active', 'service': 'students'}\n"
            )
            test_code = (
                "from fastapi.testclient import TestClient\n"
                "from main import app\n\n"
                "client = TestClient(app)\n\n"
                "def test_root():\n"
                "    response = client.get('/')\n"
                "    assert response.status_code == 200\n"
                "    assert response.json() == {'status': 'active', 'service': 'students'}\n"
            )
            steps.append(
                PlanStep(
                    step_id="step-2-create-app",
                    action=PlanStepAction.CREATE_FILE,
                    description="Create FastAPI application entrypoint",
                    inputs={"workspace_id": request.workspace_id, "relative_path": "main.py", "content": main_code, "overwrite": True},
                )
            )
            steps.append(
                PlanStep(
                    step_id="step-3-create-test",
                    action=PlanStepAction.CREATE_FILE,
                    description="Create test suite for FastAPI backend",
                    inputs={"workspace_id": request.workspace_id, "relative_path": "test_main.py", "content": test_code, "overwrite": True},
                )
            )
        elif "git" in task_lower:
            steps.append(
                PlanStep(
                    step_id="step-2-git-status",
                    action=PlanStepAction.GIT_STATUS,
                    description="Check git status",
                    inputs={"workspace_id": request.workspace_id},
                )
            )
        elif "docker" in task_lower:
            steps.append(
                PlanStep(
                    step_id="step-2-docker-avail",
                    action=PlanStepAction.DOCKER_AVAILABILITY,
                    description="Check Docker availability",
                    inputs={"workspace_id": request.workspace_id},
                )
            )
        else:
            # Generic file creation step
            steps.append(
                PlanStep(
                    step_id="step-2-create-file",
                    action=PlanStepAction.CREATE_FILE,
                    description="Create implementation module",
                    inputs={
                        "workspace_id": request.workspace_id,
                        "relative_path": "src/module.py",
                        "content": "# Implementation module\ndef run():\n    return True\n",
                        "overwrite": True,
                    },
                )
            )

        return steps

    def diagnose_failure(
        self,
        request: DevelopmentRequest,
        failed_step: PlanStep,
        failure_evidence: EvidenceSet,
        failure_output: str,
        iteration: int,
    ) -> DiagnosticResult:
        """Diagnose step failure and suggest corrective actions."""
        if self.custom_diagnostic_handler:
            return self.custom_diagnostic_handler(request, failed_step, failure_evidence, failure_output, iteration)

        # Check configured patches
        for patch_path, patch_content in self._recovery_patches.items():
            fix_step = PlanStep(
                step_id=f"step-recovery-{uuid.uuid4().hex[:6]}",
                action=PlanStepAction.UPDATE_FILE,
                description=f"Apply diagnostic patch to '{patch_path}'",
                inputs={"workspace_id": request.workspace_id, "relative_path": patch_path, "content": patch_content},
            )
            return DiagnosticResult(
                can_recover=True,
                diagnosis=f"Detected error in '{patch_path}'. Applying corrective source patch.",
                suggested_fix_steps=[fix_step],
            )

        # Check if validation failed due to missing files or broken references
        if failed_step.action == PlanStepAction.VALIDATE_PROJECT:
            fix_steps = []
            out_lower = failure_output.lower()
            if "styles.css" in out_lower and ("missing" in out_lower or "not found" in out_lower or "empty" in out_lower):
                fix_steps.append(
                    PlanStep(
                        step_id=f"step-recovery-css-{uuid.uuid4().hex[:6]}",
                        action=PlanStepAction.CREATE_FILE,
                        description="Restore missing styles.css",
                        inputs={
                            "workspace_id": request.workspace_id,
                            "relative_path": "styles.css",
                            "content": "/* Recovered styles */\nbody { margin: 0; background: #0f172a; color: #fff; }\n",
                            "overwrite": True,
                        },
                    )
                )
            if "script.js" in out_lower and ("missing" in out_lower or "not found" in out_lower or "empty" in out_lower):
                fix_steps.append(
                    PlanStep(
                        step_id=f"step-recovery-js-{uuid.uuid4().hex[:6]}",
                        action=PlanStepAction.CREATE_FILE,
                        description="Restore missing script.js",
                        inputs={
                            "workspace_id": request.workspace_id,
                            "relative_path": "script.js",
                            "content": "// Recovered script\nconsole.log('Restored');\n",
                            "overwrite": True,
                        },
                    )
                )
            if "readme.md" in out_lower and ("missing" in out_lower or "not found" in out_lower or "empty" in out_lower):
                fix_steps.append(
                    PlanStep(
                        step_id=f"step-recovery-readme-{uuid.uuid4().hex[:6]}",
                        action=PlanStepAction.CREATE_FILE,
                        description="Restore missing README.md",
                        inputs={
                            "workspace_id": request.workspace_id,
                            "relative_path": "README.md",
                            "content": "# Recovered Project Documentation\n\nRecovered project overview.\n",
                            "overwrite": True,
                        },
                    )
                )
            if "novapulse robotics" in out_lower and "missing" in out_lower:
                fix_steps.append(
                    PlanStep(
                        step_id=f"step-recovery-html-{uuid.uuid4().hex[:6]}",
                        action=PlanStepAction.CREATE_FILE,
                        description="Inject required NovaPulse Robotics facts into index.html",
                        inputs={
                            "workspace_id": request.workspace_id,
                            "relative_path": "index.html",
                            "content": "<!DOCTYPE html><html><head><title>NovaPulse Robotics</title><link rel=\"stylesheet\" href=\"styles.css\"></head><body><h1>NovaPulse Robotics</h1><script src=\"script.js\"></script></body></html>",
                            "overwrite": True,
                        },
                    )
                )

            if fix_steps:
                return DiagnosticResult(
                    can_recover=True,
                    diagnosis=f"Diagnosed project validation failure. Created {len(fix_steps)} corrective recovery step(s).",
                    suggested_fix_steps=fix_steps,
                )

        # Default fallback: if test failed and contains syntax/assertion error
        if failed_step.action == PlanStepAction.RUN_TEST:
            return DiagnosticResult(
                can_recover=False,
                diagnosis="Test execution failed and no deterministic patch was matched.",
                reason=f"Test failure in step '{failed_step.step_id}': {failure_output}",
            )

        return DiagnosticResult(
            can_recover=False,
            diagnosis=f"Unrecoverable error in step '{failed_step.step_id}' ({failed_step.action.value}).",
            reason=failure_output,
        )

    def refine_plan(
        self,
        request: DevelopmentRequest,
        plan: DevelopmentPlan,
        diagnostic: DiagnosticResult,
    ) -> DevelopmentPlan:
        """Inject recovery fix steps into the active plan before retrying."""
        if not diagnostic.suggested_fix_steps:
            return plan

        curr_idx = plan.current_step_index
        # Insert fix steps immediately before the current step so they run first, then the current step is retried
        for i, fix_step in enumerate(diagnostic.suggested_fix_steps):
            plan.steps.insert(curr_idx + i, fix_step)

        return plan


class SoftwareDevelopmentCapabilityHandler(BaseCapabilityHandler):
    """
    Registered Capability Handler for 'software_development' capability.
    Allows Executive Twins or Master Orchestrators to invoke SoftwareDevelopmentAgent
    via the SpecialistExecutionEngine boundary.
    """

    capability_name = "software_development"
    required_tool = "command_executor"
    required_params = ["workspace_id", "task"]
    allowed_params = [
        "workspace_id",
        "task",
        "requirements",
        "success_criteria",
        "constraints",
        "max_iterations",
        "max_steps",
        "timeout_seconds",
    ]

    def __init__(self, agent: ISoftwareDevelopmentAgent) -> None:
        self.agent = agent

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        task = str(request.inputs.get("task", request.task))
        requirements = request.inputs.get("requirements", [])
        success_criteria = request.inputs.get("success_criteria", request.success_criteria)
        constraints = request.inputs.get("constraints", request.constraints)
        max_iter = int(request.inputs.get("max_iterations", 5))
        max_steps = int(request.inputs.get("max_steps", 25))
        timeout_sec = float(request.inputs.get("timeout_seconds", 300.0))

        dev_req = DevelopmentRequest(
            request_id=request.delegation_id,
            specialist_id=specialist.specialist_id,
            workspace_id=ws_id,
            task=task,
            requirements=requirements if isinstance(requirements, list) else [],
            success_criteria=success_criteria if isinstance(success_criteria, list) else [],
            constraints=constraints if isinstance(constraints, list) else [],
            security_context=request.security_context,
            max_iterations=max_iter,
            max_steps=max_steps,
            timeout_seconds=timeout_sec,
        )

        dev_res: DevelopmentResult = self.agent.execute_development(dev_req)

        errors = [dev_res.failure_reason] if dev_res.failure_reason else []
        return CapabilityHandlerOutput(
            success=(dev_res.status == DevelopmentStatus.SUCCESS),
            output_text=dev_res.summary,
            facts=dev_res.facts,
            artifacts=dev_res.artifacts,
            errors=errors,
            additional_evidence=dev_res.evidence.items,
        )


class ProjectValidationCapabilityHandler(BaseCapabilityHandler):
    """
    Authoritative Capability Handler for 'project_validation'.
    Performs deterministic, bounded semantic and structural validation of multi-file projects
    strictly via IFileService (no raw OS filesystem calls or arbitrary shell commands).
    """

    capability_name = "project_validation"
    required_tool = "file_service"
    required_params = ["workspace_id"]
    allowed_params = [
        "workspace_id",
        "relative_path",
        "path",
        "required_files",
        "expected_keywords",
        "check_cross_references",
        "task",
    ]

    def __init__(self, file_service: IFileService) -> None:
        self.file_service = file_service

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        workspace_id = str(request.inputs.get("workspace_id", "default"))
        task_str = str(request.inputs.get("task", request.task or "")).lower()

        # Determine required files based on inputs or task context
        explicit_required = request.inputs.get("required_files")
        if isinstance(explicit_required, list) and explicit_required:
            required_files = [str(f) for f in explicit_required]
        elif "landing page" in task_str or "website" in task_str or "html" in task_str or "responsive" in task_str:
            required_files = ["index.html", "styles.css", "script.js", "README.md"]
        else:
            path_param = request.inputs.get("relative_path") or request.inputs.get("path")
            if path_param:
                required_files = [str(path_param)]
            else:
                required_files = ["index.html", "styles.css", "script.js", "README.md"]

        expected_keywords = request.inputs.get("expected_keywords", ["NovaPulse Robotics"])
        if not isinstance(expected_keywords, list):
            expected_keywords = [str(expected_keywords)]

        errors: List[str] = []
        validated_artifacts: List[str] = []
        evidence_items: List[Any] = []
        facts: List[FactItem] = []
        file_contents: Dict[str, str] = {}

        if hasattr(self.file_service, "get_file_service"):
            svc = self.file_service.get_file_service(workspace_id)
        else:
            svc = self.file_service

        if not svc:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"VALIDATION_FAILED: File service for workspace '{workspace_id}' not found.",
                errors=[f"File service for workspace '{workspace_id}' not found."],
            )

        # 1. Existence and non-empty checks for all required files
        for rel_file in required_files:
            read_res = svc.read_file(rel_file)
            if not read_res.success:
                errors.append(f"Missing required file: '{rel_file}' ({read_res.error_message or 'File not found'})")
                continue

            content = read_res.content or ""
            if len(content.strip()) == 0:
                errors.append(f"Required file '{rel_file}' is empty.")
                continue

            file_contents[rel_file] = content
            validated_artifacts.append(rel_file)

            mime = (
                "text/html"
                if rel_file.endswith(".html")
                else "text/css"
                if rel_file.endswith(".css")
                else "application/javascript"
                if rel_file.endswith(".js")
                else "text/markdown"
                if rel_file.endswith(".md")
                else "text/plain"
            )
            size_b = read_res.metadata.size_bytes if read_res.metadata else len(content.encode('utf-8'))
            checksum = read_res.metadata.checksum_sha256 if read_res.metadata else None
            evidence_items.append(
                ArtifactEvidence(
                    evidence_id=f"ev_art_val_{uuid.uuid4().hex[:8]}",
                    artifact_uri=f"workspace://{workspace_id}/{rel_file}",
                    mime_type=mime,
                    checksum_sha256=checksum,
                    description=f"Validated project artifact: {rel_file} ({size_b} bytes)",
                )
            )

        # 2. Semantic structure & cross-reference validation for index.html
        if "index.html" in file_contents:
            html_content = file_contents["index.html"]
            html_lower = html_content.lower()

            if "<!doctype html>" not in html_lower and "<html" not in html_lower:
                errors.append("index.html lacks valid HTML document structure (missing DOCTYPE or <html>).")
            if "<body" not in html_lower or "</body>" not in html_lower:
                errors.append("index.html lacks <body> tag structure.")

            if "styles.css" in required_files or "styles.css" in file_contents:
                if "styles.css" not in html_content:
                    errors.append("index.html does not link to 'styles.css' (missing <link rel=\"stylesheet\" href=\"styles.css\">).")

            if "script.js" in required_files or "script.js" in file_contents:
                if "script.js" not in html_content:
                    errors.append("index.html does not reference 'script.js' (missing <script src=\"script.js\"></script>).")

            for kw in expected_keywords:
                if kw.lower() not in html_lower:
                    errors.append(f"index.html is missing required company fact/keyword: '{kw}'.")

        # 3. CSS syntax/rules check for styles.css
        if "styles.css" in file_contents:
            css_content = file_contents["styles.css"]
            if "{" not in css_content or "}" not in css_content:
                errors.append("styles.css does not contain valid CSS rules/declarations.")

        # 4. JS syntax/behavior check for script.js
        if "script.js" in file_contents:
            js_content = file_contents["script.js"]
            if len(js_content.strip()) < 10:
                errors.append("script.js content is too short to be functional.")

        # 5. README check
        if "README.md" in file_contents:
            readme_content = file_contents["README.md"]
            if len(readme_content.strip()) < 20:
                errors.append("README.md does not contain adequate project documentation.")

        # Aggregate Result
        if errors:
            failure_msg = f"Project validation failed with {len(errors)} error(s): " + "; ".join(errors)
            evidence_items.append(
                ExecutionLogEvidence(
                    evidence_id=f"ev_log_val_{uuid.uuid4().hex[:8]}",
                    execution_id=request.delegation_id,
                    log_snippet=failure_msg,
                    exit_code=1,
                    description="Project validation failure log",
                )
            )
            return CapabilityHandlerOutput(
                success=False,
                output_text=failure_msg,
                facts=facts,
                artifacts=validated_artifacts,
                errors=errors,
                additional_evidence=evidence_items,
            )

        # Success Output
        success_msg = (
            f"Project validation passed successfully for workspace '{workspace_id}'. "
            f"Validated {len(validated_artifacts)} files ({', '.join(validated_artifacts)}). "
            f"All cross-references and required company information verified."
        )

        facts.append(
            FactItem(
                statement=f"Project validation passed for workspace '{workspace_id}': all required files verified.",
                state=FactState.FACT,
                source="project_validation_handler",
            )
        )

        verif_ev = VerificationEvidence(
            evidence_id=f"ev_verif_val_{uuid.uuid4().hex[:8]}",
            verifier_id="ProjectValidationCapabilityHandler",
            verified_status="VERIFIED",
            description=success_msg,
        )
        evidence_items.append(verif_ev)

        return CapabilityHandlerOutput(
            success=True,
            output_text=success_msg,
            facts=facts,
            artifacts=validated_artifacts,
            errors=[],
            additional_evidence=evidence_items,
        )


class SoftwareValidationCapabilityHandler(ProjectValidationCapabilityHandler):
    """Alias handler registered for 'software_validation'."""
    capability_name = "software_validation"


class DevTestSoftwareDevelopmentAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Sets up an integrated software development test environment
    wiring all controlled capabilities (Files, Command Execution, Git, Docker, Workspace)
    into SpecialistExecutionEngine.
    """

    def __init__(
        self,
        base_temp_dir: str = "",
        use_mock_docker: bool = True,
    ) -> None:
        self.workspace_adapter = DevTestWorkspaceAdapter(base_temp_dir=base_temp_dir)
        self.file_adapter = DevFileServiceAdapter(workspace_adapter=self.workspace_adapter)
        self.command_adapter = DevCommandExecutorAdapter(workspace_adapter=self.workspace_adapter)
        self.git_adapter = DevGitServiceAdapter(workspace_adapter=self.workspace_adapter)
        self.docker_adapter = DevDockerServiceAdapter(
            workspace_adapter=self.workspace_adapter, use_mock=use_mock_docker
        )

    def register_all_handlers(self, engine: SpecialistExecutionEngine) -> None:
        """Register all controlled capability handlers into SpecialistExecutionEngine."""
        # Files API
        engine.register_handler(FileCreateCapabilityHandler(self.file_adapter))
        engine.register_handler(FileReadCapabilityHandler(self.file_adapter))
        engine.register_handler(FileUpdateCapabilityHandler(self.file_adapter))
        engine.register_handler(FileDeleteCapabilityHandler(self.file_adapter))
        engine.register_handler(FileListCapabilityHandler(self.file_adapter))

        # Project / Software Validation
        engine.register_handler(ProjectValidationCapabilityHandler(self.file_adapter))
        engine.register_handler(SoftwareValidationCapabilityHandler(self.file_adapter))

        # Command Execution
        engine.register_handler(BuildCapabilityHandler(self.command_adapter))
        engine.register_handler(TestCapabilityHandler(self.command_adapter))
        engine.register_handler(LintCapabilityHandler(self.command_adapter))
        engine.register_handler(TypecheckCapabilityHandler(self.command_adapter))

        # Workspace Builder
        engine.register_handler(WorkspaceBuildCapabilityHandler(self.workspace_adapter))

        # Git Integration
        engine.register_handler(GitStatusCapabilityHandler(self.git_adapter))
        engine.register_handler(GitBranchCapabilityHandler(self.git_adapter))
        engine.register_handler(GitDiffCapabilityHandler(self.git_adapter))
        engine.register_handler(GitStageCapabilityHandler(self.git_adapter))
        engine.register_handler(GitUnstageCapabilityHandler(self.git_adapter))
        engine.register_handler(GitCommitCapabilityHandler(self.git_adapter))
        engine.register_handler(GitLogCapabilityHandler(self.git_adapter))

        # Docker Integration
        engine.register_handler(DockerAvailabilityCapabilityHandler(self.docker_adapter))
        engine.register_handler(DockerBuildCapabilityHandler(self.docker_adapter))
        engine.register_handler(DockerRunCapabilityHandler(self.docker_adapter))
        engine.register_handler(DockerInspectCapabilityHandler(self.docker_adapter))
        engine.register_handler(DockerStopCapabilityHandler(self.docker_adapter))
        engine.register_handler(DockerRemoveCapabilityHandler(self.docker_adapter))

