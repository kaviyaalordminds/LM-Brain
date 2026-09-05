import os
import pathlib
import tempfile
import pytest

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
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
from executive_twins.files.file_service import FileService
from executive_twins.files.interfaces import IFileService
from executive_twins.files.models import (
    FileMetadata,
    FileOperationRequest,
    FileOperationResult,
    FileOperationType,
)
from executive_twins.schemas.common import SecurityContext, SpecialistStatus, VerificationStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import Capability, SpecialistMetadata
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter
from executive_twins.workspace.local_workspace import LocalSoftwareWorkspace


@pytest.fixture
def temp_workspace():
    """Create a temporary isolated workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        ws_id = "test-ws-001"
        ws_root = os.path.join(temp_dir, ws_id)
        workspace = LocalSoftwareWorkspace(workspace_id=ws_id, root_path=ws_root)
        workspace.create_workspace()
        file_service = FileService(workspace=workspace)
        yield workspace, file_service
        workspace.close_workspace(cleanup=True)


# 1. File service initialization
def test_1_file_service_initialization(temp_workspace):
    workspace, file_service = temp_workspace
    assert file_service is not None
    assert isinstance(file_service, IFileService)
    assert file_service.workspace.workspace_id == "test-ws-001"
    assert file_service.workspace.workspace_exists() is True


# 2. Create file
def test_2_create_file(temp_workspace):
    workspace, file_service = temp_workspace
    res = file_service.create_file("src/hello.py", "print('hello world')")

    assert res.success is True
    assert res.operation == FileOperationType.CREATE
    assert res.relative_path == "src/hello.py"
    assert res.metadata is not None
    assert res.metadata.relative_path == "src/hello.py"
    assert res.metadata.file_name == "hello.py"
    assert res.metadata.size_bytes > 0
    assert res.metadata.checksum_sha256 is not None
    assert res.artifact is not None
    assert len(res.facts) > 0
    assert len(res.evidence) > 0


# 3. Read file
def test_3_read_file(temp_workspace):
    workspace, file_service = temp_workspace
    file_service.create_file("src/hello.py", "print('hello world')")

    res = file_service.read_file("src/hello.py")
    assert res.success is True
    assert res.operation == FileOperationType.READ
    assert res.content == "print('hello world')"
    assert len(res.facts) > 0


# 4. Update file
def test_4_update_file(temp_workspace):
    workspace, file_service = temp_workspace
    file_service.create_file("config.json", '{"version": 1}')

    res = file_service.update_file("config.json", '{"version": 2}')
    assert res.success is True
    assert res.operation == FileOperationType.UPDATE

    read_res = file_service.read_file("config.json")
    assert read_res.content == '{"version": 2}'


# 5. Delete file
def test_5_delete_file(temp_workspace):
    workspace, file_service = temp_workspace
    file_service.create_file("temp.txt", "delete me")

    del_res = file_service.delete_file("temp.txt")
    assert del_res.success is True
    assert del_res.operation == FileOperationType.DELETE

    exists_res = file_service.file_exists("temp.txt")
    assert exists_res.exists is False


# 6. List files
def test_6_list_files(temp_workspace):
    workspace, file_service = temp_workspace
    file_service.create_file("file1.txt", "content 1")
    file_service.create_file("file2.txt", "content 2")
    file_service.create_file("sub/file3.txt", "content 3")

    res = file_service.list_files()
    assert res.success is True
    assert res.operation == FileOperationType.LIST
    assert len(res.files) >= 3

    rel_paths = [f.relative_path for f in res.files]
    assert "file1.txt" in rel_paths
    assert "file2.txt" in rel_paths
    assert "sub/file3.txt" in rel_paths


# 7. File exists
def test_7_file_exists(temp_workspace):
    workspace, file_service = temp_workspace
    file_service.create_file("check.txt", "data")

    res_true = file_service.file_exists("check.txt")
    assert res_true.success is True
    assert res_true.exists is True

    res_false = file_service.file_exists("nonexistent.txt")
    assert res_false.success is True
    assert res_false.exists is False


# 8. File metadata
def test_8_get_file_metadata(temp_workspace):
    workspace, file_service = temp_workspace
    content = "metadata test string"
    file_service.create_file("meta.txt", content)

    res = file_service.get_file_metadata("meta.txt")
    assert res.success is True
    assert res.operation == FileOperationType.METADATA
    assert res.metadata is not None
    assert res.metadata.relative_path == "meta.txt"
    assert res.metadata.file_name == "meta.txt"
    assert res.metadata.size_bytes == len(content)
    assert res.metadata.is_directory is False
    assert res.metadata.checksum_sha256 is not None
    # Verify absolute path is NOT exposed in FileMetadata model
    assert not hasattr(res.metadata, "absolute_path")
    assert not hasattr(res.metadata, "host_path")


# 9. Duplicate creation handling
def test_9_duplicate_creation_handling(temp_workspace):
    workspace, file_service = temp_workspace
    file_service.create_file("unique.txt", "first version")

    # Overwrite=False must fail
    res_fail = file_service.create_file("unique.txt", "second version", overwrite=False)
    assert res_fail.success is False
    assert res_fail.error_type == "FILE_ALREADY_EXISTS"

    # Overwrite=True must succeed
    res_succ = file_service.create_file("unique.txt", "second version", overwrite=True)
    assert res_succ.success is True

    read_res = file_service.read_file("unique.txt")
    assert read_res.content == "second version"


# 10. Missing file handling
def test_10_missing_file_handling(temp_workspace):
    workspace, file_service = temp_workspace

    read_res = file_service.read_file("missing.txt")
    assert read_res.success is False
    assert read_res.error_type == "FILE_NOT_FOUND"

    update_res = file_service.update_file("missing.txt", "content")
    assert update_res.success is False
    assert update_res.error_type == "FILE_NOT_FOUND"

    del_res = file_service.delete_file("missing.txt")
    assert del_res.success is False
    assert del_res.error_type == "FILE_NOT_FOUND"

    meta_res = file_service.get_file_metadata("missing.txt")
    assert meta_res.success is False
    assert meta_res.error_type == "FILE_NOT_FOUND"


# 11. Directory-as-file rejection
def test_11_directory_as_file_rejection(temp_workspace):
    workspace, file_service = temp_workspace
    file_service.create_file("dir/file.txt", "content")

    # Attempt to read directory as file
    read_dir = file_service.read_file("dir")
    assert read_dir.success is False
    assert read_dir.error_type in ["IS_DIRECTORY", "FILE_NOT_FOUND"]

    # Attempt to delete directory via delete_file
    del_dir = file_service.delete_file("dir")
    assert del_dir.success is False
    assert del_dir.error_type in ["IS_DIRECTORY", "FILE_NOT_FOUND"]


# 12. ../ parent directory traversal rejection
def test_12_parent_directory_traversal_rejection(temp_workspace):
    workspace, file_service = temp_workspace

    res_create = file_service.create_file("../outside.txt", "malicious content")
    assert res_create.success is False
    assert res_create.error_type in ["SECURITY_PATH_TRAVERSAL", "INVALID_PATH"]

    res_read = file_service.read_file("../secret.txt")
    assert res_read.success is False
    assert res_read.error_type in ["SECURITY_PATH_TRAVERSAL", "INVALID_PATH"]

    res_del = file_service.delete_file("../../root.txt")
    assert res_del.success is False
    assert res_del.error_type in ["SECURITY_PATH_TRAVERSAL", "INVALID_PATH"]

    res_exists = file_service.file_exists("../outside.txt")
    assert res_exists.success is False or res_exists.exists is False


# 13. Absolute outside-path rejection
def test_13_absolute_outside_path_rejection(temp_workspace):
    workspace, file_service = temp_workspace
    outside_path = (
        "C:\\Windows\\System32\\cmd.exe"
        if os.name == "nt"
        else "/etc/passwd"
    )

    res_create = file_service.create_file(outside_path, "malicious")
    assert res_create.success is False
    assert res_create.error_type in ["SECURITY_PATH_TRAVERSAL", "INVALID_PATH", "PATH_OUTSIDE_WORKSPACE_REJECTED"]

    res_read = file_service.read_file(outside_path)
    assert res_read.success is False
    assert res_read.error_type in ["SECURITY_PATH_TRAVERSAL", "INVALID_PATH", "PATH_OUTSIDE_WORKSPACE_REJECTED"]


# 14. Outside workspace access rejection
def test_14_outside_workspace_access_rejection(temp_workspace):
    workspace, file_service = temp_workspace
    # Try traversing multiple parent directories
    deep_traversal = "../../../../../tmp/escape.txt"

    res = file_service.create_file(deep_traversal, "escape")
    assert res.success is False
    assert res.error_type in ["SECURITY_PATH_TRAVERSAL", "INVALID_PATH"]


# 15. Symlink escape protection where supported
def test_15_symlink_escape_protection(temp_workspace):
    workspace, file_service = temp_workspace

    with tempfile.TemporaryDirectory() as external_dir:
        secret_file = os.path.join(external_dir, "secret.txt")
        with open(secret_file, "w") as f:
            f.write("top_secret")

        symlink_path = os.path.join(workspace.root_path, "symlink_escape.txt")
        try:
            os.symlink(secret_file, symlink_path)
        except (OSError, NotImplementedError, AttributeAttributeError if hasattr(os, 'AttributeError') else Exception):
            pytest.skip("Symlink creation not supported or permitted in current environment.")

        # If symlink creation succeeded, attempt to read via Files API
        read_res = file_service.read_file("symlink_escape.txt")
        assert read_res.success is False
        assert read_res.error_type in ["SECURITY_PATH_TRAVERSAL", "FILE_NOT_FOUND"]


# 16. Hash and metadata correctness
def test_16_hash_and_metadata_correctness(temp_workspace):
    import hashlib

    workspace, file_service = temp_workspace
    content = "Hello, LM-Brain Files API!"
    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    create_res = file_service.create_file("test.txt", content)
    assert create_res.success is True
    assert create_res.metadata.checksum_sha256 == expected_hash

    meta_res = file_service.get_file_metadata("test.txt")
    assert meta_res.success is True
    assert meta_res.metadata.checksum_sha256 == expected_hash


# 17. Structured success result
def test_17_structured_success_result(temp_workspace):
    workspace, file_service = temp_workspace
    res = file_service.create_file("structured.txt", "data")

    assert isinstance(res, FileOperationResult)
    assert res.success is True
    assert res.operation == FileOperationType.CREATE
    assert res.workspace_id == workspace.workspace_id
    assert res.relative_path == "structured.txt"
    assert res.error_message is None
    assert res.error_type is None
    assert len(res.facts) > 0
    assert len(res.evidence) > 0


# 18. Structured failure result
def test_18_structured_failure_result(temp_workspace):
    workspace, file_service = temp_workspace
    res = file_service.read_file("nonexistent.txt")

    assert isinstance(res, FileOperationResult)
    assert res.success is False
    assert res.operation == FileOperationType.READ
    assert res.workspace_id == workspace.workspace_id
    assert res.error_message is not None
    assert res.error_type == "FILE_NOT_FOUND"


# 19. No unrestricted shell execution API
def test_19_no_unrestricted_shell_execution_api(temp_workspace):
    workspace, file_service = temp_workspace

    forbidden_methods = ["execute", "run_shell", "run_command", "system_call", "eval"]
    for method_name in forbidden_methods:
        assert not hasattr(file_service, method_name), f"FileService must not expose '{method_name}'."
        assert not hasattr(IFileService, method_name), f"IFileService must not expose '{method_name}'."


# 20. Integration with existing Software Development Workspace
def test_20_integration_with_software_workspace(temp_workspace):
    workspace, file_service = temp_workspace
    # Verify FileService wraps LocalSoftwareWorkspace properly
    assert file_service.workspace is workspace

    res = file_service.create_file("main.py", "print('main')")
    assert res.success is True
    assert workspace.file_exists("main.py") is True
    assert workspace.read_file("main.py").content == "print('main')"


# 21. Integration with SpecialistExecutionEngine
def test_21_specialist_execution_engine_integration():
    with tempfile.TemporaryDirectory() as temp_dir:
        ws_adapter = DevTestWorkspaceAdapter(base_temp_dir=temp_dir)
        ws = ws_adapter.create_workspace("spec-ws-001")
        file_adapter = DevFileServiceAdapter(workspace_adapter=ws_adapter)

        registry = InMemorySpecialistRegistryAdapter()
        specialist = SpecialistMetadata(
            specialist_id="spec-dev-01",
            name="Dev Specialist",
            capabilities=[
                Capability(name="file_create", description="Create files", required_tools=["file_service"]),
                Capability(name="file_read", description="Read files", required_tools=["file_service"]),
                Capability(name="file_update", description="Update files", required_tools=["file_service"]),
                Capability(name="file_delete", description="Delete files", required_tools=["file_service"]),
                Capability(name="file_list", description="List files", required_tools=["file_service"]),
            ],
            status=SpecialistStatus.ACTIVE,
            authorized_tools=["file_service"],
            security_level="standard",
        )
        registry.register_specialist(specialist)

        engine = SpecialistExecutionEngine(registry_client=registry)
        engine.register_handler(FileCreateCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(FileReadCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(FileUpdateCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(FileDeleteCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(FileListCapabilityHandler(file_adapter=file_adapter))

        adapter = SpecialistExecutionAdapter(execution_engine=engine)

        # 1. Execute file_create capability
        create_req = DelegationRequest(
            delegation_id="del-file-01",
            parent_task_id="task-200",
            executive_twin_id="twin-cto",
            specialist_id="spec-dev-01",
            objective="Create source file",
            task="Create file index.js",
            required_capabilities=["file_create"],
            inputs={
                "workspace_id": "spec-ws-001",
                "relative_path": "index.js",
                "content": "console.log('hello');",
            },
            expected_output="Created index.js",
            security_context=SecurityContext(is_authenticated=True),
        )
        create_res = adapter.execute_delegation(create_req)
        assert create_res.status == "SUCCESS"
        assert create_res.verification_status == VerificationStatus.VERIFIED

        # 2. Execute file_read capability
        read_req = DelegationRequest(
            delegation_id="del-file-02",
            parent_task_id="task-200",
            executive_twin_id="twin-cto",
            specialist_id="spec-dev-01",
            objective="Read source file",
            task="Read file index.js",
            required_capabilities=["file_read"],
            inputs={
                "workspace_id": "spec-ws-001",
                "relative_path": "index.js",
            },
            expected_output="File content",
            security_context=SecurityContext(is_authenticated=True),
        )
        read_res = adapter.execute_delegation(read_req)
        assert read_res.status == "SUCCESS"
        assert read_res.output == "console.log('hello');"

        # 3. Execute file_update capability
        update_req = DelegationRequest(
            delegation_id="del-file-03",
            parent_task_id="task-200",
            executive_twin_id="twin-cto",
            specialist_id="spec-dev-01",
            objective="Update source file",
            task="Update index.js",
            required_capabilities=["file_update"],
            inputs={
                "workspace_id": "spec-ws-001",
                "relative_path": "index.js",
                "content": "console.log('updated');",
            },
            expected_output="Updated index.js",
            security_context=SecurityContext(is_authenticated=True),
        )
        update_res = adapter.execute_delegation(update_req)
        assert update_res.status == "SUCCESS"

        # 4. Execute file_delete capability
        delete_req = DelegationRequest(
            delegation_id="del-file-04",
            parent_task_id="task-200",
            executive_twin_id="twin-cto",
            specialist_id="spec-dev-01",
            objective="Delete source file",
            task="Delete index.js",
            required_capabilities=["file_delete"],
            inputs={
                "workspace_id": "spec-ws-001",
                "relative_path": "index.js",
            },
            expected_output="Deleted index.js",
            security_context=SecurityContext(is_authenticated=True),
        )
        delete_res = adapter.execute_delegation(delete_req)
        assert delete_res.status == "SUCCESS"

        ws_adapter.close_all(cleanup=True)


# 22. Unauthorized file capability rejection
def test_22_unauthorized_file_capability_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        ws_adapter = DevTestWorkspaceAdapter(base_temp_dir=temp_dir)
        ws_adapter.create_workspace("spec-ws-002")
        file_adapter = DevFileServiceAdapter(workspace_adapter=ws_adapter)

        registry = InMemorySpecialistRegistryAdapter()
        # Specialist unauthorized for 'file_service' tool
        unauth_specialist = SpecialistMetadata(
            specialist_id="spec-restricted-01",
            name="Restricted Specialist",
            capabilities=[
                Capability(name="file_create", description="Create files", required_tools=["file_service"])
            ],
            status=SpecialistStatus.ACTIVE,
            authorized_tools=[],  # Empty authorized tools list
            security_level="standard",
        )
        registry.register_specialist(unauth_specialist)

        engine = SpecialistExecutionEngine(registry_client=registry)
        engine.register_handler(FileCreateCapabilityHandler(file_adapter=file_adapter))
        adapter = SpecialistExecutionAdapter(execution_engine=engine)

        req = DelegationRequest(
            delegation_id="del-unauth-01",
            parent_task_id="task-200",
            executive_twin_id="twin-cto",
            specialist_id="spec-restricted-01",
            objective="Create unauthorized file",
            task="Create file test.txt",
            required_capabilities=["file_create"],
            inputs={
                "workspace_id": "spec-ws-002",
                "relative_path": "test.txt",
                "content": "unauthorized",
            },
            expected_output="Output",
            security_context=SecurityContext(is_authenticated=True),
        )

        res = adapter.execute_delegation(req)
        assert res.status == "FAILED"
        assert res.verification_status == VerificationStatus.FAILED
        assert "AUTHORIZATION_DENIED" in res.output

        ws_adapter.close_all(cleanup=True)
