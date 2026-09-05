"""
Comprehensive unit and security test suite for Software Development Workspace.
Tests isolation, path traversal prevention, artifact hashing, structured evidence, and execution restriction.
"""

import os
from pathlib import Path
import tempfile
import pytest

from executive_twins.execution.capability_execution_engine import SpecialistExecutionEngine
from executive_twins.schemas.common import SecurityContext, SpecialistStatus, VerificationStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import Capability, SpecialistMetadata
from executive_twins.workspace.dev_adapters import (
    DevTestWorkspaceAdapter,
    WorkspaceBuildCapabilityHandler,
)
from executive_twins.workspace.interfaces import ISoftwareWorkspace
from executive_twins.workspace.local_workspace import (
    LocalSoftwareWorkspace,
    PathSecurityException,
)
from executive_twins.workspace.models import (
    WorkspaceOperationResult,
    WorkspaceOperationType,
)


@pytest.fixture
def temp_workspace_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def workspace(temp_workspace_dir):
    ws_path = os.path.join(temp_workspace_dir, "test_ws")
    ws = LocalSoftwareWorkspace(workspace_id="ws-123", root_path=ws_path)
    ws.create_workspace()
    return ws


# 1. Test Workspace Creation
def test_1_workspace_creation(temp_workspace_dir):
    ws_path = os.path.join(temp_workspace_dir, "ws_create")
    ws = LocalSoftwareWorkspace(workspace_id="ws-create", root_path=ws_path)
    assert not ws.workspace_exists()
    res = ws.create_workspace()
    assert res.success is True
    assert res.operation == WorkspaceOperationType.CREATE_WORKSPACE
    assert ws.workspace_exists()
    assert os.path.exists(ws_path)


# 2. Test Workspace Existence
def test_2_workspace_existence(workspace):
    assert workspace.workspace_exists() is True
    ws_nonexistent = LocalSoftwareWorkspace(
        workspace_id="ws-none", root_path="/path/does/not/exist/999"
    )
    assert ws_nonexistent.workspace_exists() is False


# 3. Test File Creation (write_file)
def test_3_file_creation(workspace):
    res = workspace.write_file("src/main.py", "print('Hello World')")
    assert res.success is True
    assert res.operation == WorkspaceOperationType.WRITE_FILE
    assert res.relative_path == "src/main.py"
    assert res.artifact is not None
    assert res.artifact.relative_path == "src/main.py"
    assert len(res.facts) > 0
    assert len(res.evidence) > 0


# 4. Test File Reading (read_file)
def test_4_file_reading(workspace):
    workspace.write_file("config/app.json", '{"name": "test_app"}')
    res = workspace.read_file("config/app.json")
    assert res.success is True
    assert res.operation == WorkspaceOperationType.READ_FILE
    assert res.content == '{"name": "test_app"}'
    assert res.relative_path == "config/app.json"


# 5. Test File Listing (list_files)
def test_5_file_listing(workspace):
    workspace.write_file("file1.txt", "content1")
    workspace.write_file("sub/file2.txt", "content2")
    res = workspace.list_files()
    assert res.success is True
    assert res.operation == WorkspaceOperationType.LIST_FILES
    rel_paths = [f.relative_path for f in res.files]
    assert "file1.txt" in rel_paths
    assert "sub/file2.txt" in rel_paths
    # Ensure no host absolute path leak
    for path_str in rel_paths:
        assert not path_str.startswith("/")
        assert ":" not in path_str


# 6. Test File Existence (file_exists)
def test_6_file_existence(workspace):
    assert workspace.file_exists("index.html") is False
    workspace.write_file("index.html", "<h1>Hello</h1>")
    assert workspace.file_exists("index.html") is True
    assert workspace.file_exists("nonexistent.txt") is False


# 7. Test Artifact Recording (record_artifact)
def test_7_artifact_recording(workspace):
    workspace.write_file("build/output.bin", "binary_data_content")
    res = workspace.record_artifact("build/output.bin", description="Build output artifact")
    assert res.success is True
    assert res.operation == WorkspaceOperationType.RECORD_ARTIFACT
    assert res.artifact is not None
    assert res.artifact.artifact_uri == "workspace://ws-123/build/output.bin"
    assert res.artifact.description == "Build output artifact"


# 8. Test SHA-256 Artifact Hashing
def test_8_sha256_artifact_hashing(workspace):
    content = "deterministic_sha256_test_content"
    import hashlib
    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    res = workspace.write_file("hashed_file.txt", content)
    assert res.success is True
    assert res.artifact.checksum_sha256 == expected_hash

    art_res = workspace.record_artifact("hashed_file.txt")
    assert art_res.artifact.checksum_sha256 == expected_hash


# 9. Test Workspace-Relative Path Validation
def test_9_workspace_relative_path_validation(workspace):
    res = workspace.write_file("nested/dir/deep/file.py", "x = 1")
    assert res.success is True
    assert res.relative_path == "nested/dir/deep/file.py"
    assert workspace.file_exists("nested/dir/deep/file.py")


# 10. Test Parent-Directory Traversal Rejection (../)
def test_10_parent_directory_traversal_rejection(workspace):
    res_read = workspace.read_file("../outside.txt")
    assert res_read.success is False
    assert res_read.error_type == "SECURITY_PATH_TRAVERSAL"
    assert "PATH_TRAVERSAL_REJECTED" in res_read.error_message

    res_write = workspace.write_file("sub/../../escaped.txt", "data")
    assert res_write.success is False
    assert res_write.error_type == "SECURITY_PATH_TRAVERSAL"

    res_list = workspace.list_files("../")
    assert res_list.success is False
    assert res_list.error_type == "SECURITY_PATH_TRAVERSAL"


# 11. Test Absolute Outside-Path Rejection
def test_11_absolute_outside_path_rejection(workspace, temp_workspace_dir):
    outside_file = os.path.join(temp_workspace_dir, "outside_secret.txt")
    with open(outside_file, "w") as f:
        f.write("secret_data")

    res_read = workspace.read_file(outside_file)
    assert res_read.success is False
    assert res_read.error_type == "SECURITY_PATH_TRAVERSAL"
    assert "PATH_OUTSIDE_WORKSPACE_REJECTED" in res_read.error_message

    res_write = workspace.write_file(outside_file, "malicious_overwrite")
    assert res_write.success is False
    assert res_write.error_type == "SECURITY_PATH_TRAVERSAL"


# 12. Test Symlink Escape Rejection
def test_12_symlink_escape_rejection(workspace, temp_workspace_dir):
    outside_target = os.path.join(temp_workspace_dir, "target.txt")
    with open(outside_target, "w") as f:
        f.write("sensitive_outside_content")

    symlink_inside = os.path.join(workspace.root_path, "symlink_escape.txt")
    try:
        os.symlink(outside_target, symlink_inside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this OS/user privilege level.")

    res = workspace.read_file("symlink_escape.txt")
    assert res.success is False
    assert res.error_type == "SECURITY_PATH_TRAVERSAL"
    assert "PATH_OUTSIDE_WORKSPACE_REJECTED" in res.error_message


# 13. Test Access Attempts to Files Outside Workspace
def test_13_access_files_outside_workspace(workspace):
    system_paths = ["/etc/passwd", "C:\\Windows\\System32\\cmd.exe", "../../"]
    for path in system_paths:
        res = workspace.read_file(path)
        assert res.success is False
        assert res.error_type == "SECURITY_PATH_TRAVERSAL"


# 14. Test Workspace Cleanup / Close Behavior
def test_14_workspace_cleanup_close(temp_workspace_dir):
    ws_path = os.path.join(temp_workspace_dir, "ws_close")
    ws = LocalSoftwareWorkspace(workspace_id="ws-close", root_path=ws_path)
    ws.create_workspace()
    ws.write_file("temp.txt", "temporary")

    res_close = ws.close_workspace(cleanup=True)
    assert res_close.success is True
    assert not os.path.exists(ws_path)
    assert ws.workspace_exists() is False

    # Operations on closed workspace fail cleanly
    res_op = ws.read_file("temp.txt")
    assert res_op.success is False
    assert res_op.error_type == "WORKSPACE_NOT_FOUND"


# 15. Test Structured Success Results
def test_15_structured_success_results(workspace):
    res = workspace.write_file("src/app.py", "def main(): pass")
    assert isinstance(res, WorkspaceOperationResult)
    assert res.success is True
    assert res.operation == WorkspaceOperationType.WRITE_FILE
    assert res.workspace_id == "ws-123"
    assert res.artifact is not None
    assert len(res.facts) == 1
    assert len(res.evidence) == 1


# 16. Test Structured Failure Results
def test_16_structured_failure_results(workspace):
    res = workspace.read_file("missing_file.py")
    assert isinstance(res, WorkspaceOperationResult)
    assert res.success is False
    assert res.error_type == "FILE_NOT_FOUND"
    assert res.error_message is not None
    assert "missing_file.py" in res.error_message


# 17. Test No Unrestricted Shell Execution Capability Exists
def test_17_no_unrestricted_shell_execution(workspace):
    # Verify the workspace API has no generic shell or code execution methods
    assert not hasattr(workspace, "execute")
    assert not hasattr(workspace, "run_shell")
    assert not hasattr(workspace, "system")
    assert not hasattr(workspace, "eval")

    # Verify that attempting to pass shell commands through specialist execution is rejected by boundary
    class MockRegistryClient:
        def get_specialist_by_id(self, specialist_id: str):
            return SpecialistMetadata(
                specialist_id=specialist_id,
                name="Software Specialist",
                capabilities=[
                    Capability(
                        name="workspace_build",
                        description="Build capability",
                        required_tools=["workspace_builder"],
                    )
                ],
                authorized_tools=["workspace_builder"],
                status=SpecialistStatus.ACTIVE,
            )

    adapter = DevTestWorkspaceAdapter(temp_workspace_dir=os.path.dirname(workspace.root_path))
    adapter._active_workspaces[workspace.workspace_id] = workspace

    handler = WorkspaceBuildCapabilityHandler(workspace_adapter=adapter)
    engine = SpecialistExecutionEngine(registry_client=MockRegistryClient())
    engine.register_handler(handler)

    # Attempt to inject shell command in task or inputs
    malicious_request = DelegationRequest(
        delegation_id="del-malicious",
        parent_task_id="task-001",
        executive_twin_id="twin-cto",
        specialist_id="spec-dev",
        objective="Attempt shell execution",
        expected_output="Blocked result",
        task="run_shell rm -rf /",
        required_capabilities=["workspace_build"],
        inputs={"workspace_id": workspace.workspace_id, "project_file": "app.py", "action_type": "shell_exec"},
        security_context=SecurityContext(),
    )

    result = engine.execute_delegation(malicious_request)
    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "AUTHORIZATION_DENIED" in result.output or "blocked" in result.output.lower()


# 18. Integration test for registered workspace build capability
def test_18_workspace_build_capability_integration(workspace, temp_workspace_dir):
    workspace.write_file("main.py", "print('build target')")

    class MockRegistryClient:
        def get_specialist_by_id(self, specialist_id: str):
            return SpecialistMetadata(
                specialist_id="spec-dev",
                name="Software Specialist",
                capabilities=[
                    Capability(
                        name="workspace_build",
                        description="Build capability",
                        required_tools=["workspace_builder"],
                    )
                ],
                authorized_tools=["workspace_builder"],
                status=SpecialistStatus.ACTIVE,
            )

    adapter = DevTestWorkspaceAdapter(temp_workspace_dir=temp_workspace_dir)
    adapter._active_workspaces[workspace.workspace_id] = workspace

    handler = WorkspaceBuildCapabilityHandler(workspace_adapter=adapter)
    engine = SpecialistExecutionEngine(registry_client=MockRegistryClient())
    engine.register_handler(handler)

    request = DelegationRequest(
        delegation_id="del-build-001",
        parent_task_id="task-002",
        executive_twin_id="twin-cto",
        specialist_id="spec-dev",
        objective="Build workspace application",
        expected_output="Build result and artifact",
        task="Build the workspace application",
        required_capabilities=["workspace_build"],
        inputs={"workspace_id": workspace.workspace_id, "project_file": "main.py"},
        security_context=SecurityContext(),
    )

    result = engine.execute_delegation(request)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED
    assert "Workspace build completed" in result.output
    assert len(result.evidence.items) > 0
