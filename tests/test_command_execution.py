"""
Comprehensive unit and security test suite for Controlled Build & Test Command Execution.
Tests allowlists, shell injection rejection, path traversal prevention, timeout enforcement,
output capping, authorization, and SpecialistExecutionEngine integration.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import pytest

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.command_execution import (
    BuildCapabilityHandler,
    CommandRegistry,
    CommandRequest,
    CommandResult,
    CommandSpecification,
    CommandStatus,
    CommandType,
    ControlledCommandExecutor,
    DevCommandExecutorAdapter,
    ICommandExecutor,
    LintCapabilityHandler,
    TestCapabilityHandler,
    TypecheckCapabilityHandler,
)
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.schemas.common import (
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import EvidenceCategory
from executive_twins.schemas.specialist import Capability, SpecialistMetadata
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter
from executive_twins.workspace.local_workspace import LocalSoftwareWorkspace


@pytest.fixture
def temp_env_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def workspace(temp_env_dir):
    ws_path = os.path.join(temp_env_dir, "ws_test")
    ws = LocalSoftwareWorkspace(workspace_id="ws-cmd-01", root_path=ws_path)
    ws.create_workspace()
    return ws


@pytest.fixture
def executor(workspace):
    return ControlledCommandExecutor(workspace=workspace)


# ---------------------------------------------------------------------------
# Basic Execution Tests
# ---------------------------------------------------------------------------

def test_1_approved_command_executes(workspace, executor):
    """1. Approved command executes inside workspace."""
    workspace.write_file("test_sample.py", "def test_ok(): assert True")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_sample.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is True
    assert res.status == CommandStatus.SUCCESS
    assert res.exit_code == 0


def test_2_approved_test_capability_executes(workspace, executor):
    """2. Approved test capability executes and passes."""
    workspace.write_file("test_math.py", "import unittest\nclass T(unittest.TestCase):\n  def test_add(self):\n    self.assertEqual(1+1, 2)")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "unittest", "test_math.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is True
    assert res.status == CommandStatus.SUCCESS


def test_3_successful_command_returns_success(workspace, executor):
    """3. Successful command returns SUCCESS status and exit_code 0."""
    workspace.write_file("test_ok.py", "def test_pass(): pass")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_ok.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is True
    assert res.status == CommandStatus.SUCCESS
    assert res.exit_code == 0


def test_4_failing_command_returns_failed(workspace, executor):
    """4. Failing command returns FAILED status and non-zero exit_code."""
    workspace.write_file("test_fail.py", "def test_boom(): assert 1 == 2")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_fail.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.FAILED
    assert res.exit_code != 0


def test_5_stdout_captured(workspace, executor):
    """5. Stdout is captured in the result."""
    workspace.write_file("test_out.py", "def test_verbose(): print('HELLO_STDOUT'); assert True")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "-s", "test_out.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert "HELLO_STDOUT" in res.stdout


def test_6_stderr_captured(workspace, executor):
    """6. Stderr is captured in the result."""
    workspace.write_file("test_err.py", "import sys\ndef test_err(): sys.stderr.write('HELLO_STDERR\\n'); assert True")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "-s", "test_err.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert "HELLO_STDERR" in res.stderr or "HELLO_STDERR" in res.stdout


def test_7_exit_code_captured(workspace, executor):
    """7. Exit code is captured correctly."""
    workspace.write_file("test_pass.py", "def test_pass(): assert True")
    res = executor.execute(
        CommandRequest(
            command_type=CommandType.TEST,
            executable="python",
            arguments=["-m", "pytest", "test_pass.py"],
            workspace_id=workspace.workspace_id,
        )
    )
    assert res.exit_code == 0


def test_8_duration_captured(workspace, executor):
    """8. Duration is measured and recorded."""
    workspace.write_file("test_quick.py", "def test_fast(): assert True")
    res = executor.execute(
        CommandRequest(
            command_type=CommandType.TEST,
            executable="python",
            arguments=["-m", "pytest", "test_quick.py"],
            workspace_id=workspace.workspace_id,
        )
    )
    assert res.duration_seconds > 0.0


# ---------------------------------------------------------------------------
# Authorization Tests
# ---------------------------------------------------------------------------

def test_9_authorized_specialist_can_execute_approved_capability(workspace, temp_env_dir):
    """9. Authorized specialist can execute approved command capability."""
    workspace.write_file("test_auth.py", "def test_ok(): assert True")

    ws_adapter = DevTestWorkspaceAdapter(temp_workspace_dir=temp_env_dir)
    ws_adapter._active_workspaces[workspace.workspace_id] = workspace
    cmd_adapter = DevCommandExecutorAdapter(workspace_adapter=ws_adapter)

    registry = InMemorySpecialistRegistryAdapter()
    specialist = SpecialistMetadata(
        specialist_id="spec-dev-01",
        name="Software Developer",
        capabilities=[
            Capability(
                name="test_command_execution",
                description="Run controlled test commands",
                required_tools=["command_executor"],
            )
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["command_executor"],
    )
    registry.register_specialist(specialist)

    engine = SpecialistExecutionEngine(registry_client=registry)
    engine.register_handler(TestCapabilityHandler(adapter=cmd_adapter))

    req = DelegationRequest(
        delegation_id="del-cmd-001",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-dev-01",
        objective="Run tests",
        task="Execute automated tests",
        required_capabilities=["test_command_execution"],
        inputs={
            "workspace_id": workspace.workspace_id,
            "executable": "python",
            "arguments": ["-m", "pytest", "test_auth.py"],
        },
        expected_output="Test pass result",
    )

    result = engine.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED


def test_10_unauthorized_specialist_is_rejected(workspace, temp_env_dir):
    """10. Unauthorized specialist is rejected by SecurityGuard."""
    ws_adapter = DevTestWorkspaceAdapter(temp_workspace_dir=temp_env_dir)
    ws_adapter._active_workspaces[workspace.workspace_id] = workspace
    cmd_adapter = DevCommandExecutorAdapter(workspace_adapter=ws_adapter)

    registry = InMemorySpecialistRegistryAdapter()
    unauth_specialist = SpecialistMetadata(
        specialist_id="spec-unauth-cmd",
        name="Untrusted Agent",
        capabilities=[
            Capability(
                name="test_command_execution",
                description="Run controlled test commands",
                required_tools=["command_executor"],
            )
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=[],  # Missing 'command_executor'
    )
    registry.register_specialist(unauth_specialist)

    engine = SpecialistExecutionEngine(registry_client=registry)
    engine.register_handler(TestCapabilityHandler(adapter=cmd_adapter))

    req = DelegationRequest(
        delegation_id="del-cmd-002",
        parent_task_id="task-100",
        executive_twin_id="twin-cto",
        specialist_id="spec-unauth-cmd",
        objective="Run tests",
        task="Execute tests",
        required_capabilities=["test_command_execution"],
        inputs={
            "workspace_id": workspace.workspace_id,
            "executable": "python",
            "arguments": ["-m", "pytest"],
        },
        expected_output="Output",
    )

    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "AUTHORIZATION_DENIED" in result.output


# ---------------------------------------------------------------------------
# Command Validation Tests
# ---------------------------------------------------------------------------

def test_11_arbitrary_executable_rejected(workspace, executor):
    """11. Arbitrary non-allowlisted executable is rejected."""
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="bash",
        arguments=["-c", "echo pwned"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.INVALID_COMMAND
    assert res.error_type == "INVALID_COMMAND"


def test_12_unsupported_command_type_rejected(workspace, executor):
    """12. Unsupported command type / executable combination is rejected."""
    # python executable under PACKAGE without approved arguments
    req = CommandRequest(
        command_type=CommandType.PACKAGE,
        executable="python",
        arguments=["arbitrary_script.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.INVALID_COMMAND


def test_13_arbitrary_command_string_rejected(workspace, executor):
    """13. Arbitrary command arguments not matching allowlist are rejected."""
    req = CommandRequest(
        command_type=CommandType.BUILD,
        executable="python",
        arguments=["-m", "http.server", "8000"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.INVALID_COMMAND


def test_14_and_operator_rejected(workspace, executor):
    """14. '&&' shell operator is rejected."""
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "&&", "evil"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_SHELL_OPERATOR_REJECTED"


def test_15_or_operator_rejected(workspace, executor):
    """15. '||' shell operator is rejected."""
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "||", "echo fail"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_SHELL_OPERATOR_REJECTED"


def test_16_semicolon_operator_rejected(workspace, executor):
    """16. ';' shell operator is rejected."""
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest; rm -rf /"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_SHELL_OPERATOR_REJECTED"


def test_17_pipe_operator_rejected(workspace, executor):
    """17. '|' shell pipe is rejected."""
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "|", "cat"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_SHELL_OPERATOR_REJECTED"


def test_18_redirection_operator_rejected(workspace, executor):
    """18. '>' redirection operator is rejected."""
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", ">", "out.txt"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_SHELL_OPERATOR_REJECTED"


def test_19_command_substitution_rejected(workspace, executor):
    """19. Command substitution `$(...)` and backticks are rejected."""
    req1 = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "$(whoami)"],
        workspace_id=workspace.workspace_id,
    )
    res1 = executor.execute(req1)
    assert res1.success is False
    assert res1.status == CommandStatus.REJECTED

    req2 = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "`whoami`"],
        workspace_id=workspace.workspace_id,
    )
    res2 = executor.execute(req2)
    assert res2.success is False
    assert res2.status == CommandStatus.REJECTED


# ---------------------------------------------------------------------------
# Workspace Security Tests
# ---------------------------------------------------------------------------

def test_20_arbitrary_working_directory_rejected(workspace, executor):
    """20. Command execution strictly uses workspace root as working directory."""
    # Verify ControlledCommandExecutor does not accept arbitrary cwd parameter
    assert not hasattr(executor, "cwd")
    assert executor.workspace.root_path == workspace.root_path


def test_21_absolute_working_directory_rejected(workspace, executor, temp_env_dir):
    """21. Absolute outside path argument is rejected."""
    outside_file = os.path.join(temp_env_dir, "outside_test.py")
    with open(outside_file, "w") as f:
        f.write("def test_outside(): assert True")

    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", outside_file],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_PATH_TRAVERSAL"


def test_22_path_traversal_rejected(workspace, executor):
    """22. Parent-directory traversal '../' in arguments is rejected."""
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "../outside_dir/test.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_PATH_TRAVERSAL"


def test_23_outside_workspace_path_rejected(workspace, executor):
    """23. System paths like C:\\Windows or /etc are rejected."""
    system_path = "C:\\Windows\\System32\\cmd.exe" if sys.platform == "win32" else "/etc/passwd"
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", system_path],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_PATH_TRAVERSAL"


def test_24_symlink_escape_rejected(workspace, executor, temp_env_dir):
    """24. Symlink pointing outside the workspace is rejected where supported."""
    outside_target = os.path.join(temp_env_dir, "outside_target.py")
    with open(outside_target, "w") as f:
        f.write("def test_sym(): assert True")

    symlink_inside = os.path.join(workspace.root_path, "symlink_test.py")
    try:
        os.symlink(outside_target, symlink_inside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this OS / privilege level.")

    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "symlink_test.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.REJECTED
    assert res.error_type == "SECURITY_PATH_TRAVERSAL"


# ---------------------------------------------------------------------------
# Runtime Safety Tests
# ---------------------------------------------------------------------------

def test_25_timeout_is_enforced(workspace, executor):
    """25. Timeout is enforced when command exceeds configured threshold."""
    # Write a test that sleeps for 5 seconds
    workspace.write_file("test_sleep.py", "import time\ndef test_slow(): time.sleep(5)")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_sleep.py"],
        workspace_id=workspace.workspace_id,
        timeout_seconds=0.5,
    )
    res = executor.execute(req)
    assert res.success is False
    assert res.status == CommandStatus.TIMEOUT
    assert res.error_type == "EXECUTION_TIMEOUT"


def test_26_output_size_limit_is_enforced(workspace, executor):
    """26. Output size limit is enforced and marks is_truncated = True."""
    # Create test emitting 150KB of output
    workspace.write_file("test_huge.py", "def test_huge():\n  print('A' * 120_000)\n  assert True")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "-s", "test_huge.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.is_truncated is True
    assert "[STDOUT TRUNCATED]" in res.stdout


def test_27_structured_timeout_result_returned(workspace, executor):
    """27. Structured timeout result includes error type and message."""
    workspace.write_file("test_hang.py", "import time\ndef test_hang(): time.sleep(4)")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_hang.py"],
        workspace_id=workspace.workspace_id,
        timeout_seconds=0.3,
    )
    res = executor.execute(req)
    assert isinstance(res, CommandResult)
    assert res.status == CommandStatus.TIMEOUT
    assert res.error_type == "EXECUTION_TIMEOUT"
    assert "timed out" in res.error_message.lower()


def test_28_structured_failure_result_returned(workspace, executor):
    """28. Structured failure result is returned for non-zero exit codes."""
    workspace.write_file("test_broken.py", "def test_err(): raise RuntimeError('kaboom')")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_broken.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert isinstance(res, CommandResult)
    assert res.success is False
    assert res.status == CommandStatus.FAILED
    assert res.exit_code != 0
    assert len(res.facts) > 0


# ---------------------------------------------------------------------------
# Evidence Tests
# ---------------------------------------------------------------------------

def test_29_execution_evidence_generated(workspace, executor):
    """29. Execution log and verification evidence generated."""
    workspace.write_file("test_ev.py", "def test_1(): assert True")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_ev.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert len(res.evidence) >= 2
    assert any(ev.category == EvidenceCategory.EXECUTION_LOG for ev in res.evidence)
    assert any(ev.category == EvidenceCategory.VERIFICATION for ev in res.evidence)


def test_30_successful_test_generates_test_evidence(workspace, executor):
    """30. Successful test generates TestEvidence."""
    workspace.write_file("test_pass_ev.py", "def test_ok(): assert True")
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_pass_ev.py"],
        workspace_id=workspace.workspace_id,
    )
    res = executor.execute(req)
    assert any(ev.category == EvidenceCategory.TEST for ev in res.evidence)


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

def test_31_build_capability_handler_works_through_engine(workspace, temp_env_dir):
    """31. BuildCapabilityHandler works through SpecialistExecutionEngine."""
    ws_adapter = DevTestWorkspaceAdapter(temp_workspace_dir=temp_env_dir)
    ws_adapter._active_workspaces[workspace.workspace_id] = workspace
    cmd_adapter = DevCommandExecutorAdapter(workspace_adapter=ws_adapter)

    # Register a custom python build specification for deterministic test
    cmd_adapter.registry.register_specification(
        CommandSpecification(
            command_type=CommandType.BUILD,
            executable="python",
            allowed_argument_prefixes=[["-m", "unittest"]],
        )
    )

    workspace.write_file("test_build_step.py", "import unittest\nclass T(unittest.TestCase):\n  def test_b(self): pass")

    registry = InMemorySpecialistRegistryAdapter()
    specialist = SpecialistMetadata(
        specialist_id="spec-builder-01",
        name="Build Specialist",
        capabilities=[
            Capability(
                name="build_command_execution",
                description="Controlled build execution",
                required_tools=["command_executor"],
            )
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["command_executor"],
    )
    registry.register_specialist(specialist)

    engine = SpecialistExecutionEngine(registry_client=registry)
    engine.register_handler(BuildCapabilityHandler(adapter=cmd_adapter))

    req = DelegationRequest(
        delegation_id="del-build-001",
        parent_task_id="task-101",
        executive_twin_id="twin-cto",
        specialist_id="spec-builder-01",
        objective="Run build step",
        task="Execute build step",
        required_capabilities=["build_command_execution"],
        inputs={
            "workspace_id": workspace.workspace_id,
            "executable": "python",
            "arguments": ["-m", "unittest", "test_build_step.py"],
        },
        expected_output="Build result",
    )

    result = engine.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED


def test_32_test_capability_handler_works_through_engine(workspace, temp_env_dir):
    """32. TestCapabilityHandler works through SpecialistExecutionEngine."""
    workspace.write_file("test_eng.py", "def test_engine(): assert True")

    ws_adapter = DevTestWorkspaceAdapter(temp_workspace_dir=temp_env_dir)
    ws_adapter._active_workspaces[workspace.workspace_id] = workspace
    cmd_adapter = DevCommandExecutorAdapter(workspace_adapter=ws_adapter)

    registry = InMemorySpecialistRegistryAdapter()
    specialist = SpecialistMetadata(
        specialist_id="spec-tester-01",
        name="Test Specialist",
        capabilities=[
            Capability(
                name="test_command_execution",
                description="Controlled test execution",
                required_tools=["command_executor"],
            )
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["command_executor"],
    )
    registry.register_specialist(specialist)

    engine = SpecialistExecutionEngine(registry_client=registry)
    engine.register_handler(TestCapabilityHandler(adapter=cmd_adapter))

    req = DelegationRequest(
        delegation_id="del-test-001",
        parent_task_id="task-102",
        executive_twin_id="twin-cto",
        specialist_id="spec-tester-01",
        objective="Run test suite",
        task="Execute test suite",
        required_capabilities=["test_command_execution"],
        inputs={
            "workspace_id": workspace.workspace_id,
            "executable": "python",
            "arguments": ["-m", "pytest", "test_eng.py"],
        },
        expected_output="Test result",
    )

    result = engine.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED


def test_33_unauthorized_command_capability_is_rejected(workspace, temp_env_dir):
    """33. Specialist requesting capability it is not authorized for is rejected."""
    ws_adapter = DevTestWorkspaceAdapter(temp_workspace_dir=temp_env_dir)
    ws_adapter._active_workspaces[workspace.workspace_id] = workspace
    cmd_adapter = DevCommandExecutorAdapter(workspace_adapter=ws_adapter)

    registry = InMemorySpecialistRegistryAdapter()
    specialist = SpecialistMetadata(
        specialist_id="spec-doc-01",
        name="Documentation Specialist",
        capabilities=[
            Capability(
                name="test_command_execution",
                description="Controlled test execution",
                required_tools=["command_executor"],
            )
        ],
        status=SpecialistStatus.ACTIVE,
        authorized_tools=["doc_writer"],  # Not authorized for command_executor
    )
    registry.register_specialist(specialist)

    engine = SpecialistExecutionEngine(registry_client=registry)
    engine.register_handler(TestCapabilityHandler(adapter=cmd_adapter))

    req = DelegationRequest(
        delegation_id="del-test-002",
        parent_task_id="task-103",
        executive_twin_id="twin-cto",
        specialist_id="spec-doc-01",
        objective="Run tests",
        task="Execute tests",
        required_capabilities=["test_command_execution"],
        inputs={
            "workspace_id": workspace.workspace_id,
            "executable": "python",
            "arguments": ["-m", "pytest"],
        },
        expected_output="Test result",
    )

    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "AUTHORIZATION_DENIED" in result.output
