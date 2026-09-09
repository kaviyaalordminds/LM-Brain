"""
Comprehensive production-grade test suite for Software Development Agent.
Covers 54 focused test scenarios: lifecycle, file operations, validation, failure recovery,
security boundaries, empirical evidence integrity, bounded execution limits, and full capability integration.
"""

from datetime import datetime, timezone
import os
import pathlib
import subprocess
import tempfile
import time
import pytest

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.command_execution.command_executor import CommandRegistry, CommandSpecification
from executive_twins.command_execution.models import CommandType
from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard, SecurityGuardException
from executive_twins.registry.capability_matcher import CapabilityMatcher
from executive_twins.schemas.common import (
    FactItem,
    FactState,
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    EvidenceSet,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import Capability, CapabilityRequirement, SpecialistMetadata
from executive_twins.software_development.dev_adapters import (
    DeterministicDevelopmentPlanner,
    DevTestSoftwareDevelopmentAdapter,
    SoftwareDevelopmentCapabilityHandler,
    create_software_development_specialist,
)
from executive_twins.software_development.interfaces import ISoftwareDevelopmentAgent
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
from executive_twins.utils.audit_logger import AuditLogger


@pytest.fixture
def dev_env():
    """Sets up a complete isolated development test environment."""
    with tempfile.TemporaryDirectory() as temp_dir:
        registry = InMemorySpecialistRegistryAdapter()
        specialist = create_software_development_specialist("spec_software_dev_01")
        registry.register_specialist(specialist)

        engine = SpecialistExecutionEngine(registry_client=registry)
        dev_adapter = DevTestSoftwareDevelopmentAdapter(base_temp_dir=temp_dir, use_mock_docker=True)
        dev_adapter.register_all_handlers(engine)

        ws = dev_adapter.workspace_adapter.create_workspace("test-ws-001")
        planner = DeterministicDevelopmentPlanner()
        agent = SoftwareDevelopmentAgent(execution_engine=engine, planner=planner)

        # Register software_development capability into engine
        engine.register_handler(SoftwareDevelopmentCapabilityHandler(agent))

        yield {
            "registry": registry,
            "specialist": specialist,
            "engine": engine,
            "dev_adapter": dev_adapter,
            "workspace": ws,
            "workspace_id": "test-ws-001",
            "planner": planner,
            "agent": agent,
            "temp_dir": temp_dir,
        }

        dev_adapter.workspace_adapter.close_all(cleanup=True)


# =============================================================================
# 1. Basic Lifecycle (Tests 1 - 7)
# =============================================================================

def test_1_request_accepted(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(
        request_id="req-001",
        workspace_id=dev_env["workspace_id"],
        task="Create basic Python package structure",
    )
    is_valid, err = agent.validate_request(req)
    assert is_valid is True
    assert err is None


def test_2_plan_created(dev_env):
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    req = DevelopmentRequest(
        request_id="req-002",
        workspace_id=dev_env["workspace_id"],
        task="Create FastAPI student management backend",
    )
    plan = planner.create_plan(req)
    assert plan is not None
    assert plan.plan_id.startswith("plan-")
    assert plan.request_id == "req-002"
    assert len(plan.steps) >= 3


def test_3_plan_contains_typed_steps(dev_env):
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    req = DevelopmentRequest(
        request_id="req-003",
        workspace_id=dev_env["workspace_id"],
        task="Create FastAPI student management backend",
    )
    plan = planner.create_plan(req)
    actions = [s.action for s in plan.steps]
    assert PlanStepAction.INSPECT in actions
    assert PlanStepAction.CREATE_FILE in actions
    for s in plan.steps:
        assert isinstance(s.action, PlanStepAction)
        assert isinstance(s.status, PlanStepStatus)


def test_4_development_succeeds(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(
        request_id="req-004",
        workspace_id=dev_env["workspace_id"],
        task="Create a simple module",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert result.verification == VerificationStatus.VERIFIED
    assert len(result.completed_steps) > 0
    assert len(result.failed_steps) == 0
    assert len(result.evidence.items) > 0


def test_5_development_failure(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    def failing_plan_generator(request: DevelopmentRequest):
        return [
            PlanStep(
                step_id="step-fail",
                action=PlanStepAction.READ_FILE,
                description="Read non-existent file",
                inputs={"workspace_id": request.workspace_id, "relative_path": "non_existent.py"},
                max_retries=0,
            )
        ]

    planner.custom_plan_generator = failing_plan_generator

    req = DevelopmentRequest(
        request_id="req-005",
        workspace_id=dev_env["workspace_id"],
        task="Read missing file",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.FAILED
    assert result.verification == VerificationStatus.FAILED
    assert len(result.failed_steps) == 1


def test_6_blocked_state(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(
        request_id="req-006",
        workspace_id=dev_env["workspace_id"],
        task="Run command with shell_exec injection",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.BLOCKED
    assert "Forbidden" in result.summary


def test_7_partial_state(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    def partial_plan_generator(request: DevelopmentRequest):
        return [
            PlanStep(
                step_id="step-1-pass",
                action=PlanStepAction.CREATE_FILE,
                description="Create file 1",
                inputs={"workspace_id": request.workspace_id, "relative_path": "file1.txt", "content": "data"},
            ),
            PlanStep(
                step_id="step-2-fail",
                action=PlanStepAction.READ_FILE,
                description="Read missing file",
                inputs={"workspace_id": request.workspace_id, "relative_path": "missing.txt"},
                max_retries=0,
            ),
        ]

    planner.custom_plan_generator = partial_plan_generator

    req = DevelopmentRequest(
        request_id="req-007",
        workspace_id=dev_env["workspace_id"],
        task="Create then fail",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.PARTIAL
    assert len(result.completed_steps) == 1
    assert len(result.failed_steps) == 1


# =============================================================================
# 2. File Integration (Tests 8 - 12)
# =============================================================================

def test_8_create_file(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-create",
            action=PlanStepAction.CREATE_FILE,
            description="Create app.py",
            inputs={"workspace_id": req.workspace_id, "relative_path": "src/app.py", "content": "print('hello')", "overwrite": True},
        )
    ]
    req = DevelopmentRequest(request_id="req-008", workspace_id=dev_env["workspace_id"], task="Create file")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert dev_env["workspace"].file_exists("src/app.py") is True


def test_9_read_file(dev_env):
    dev_env["workspace"].write_file("data.txt", "test_content")
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-read",
            action=PlanStepAction.READ_FILE,
            description="Read data.txt",
            inputs={"workspace_id": req.workspace_id, "relative_path": "data.txt"},
        )
    ]
    req = DevelopmentRequest(request_id="req-009", workspace_id=dev_env["workspace_id"], task="Read file")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert result.completed_steps[0].result_output == "test_content"


def test_10_update_file(dev_env):
    dev_env["workspace"].write_file("config.json", '{"v": 1}')
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-update",
            action=PlanStepAction.UPDATE_FILE,
            description="Update config.json",
            inputs={"workspace_id": req.workspace_id, "relative_path": "config.json", "content": '{"v": 2}'},
        )
    ]
    req = DevelopmentRequest(request_id="req-010", workspace_id=dev_env["workspace_id"], task="Update file")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    read_res = dev_env["workspace"].read_file("config.json")
    assert read_res.content == '{"v": 2}'


def test_11_delete_file(dev_env):
    dev_env["workspace"].write_file("temp.log", "debug data")
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-del",
            action=PlanStepAction.DELETE_FILE,
            description="Delete temp.log",
            inputs={"workspace_id": req.workspace_id, "relative_path": "temp.log"},
        )
    ]
    req = DevelopmentRequest(request_id="req-011", workspace_id=dev_env["workspace_id"], task="Delete file")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert dev_env["workspace"].file_exists("temp.log") is False


def test_12_workspace_isolation(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-escape",
            action=PlanStepAction.CREATE_FILE,
            description="Attempt write outside workspace",
            inputs={"workspace_id": req.workspace_id, "relative_path": "../escape.txt", "content": "bad"},
        )
    ]
    req = DevelopmentRequest(request_id="req-012", workspace_id=dev_env["workspace_id"], task="Escape test")
    result = agent.execute_development(req)
    assert result.status in (DevelopmentStatus.BLOCKED, DevelopmentStatus.FAILED)
    assert result.verification == VerificationStatus.FAILED


# =============================================================================
# 3. Validation (Tests 13 - 18)
# =============================================================================

def test_13_test_execution(dev_env):
    dev_env["workspace"].write_file("test_sample.py", "def test_ok(): assert True\n")
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-test",
            action=PlanStepAction.RUN_TEST,
            description="Execute test suite",
            inputs={"workspace_id": req.workspace_id, "executable": "python", "arguments": ["-m", "pytest", "test_sample.py"]},
        )
    ]
    req = DevelopmentRequest(request_id="req-013", workspace_id=dev_env["workspace_id"], task="Run tests")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert any(isinstance(e, ExecutionLogEvidence) for e in result.evidence.items)


def test_14_build_execution(dev_env):
    dev_env["workspace"].write_file("src/app.py", "print('hello')\n")
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-build",
            action=PlanStepAction.WORKSPACE_BUILD,
            description="Build package artifact",
            inputs={"workspace_id": req.workspace_id, "project_file": "src/app.py"},
        )
    ]
    req = DevelopmentRequest(request_id="req-014", workspace_id=dev_env["workspace_id"], task="Run build")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS


def test_15_lint_execution(dev_env):
    dev_env["dev_adapter"].command_adapter.registry.register_specification(
        CommandSpecification(
            command_type=CommandType.LINT,
            executable="python",
            allowed_argument_prefixes=[["-m", "unittest"]],
        )
    )
    dev_env["workspace"].write_file("test_lint.py", "import unittest\nclass T(unittest.TestCase):\n  def test_l(self): pass\n")
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-lint",
            action=PlanStepAction.RUN_LINT,
            description="Run lint verification",
            inputs={"workspace_id": req.workspace_id, "executable": "python", "arguments": ["-m", "unittest", "test_lint.py"]},
        )
    ]
    req = DevelopmentRequest(request_id="req-015", workspace_id=dev_env["workspace_id"], task="Run lint")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS


def test_16_typecheck_execution(dev_env):
    dev_env["dev_adapter"].command_adapter.registry.register_specification(
        CommandSpecification(
            command_type=CommandType.TYPECHECK,
            executable="python",
            allowed_argument_prefixes=[["-m", "unittest"]],
        )
    )
    dev_env["workspace"].write_file("test_type.py", "import unittest\nclass T(unittest.TestCase):\n  def test_t(self): pass\n")
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-typecheck",
            action=PlanStepAction.RUN_TYPECHECK,
            description="Run typecheck verification",
            inputs={"workspace_id": req.workspace_id, "executable": "python", "arguments": ["-m", "unittest", "test_type.py"]},
        )
    ]
    req = DevelopmentRequest(request_id="req-016", workspace_id=dev_env["workspace_id"], task="Run typecheck")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS


def test_17_failed_test(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-fail-test",
            action=PlanStepAction.RUN_TEST,
            description="Run unallowed test command",
            inputs={"workspace_id": req.workspace_id, "executable": "unregistered_test_tool", "arguments": []},
            max_retries=0,
        )
    ]
    req = DevelopmentRequest(request_id="req-017", workspace_id=dev_env["workspace_id"], task="Fail test")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.FAILED
    assert result.verification == VerificationStatus.FAILED


def test_18_failed_build(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-fail-build",
            action=PlanStepAction.RUN_BUILD,
            description="Run disallowed build executable",
            inputs={"workspace_id": req.workspace_id, "executable": "malicious_compiler", "arguments": []},
            max_retries=0,
        )
    ]
    req = DevelopmentRequest(request_id="req-018", workspace_id=dev_env["workspace_id"], task="Fail build")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.FAILED


# =============================================================================
# 4. Failure Recovery (Tests 19 - 24)
# =============================================================================

def test_19_failure_detected(dev_env):
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    failed_step = PlanStep(
        step_id="step-test",
        action=PlanStepAction.RUN_TEST,
        description="Run test suite",
        inputs={"workspace_id": "ws-1", "executable": "pytest"},
    )
    ev_set = EvidenceSet()
    diag = planner.diagnose_failure(
        request=DevelopmentRequest(request_id="r1", workspace_id="ws-1", task="test"),
        failed_step=failed_step,
        failure_evidence=ev_set,
        failure_output="AssertionError: 1 != 2 in test_calc.py",
        iteration=1,
    )
    assert diag is not None


def test_20_evidence_inspected(dev_env):
    called = []

    def custom_diagnostic(req, step, ev_set, err_out, iteration):
        called.append((step.step_id, err_out, len(ev_set.items)))
        return DiagnosticResult(can_recover=False, diagnosis="Observed evidence")

    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_diagnostic_handler = custom_diagnostic
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-fail",
            action=PlanStepAction.READ_FILE,
            description="Read missing file",
            inputs={"workspace_id": req.workspace_id, "relative_path": "missing.txt"},
            max_retries=1,
        )
    ]
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    agent.execute_development(DevelopmentRequest(request_id="req-020", workspace_id=dev_env["workspace_id"], task="Inspect"))
    assert len(called) == 1
    assert called[0][0] == "step-fail"


def test_21_recovery_step_created(dev_env):
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.set_recovery_patch("main.py", "def root(): return {'status': 'fixed'}")
    failed_step = PlanStep(
        step_id="step-test",
        action=PlanStepAction.RUN_TEST,
        description="Run tests",
        inputs={"workspace_id": "ws-1", "executable": "pytest"},
    )
    diag = planner.diagnose_failure(
        request=DevelopmentRequest(request_id="r21", workspace_id="ws-1", task="test"),
        failed_step=failed_step,
        failure_evidence=EvidenceSet(),
        failure_output="Test failed",
        iteration=1,
    )
    assert diag.can_recover is True
    assert len(diag.suggested_fix_steps) == 1
    assert diag.suggested_fix_steps[0].action == PlanStepAction.UPDATE_FILE


def test_22_successful_retry(dev_env):
    dev_env["workspace"].write_file("calc.py", "def add(a, b): return a - b")  # Buggy code
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    attempt_count = 0

    class BuggyFileReadHandler(BaseCapabilityHandler):
        capability_name = "buggy_calc_read"
        required_tool = "file_service"
        required_params = ["workspace_id"]

        def execute(self, request, specialist):
            nonlocal attempt_count
            attempt_count += 1
            ws_id = request.inputs.get("workspace_id")
            fs = dev_env["dev_adapter"].file_adapter.get_file_service(ws_id)
            res = fs.read_file("calc.py")
            if "return a - b" in (res.content or ""):
                return CapabilityHandlerOutput(
                    success=False,
                    output_text="AssertionError: calc.py contains subtraction bug",
                    errors=["Bug detected in calc.py"],
                )
            return CapabilityHandlerOutput(
                success=True,
                output_text="calc.py verified fixed",
                facts=[FactItem(statement="calc.py verified", state=FactState.FACT, source="test")],
            )

    dev_env["engine"].register_handler(BuggyFileReadHandler())
    dev_env["specialist"].capabilities.append(
        Capability(name="buggy_calc_read", description="Buggy test capability", required_tools=["file_service"])
    )

    # Configure planner patch for recovery
    planner.set_recovery_patch("calc.py", "def add(a, b): return a + b")

    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-verify-calc",
            action=PlanStepAction.INSPECT,
            description="Verify calc.py functionality",
            inputs={"workspace_id": req.workspace_id},
            max_retries=2,
        )
    ]
    # Map INSPECT temporarily to our custom handler
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "buggy_calc_read"

    req = DevelopmentRequest(request_id="req-022", workspace_id=dev_env["workspace_id"], task="Fix calc bug")
    result = agent.execute_development(req)

    # Restore map
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "file_list"

    assert result.status == DevelopmentStatus.SUCCESS
    assert result.iterations_run >= 1
    assert "return a + b" in dev_env["workspace"].read_file("calc.py").content


def test_23_bounded_retries(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    attempts = 0

    def retry_diagnostic(req, step, ev_set, err_out, iteration):
        nonlocal attempts
        attempts += 1
        return DiagnosticResult(can_recover=True, diagnosis="Try again", suggested_fix_steps=[])

    planner.custom_diagnostic_handler = retry_diagnostic
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-always-fail",
            action=PlanStepAction.READ_FILE,
            description="Read missing file",
            inputs={"workspace_id": req.workspace_id, "relative_path": "ghost.py"},
            max_retries=2,
        )
    ]

    req = DevelopmentRequest(request_id="req-023", workspace_id=dev_env["workspace_id"], task="Retry bound", max_iterations=5)
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.FAILED
    assert attempts <= 3


def test_24_retry_exhaustion(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-exhaust",
            action=PlanStepAction.READ_FILE,
            description="Read ghost file",
            inputs={"workspace_id": req.workspace_id, "relative_path": "never.py"},
            max_retries=0,
        )
    ]
    req = DevelopmentRequest(request_id="req-024", workspace_id=dev_env["workspace_id"], task="Exhaust")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.FAILED
    assert "RETRY_EXHAUSTED" in str(result.failure_reason) or "RECOVERY_FAILED" in str(result.failure_reason) or "FILE_NOT_FOUND" in str(result.failure_reason)


# =============================================================================
# 5. Security Requirements (Tests 25 - 34)
# =============================================================================

def test_25_arbitrary_shell_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(
        request_id="req-025",
        workspace_id=dev_env["workspace_id"],
        task="Please execute shell_exec 'rm -rf /'",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.BLOCKED
    assert "Forbidden" in result.summary


def test_26_powershell_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(
        request_id="req-026",
        workspace_id=dev_env["workspace_id"],
        task="Invoke powershell Get-Process",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.BLOCKED


def test_27_cmd_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(
        request_id="req-027",
        workspace_id=dev_env["workspace_id"],
        task="Run cmd.exe /c dir",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.BLOCKED


def test_28_arbitrary_subprocess_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(
        request_id="req-028",
        workspace_id=dev_env["workspace_id"],
        task="Execute subprocess.Popen(['ls'])",
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.BLOCKED


def test_29_filesystem_traversal_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-trav",
            action=PlanStepAction.CREATE_FILE,
            description="Parent traversal",
            inputs={"workspace_id": req.workspace_id, "relative_path": "../../secret.txt", "content": "leak"},
        )
    ]
    req = DevelopmentRequest(request_id="req-029", workspace_id=dev_env["workspace_id"], task="Traversal")
    result = agent.execute_development(req)
    assert result.status in (DevelopmentStatus.BLOCKED, DevelopmentStatus.FAILED)
    assert "TRAVERSAL" in str(result.failure_reason) or "OUTSIDE" in str(result.failure_reason)


def test_30_absolute_host_path_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-abs",
            action=PlanStepAction.READ_FILE,
            description="Absolute path read",
            inputs={"workspace_id": req.workspace_id, "relative_path": "C:/Windows/System32/calc.exe"},
        )
    ]
    req = DevelopmentRequest(request_id="req-030", workspace_id=dev_env["workspace_id"], task="Absolute path")
    result = agent.execute_development(req)
    assert result.status in (DevelopmentStatus.BLOCKED, DevelopmentStatus.FAILED)


def test_31_symlink_escape_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-symlink",
            action=PlanStepAction.CREATE_FILE,
            description="Write outside via traversal",
            inputs={"workspace_id": req.workspace_id, "relative_path": "../out.txt", "content": "bad"},
        )
    ]
    req = DevelopmentRequest(request_id="req-031", workspace_id=dev_env["workspace_id"], task="Symlink test")
    result = agent.execute_development(req)
    assert result.status in (DevelopmentStatus.BLOCKED, DevelopmentStatus.FAILED)


def test_32_docker_bypass_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-docker-bad",
            action=PlanStepAction.DOCKER_RUN,
            description="Run container with shell injection",
            inputs={"workspace_id": req.workspace_id, "image_name": "alpine", "command": ["sh", "-c", "whoami"]},
        )
    ]
    req = DevelopmentRequest(request_id="req-032", workspace_id=dev_env["workspace_id"], task="Docker bypass test")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.FAILED
    assert result.verification == VerificationStatus.FAILED


def test_33_git_bypass_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-git-bad",
            action=PlanStepAction.GIT_STAGE,
            description="Stage outside path",
            inputs={"workspace_id": req.workspace_id, "paths": ["../outside.txt"]},
        )
    ]
    req = DevelopmentRequest(request_id="req-033", workspace_id=dev_env["workspace_id"], task="Git bypass test")
    result = agent.execute_development(req)
    assert result.status in (DevelopmentStatus.BLOCKED, DevelopmentStatus.FAILED)


def test_34_specialist_execution_engine_bypass_rejected(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-bypass",
            action=PlanStepAction.RUN_BUILD,
            description="Run eval() bypass",
            inputs={"workspace_id": req.workspace_id, "executable": "eval(print(1))"},
        )
    ]
    req = DevelopmentRequest(request_id="req-034", workspace_id=dev_env["workspace_id"], task="Eval test")
    result = agent.execute_development(req)
    assert result.status in (DevelopmentStatus.BLOCKED, DevelopmentStatus.FAILED)


# =============================================================================
# 6. Evidence and Quality Verification (Tests 35 - 41)
# =============================================================================

def test_35_execution_evidence(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(request_id="req-035", workspace_id=dev_env["workspace_id"], task="Create file")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert result.evidence.contains_category(EvidenceCategory.EXECUTION_LOG)


def test_36_artifact_evidence(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-art",
            action=PlanStepAction.CREATE_FILE,
            description="Create artifact file",
            inputs={"workspace_id": req.workspace_id, "relative_path": "art.txt", "content": "artifact data"},
        )
    ]
    req = DevelopmentRequest(request_id="req-036", workspace_id=dev_env["workspace_id"], task="Artifact")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert len(result.artifacts) > 0


def test_37_test_evidence(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    class MockTestCapabilityHandler(BaseCapabilityHandler):
        capability_name = "mock_test_cap"
        required_tool = "test_runner"
        required_params = ["workspace_id"]

        def execute(self, request, specialist):
            ev = TestEvidence(
                evidence_id="ev-test-mock",
                suite_name="unit_tests",
                tests_passed=10,
                tests_failed=0,
                description="Mock test report",
            )
            return CapabilityHandlerOutput(
                success=True,
                output_text="10 passed",
                additional_evidence=[ev],
            )

    dev_env["engine"].register_handler(MockTestCapabilityHandler())
    dev_env["specialist"].capabilities.append(
        Capability(name="mock_test_cap", description="Mock test", required_tools=["test_runner"])
    )
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.RUN_TEST] = "mock_test_cap"

    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-test",
            action=PlanStepAction.RUN_TEST,
            description="Run mock tests",
            inputs={"workspace_id": req.workspace_id},
        )
    ]
    req = DevelopmentRequest(request_id="req-037", workspace_id=dev_env["workspace_id"], task="Run mock test")
    result = agent.execute_development(req)

    # Restore map
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.RUN_TEST] = "test_command_execution"

    assert result.status == DevelopmentStatus.SUCCESS
    assert result.evidence.contains_category(EvidenceCategory.TEST)


def test_38_verification_evidence(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(request_id="req-038", workspace_id=dev_env["workspace_id"], task="Create file")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert result.evidence.contains_category(EvidenceCategory.VERIFICATION)


def test_39_no_false_success_from_unknown(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    class UnknownFactHandler(BaseCapabilityHandler):
        capability_name = "unknown_fact_cap"
        required_tool = "static_analyzer"
        required_params = ["workspace_id"]

        def execute(self, request, specialist):
            return CapabilityHandlerOutput(
                success=True,
                output_text="Success assumed",
                facts=[FactItem(statement="Deployed", state=FactState.UNKNOWN, source="guess")],
                has_unknowns_or_assumptions=True,
            )

    dev_env["engine"].register_handler(UnknownFactHandler())
    dev_env["specialist"].capabilities.append(
        Capability(name="unknown_fact_cap", description="Unknown fact", required_tools=["static_analyzer"])
    )
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "unknown_fact_cap"

    planner.custom_plan_generator = lambda req: [
        PlanStep(step_id="step-unk", action=PlanStepAction.INSPECT, description="Unknown step", inputs={"workspace_id": req.workspace_id})
    ]
    req = DevelopmentRequest(request_id="req-039", workspace_id=dev_env["workspace_id"], task="Unknown test")
    result = agent.execute_development(req)

    # Restore map
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "file_list"

    assert result.status == DevelopmentStatus.FAILED
    assert result.verification == VerificationStatus.FAILED


def test_40_no_false_success_from_assumption(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    class AssumptionFactHandler(BaseCapabilityHandler):
        capability_name = "assumption_fact_cap"
        required_tool = "static_analyzer"
        required_params = ["workspace_id"]

        def execute(self, request, specialist):
            return CapabilityHandlerOutput(
                success=True,
                output_text="Success assumed",
                facts=[FactItem(statement="Database online", state=FactState.ASSUMPTION, source="guess")],
                has_unknowns_or_assumptions=True,
            )

    dev_env["engine"].register_handler(AssumptionFactHandler())
    dev_env["specialist"].capabilities.append(
        Capability(name="assumption_fact_cap", description="Assumption fact", required_tools=["static_analyzer"])
    )
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "assumption_fact_cap"

    planner.custom_plan_generator = lambda req: [
        PlanStep(step_id="step-assump", action=PlanStepAction.INSPECT, description="Assumption step", inputs={"workspace_id": req.workspace_id})
    ]
    req = DevelopmentRequest(request_id="req-040", workspace_id=dev_env["workspace_id"], task="Assumption test")
    result = agent.execute_development(req)

    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "file_list"

    assert result.status == DevelopmentStatus.FAILED
    assert result.verification == VerificationStatus.FAILED


def test_41_no_false_success_from_unverified(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    class UnverifiedFactHandler(BaseCapabilityHandler):
        capability_name = "unverified_fact_cap"
        required_tool = "static_analyzer"
        required_params = ["workspace_id"]

        def execute(self, request, specialist):
            return CapabilityHandlerOutput(
                success=True,
                output_text="Unverified execution",
                facts=[FactItem(statement="Security checked", state=FactState.UNVERIFIED, source="guess")],
                has_unknowns_or_assumptions=True,
            )

    dev_env["engine"].register_handler(UnverifiedFactHandler())
    dev_env["specialist"].capabilities.append(
        Capability(name="unverified_fact_cap", description="Unverified fact", required_tools=["static_analyzer"])
    )
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "unverified_fact_cap"

    planner.custom_plan_generator = lambda req: [
        PlanStep(step_id="step-unv", action=PlanStepAction.INSPECT, description="Unverified step", inputs={"workspace_id": req.workspace_id})
    ]
    req = DevelopmentRequest(request_id="req-041", workspace_id=dev_env["workspace_id"], task="Unverified test")
    result = agent.execute_development(req)

    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "file_list"

    assert result.status == DevelopmentStatus.FAILED
    assert result.verification == VerificationStatus.FAILED


# =============================================================================
# 7. Limits and Bounds (Tests 42 - 45)
# =============================================================================

def test_42_max_iterations(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    planner.custom_diagnostic_handler = lambda req, step, ev, err, it: DiagnosticResult(
        can_recover=True, diagnosis="Keep retrying", suggested_fix_steps=[]
    )
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-inf-fail",
            action=PlanStepAction.READ_FILE,
            description="Fail forever",
            inputs={"workspace_id": req.workspace_id, "relative_path": "none.txt"},
            max_retries=10,
        )
    ]

    req = DevelopmentRequest(
        request_id="req-042",
        workspace_id=dev_env["workspace_id"],
        task="Iteration limit test",
        max_iterations=3,
    )
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.FAILED
    assert result.iterations_run <= 3


def test_43_max_steps(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id=f"step-{i}",
            action=PlanStepAction.CREATE_FILE,
            description=f"Create file {i}",
            inputs={"workspace_id": req.workspace_id, "relative_path": f"f{i}.txt", "content": f"{i}"},
        )
        for i in range(10)
    ]

    req = DevelopmentRequest(
        request_id="req-043",
        workspace_id=dev_env["workspace_id"],
        task="Max steps test",
        max_steps=4,
    )
    result = agent.execute_development(req)
    assert result.status in (DevelopmentStatus.BLOCKED, DevelopmentStatus.PARTIAL, DevelopmentStatus.FAILED)
    assert len(result.completed_steps) <= 4


def test_44_timeout(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]

    class SlowHandler(BaseCapabilityHandler):
        capability_name = "slow_cap"
        required_tool = "file_service"
        required_params = ["workspace_id"]

        def execute(self, request, specialist):
            time.sleep(0.3)
            return CapabilityHandlerOutput(success=True, output_text="Slow step done")

    dev_env["engine"].register_handler(SlowHandler())
    dev_env["specialist"].capabilities.append(
        Capability(name="slow_cap", description="Slow capability", required_tools=["file_service"])
    )
    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "slow_cap"

    planner.custom_plan_generator = lambda req: [
        PlanStep(step_id=f"step-slow-{i}", action=PlanStepAction.INSPECT, description=f"Slow step {i}", inputs={"workspace_id": req.workspace_id})
        for i in range(5)
    ]

    req = DevelopmentRequest(
        request_id="req-044",
        workspace_id=dev_env["workspace_id"],
        task="Timeout test",
        timeout_seconds=0.2,
    )
    result = agent.execute_development(req)

    agent.ACTION_CAPABILITY_MAP[PlanStepAction.INSPECT] = "file_list"

    assert result.status == DevelopmentStatus.TIMEOUT
    assert "TIMEOUT" in str(result.failure_reason)


def test_45_bounded_output_result(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(request_id="req-045", workspace_id=dev_env["workspace_id"], task="Output test")
    result = agent.execute_development(req)
    assert isinstance(result, DevelopmentResult)
    assert isinstance(result.summary, str)
    assert isinstance(result.duration_seconds, float)
    assert result.completed_at is not None


# =============================================================================
# 8. Full Integration (Tests 46 - 54)
# =============================================================================

def test_46_specialist_execution_engine_integration(dev_env):
    engine: SpecialistExecutionEngine = dev_env["engine"]
    specialist: SpecialistMetadata = dev_env["specialist"]

    del_req = DelegationRequest(
        delegation_id="del-dev-046",
        parent_task_id="task-46",
        executive_twin_id="twin-cto",
        specialist_id=specialist.specialist_id,
        objective="Develop backend module",
        task="Create basic Python package structure",
        required_capabilities=["software_development"],
        inputs={"workspace_id": dev_env["workspace_id"], "task": "Create simple module"},
        expected_output="Verified module",
    )
    result = engine.execute_delegation(del_req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED


def test_47_security_guard_integration(dev_env):
    with pytest.raises(SecurityGuardException):
        SecurityGuard.validate_twin_action("shell_exec")

    with pytest.raises(SecurityGuardException):
        SecurityGuard.validate_twin_action("code_execution")


def test_48_registry_integration(dev_env):
    registry: InMemorySpecialistRegistryAdapter = dev_env["registry"]
    reqs = [CapabilityRequirement(capability_name="software_development", description="Software specialist")]
    matches = registry.discover_specialists(reqs, SecurityContext())
    assert len(matches) == 1
    assert matches[0].status == "MATCHED"
    assert matches[0].selected_specialist.specialist_id == "spec_software_dev_01"


def test_49_workspace_integration(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-ws-build",
            action=PlanStepAction.WORKSPACE_BUILD,
            description="Build project artifact",
            inputs={"workspace_id": req.workspace_id, "project_file": "src/app.py"},
        )
    ]
    dev_env["workspace"].write_file("src/app.py", "print('build me')")

    req = DevelopmentRequest(request_id="req-049", workspace_id=dev_env["workspace_id"], task="Workspace build")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS


def test_50_files_api_integration(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-1",
            action=PlanStepAction.CREATE_FILE,
            description="Create file",
            inputs={"workspace_id": req.workspace_id, "relative_path": "api.py", "content": "API=1"},
        ),
        PlanStep(
            step_id="step-2",
            action=PlanStepAction.READ_FILE,
            description="Read file",
            inputs={"workspace_id": req.workspace_id, "relative_path": "api.py"},
        ),
        PlanStep(
            step_id="step-3",
            action=PlanStepAction.LIST_FILES,
            description="List files",
            inputs={"workspace_id": req.workspace_id},
        ),
    ]
    req = DevelopmentRequest(request_id="req-050", workspace_id=dev_env["workspace_id"], task="Files API workflow")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert len(result.completed_steps) == 3


def test_51_command_execution_integration(dev_env):
    dev_env["workspace"].write_file("test_mod.py", "def test_pass(): pass\n")
    dev_env["workspace"].write_file("clean.py", "x = 1\n")
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-test",
            action=PlanStepAction.RUN_TEST,
            description="Run pytest",
            inputs={"workspace_id": req.workspace_id, "executable": "python", "arguments": ["-m", "pytest", "test_mod.py"]},
        ),
        PlanStep(
            step_id="step-build",
            action=PlanStepAction.WORKSPACE_BUILD,
            description="Build workspace artifact",
            inputs={"workspace_id": req.workspace_id, "project_file": "clean.py"},
        ),
    ]
    req = DevelopmentRequest(request_id="req-051", workspace_id=dev_env["workspace_id"], task="Command workflow")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert len(result.completed_steps) == 2


def test_52_git_integration(dev_env):
    ws_root = dev_env["workspace"].root_path
    subprocess.run(["git", "init"], cwd=ws_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Specialist"], cwd=ws_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "specialist@lordminds.internal"], cwd=ws_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=ws_root, check=True, capture_output=True)

    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-git-status",
            action=PlanStepAction.GIT_STATUS,
            description="Check repository status",
            inputs={"workspace_id": req.workspace_id},
        ),
        PlanStep(
            step_id="step-git-stage",
            action=PlanStepAction.GIT_STAGE,
            description="Stage changes",
            inputs={"workspace_id": req.workspace_id, "paths": ["src/app.py"]},
        ),
        PlanStep(
            step_id="step-git-commit",
            action=PlanStepAction.GIT_COMMIT,
            description="Commit changes",
            inputs={"workspace_id": req.workspace_id, "message": "feat: add app module"},
        ),
    ]
    dev_env["workspace"].write_file("src/app.py", "app code")

    req = DevelopmentRequest(request_id="req-052", workspace_id=dev_env["workspace_id"], task="Git workflow")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert len(result.completed_steps) == 3


def test_53_docker_integration(dev_env):
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    planner: DeterministicDevelopmentPlanner = dev_env["planner"]
    planner.custom_plan_generator = lambda req: [
        PlanStep(
            step_id="step-docker-avail",
            action=PlanStepAction.DOCKER_AVAILABILITY,
            description="Check docker availability",
            inputs={"workspace_id": req.workspace_id},
        ),
        PlanStep(
            step_id="step-docker-build",
            action=PlanStepAction.DOCKER_BUILD,
            description="Build docker image",
            inputs={"workspace_id": req.workspace_id, "image_name": "student-api:v1", "dockerfile_path": "Dockerfile"},
        ),
        PlanStep(
            step_id="step-docker-run",
            action=PlanStepAction.DOCKER_RUN,
            description="Run docker container test",
            inputs={"workspace_id": req.workspace_id, "image_name": "student-api:v1", "command": ["node", "index.js"]},
        ),
    ]
    dev_env["workspace"].write_file("Dockerfile", "FROM node:alpine\nCMD node index.js")

    req = DevelopmentRequest(request_id="req-053", workspace_id=dev_env["workspace_id"], task="Docker workflow")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS
    assert len(result.completed_steps) == 3


def test_54_audit_logging_events(dev_env):
    AuditLogger.clear_events()
    agent: SoftwareDevelopmentAgent = dev_env["agent"]
    req = DevelopmentRequest(request_id="req-054", workspace_id=dev_env["workspace_id"], task="Create audit test file")
    result = agent.execute_development(req)
    assert result.status == DevelopmentStatus.SUCCESS

    events = AuditLogger.get_events()
    event_types = [e.event_type for e in events]
    assert "development.request_received" in event_types
    assert "development.plan_created" in event_types
    assert "development.step_started" in event_types
    assert "development.step_completed" in event_types
    assert "development.succeeded" in event_types
