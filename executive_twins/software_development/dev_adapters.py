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
from executive_twins.schemas.common import FactItem, FactState, SpecialistStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import EvidenceCategory, EvidenceSet
from executive_twins.schemas.specialist import Capability, RegistryProvenance, SpecialistMetadata
from executive_twins.software_development.interfaces import (
    IDevelopmentPlanner,
    ISoftwareDevelopmentAgent,
)
from executive_twins.software_development.models import (
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

        return DevelopmentPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
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
        if "fastapi" in task_lower or "backend" in task_lower or "api" in task_lower:
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
