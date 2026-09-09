"""
Comprehensive unit and security test suite for Controlled Docker Execution Layer.
Tests Docker availability, workspace boundary isolation, image build safety,
container isolation, resource bounds, container lifecycle, SecurityGuard authorization,
SpecialistExecutionEngine integration, evidence generation, and regression.
"""

from datetime import datetime, timezone
import inspect
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import List, Optional, Set
import pytest

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.command_execution import (
    CommandRequest,
    CommandType,
    ControlledCommandExecutor,
)
from executive_twins.docker import (
    BaseDockerCapabilityHandler,
    ControlledDockerService,
    DevDockerServiceAdapter,
    DevTestDockerService,
    DockerAvailabilityCapabilityHandler,
    DockerBuildCapabilityHandler,
    DockerInspectCapabilityHandler,
    DockerOperationType,
    DockerRemoveCapabilityHandler,
    DockerRequest,
    DockerResult,
    DockerRunCapabilityHandler,
    DockerStatus,
    DockerStopCapabilityHandler,
    IDockerService,
)
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard
from executive_twins.files import FileService, FileOperationType, FileOperationRequest
from executive_twins.git import ControlledGitService, GitOperationType, GitRequest
from executive_twins.schemas.common import (
    FailureState,
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import Capability, SpecialistMetadata
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter
from executive_twins.workspace.local_workspace import LocalSoftwareWorkspace


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def docker_workspace(temp_dir):
    """Create a temporary initialized workspace containing a sample Dockerfile."""
    ws_path = os.path.join(temp_dir, "ws_docker_test")
    ws = LocalSoftwareWorkspace(workspace_id="ws-docker-01", root_path=ws_path)
    ws.create_workspace()
    # Write sample Dockerfile and app files
    ws.write_file("Dockerfile", "FROM node:alpine\nCOPY . .\nCMD [\"node\", \"index.js\"]\n")
    ws.write_file("index.js", "console.log('hello from container');\n")
    return ws


@pytest.fixture
def test_docker_service(docker_workspace):
    """Provide a deterministic DevTestDockerService associated with the workspace."""
    service = DevTestDockerService(
        workspace=docker_workspace,
        approved_images={"node:alpine", "python:3.11-slim", "alpine:latest"},
    )
    return service


@pytest.fixture
def real_or_controlled_service(docker_workspace):
    """Provide a ControlledDockerService."""
    return ControlledDockerService(
        workspace=docker_workspace,
        approved_images={"node:alpine", "python:3.11-slim", "alpine:latest"},
    )


# -----------------------------------------------------------------------------
# 1. Availability Tests (1-2)
# -----------------------------------------------------------------------------

def test_1_docker_availability_success(test_docker_service):
    """1. Docker availability check succeeds when daemon is available."""
    res = test_docker_service.check_availability()
    assert res.success is True
    assert res.status == DockerStatus.SUCCESS
    assert "available" in res.message.lower()
    assert len(res.facts) > 0
    assert any(isinstance(e, ExecutionLogEvidence) for e in res.evidence)
    assert any(isinstance(e, VerificationEvidence) for e in res.evidence)


def test_2_docker_unavailable_handling(docker_workspace):
    """2. Docker unavailable handling produces DOCKER_UNAVAILABLE status cleanly."""
    unavailable_service = DevTestDockerService(
        workspace=docker_workspace,
        simulate_docker_unavailable=True,
    )
    res = unavailable_service.check_availability()
    assert res.success is False
    assert res.status == DockerStatus.DOCKER_UNAVAILABLE
    assert "unavailable" in res.message.lower() or "not running" in res.message.lower()


# -----------------------------------------------------------------------------
# 2. Workspace Security Tests (3-8)
# -----------------------------------------------------------------------------

def test_3_valid_workspace_accepted(test_docker_service):
    """3. Valid workspace-contained paths are accepted."""
    res = test_docker_service.build_image(
        image_name="test-app:1.0",
        dockerfile_path="Dockerfile",
        build_context=".",
    )
    assert res.success is True
    assert res.status == DockerStatus.SUCCESS
    assert res.image_name == "test-app:1.0"


def test_4_absolute_build_context_rejected(test_docker_service):
    """4. Absolute host build context path is rejected."""
    abs_path = "C:/Windows" if sys.platform == "win32" else "/etc"
    res = test_docker_service.build_image(
        image_name="test-app:1.0",
        dockerfile_path="Dockerfile",
        build_context=abs_path,
    )
    assert res.success is False
    assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)
    assert "OUTSIDE" in res.error_message or "REJECTED" in res.error_message or "Absolute" in res.error_message


def test_5_parent_traversal_rejected(test_docker_service):
    """5. Parent directory traversal `../` is strictly rejected."""
    res = test_docker_service.build_image(
        image_name="test-app:1.0",
        dockerfile_path="../Dockerfile",
        build_context=".",
    )
    assert res.success is False
    assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)
    assert "TRAVERSAL" in str(res.error_message)


def test_6_windows_traversal_rejected(test_docker_service):
    """6. Windows-style traversal `..\\` and drive letters are rejected."""
    res = test_docker_service.build_image(
        image_name="test-app:1.0",
        dockerfile_path="..\\Dockerfile",
        build_context=".",
    )
    assert res.success is False
    assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)

    res2 = test_docker_service.build_image(
        image_name="test-app:1.0",
        dockerfile_path="D:\\secret\\Dockerfile",
        build_context=".",
    )
    assert res2.success is False
    assert res2.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


def test_7_symlink_escape_rejected(docker_workspace, test_docker_service, temp_dir):
    """7. Symlink escaping outside workspace boundary is rejected."""
    outside_file = Path(temp_dir) / "outside_dockerfile"
    outside_file.write_text("FROM alpine\n")
    symlink_path = Path(docker_workspace.root_path) / "symlink_df"
    try:
        symlink_path.symlink_to(outside_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation requires elevated privileges on Windows.")

    res = test_docker_service.build_image(
        image_name="test-app:1.0",
        dockerfile_path="symlink_df",
        build_context=".",
    )
    assert res.success is False
    assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


def test_8_dockerfile_outside_workspace_rejected(test_docker_service):
    """8. Dockerfile resolving outside workspace boundary is rejected."""
    res = test_docker_service.build_image(
        image_name="test-app:1.0",
        dockerfile_path="sub/../../secret.Dockerfile",
        build_context=".",
    )
    assert res.success is False
    assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


# -----------------------------------------------------------------------------
# 3. Image Build Tests (9-15)
# -----------------------------------------------------------------------------

def test_9_valid_build_request(test_docker_service):
    """9. Valid build request builds image and registers artifact evidence."""
    res = test_docker_service.build_image(
        image_name="valid-img:v1",
        dockerfile_path="Dockerfile",
        build_context=".",
    )
    assert res.success is True
    assert res.status == DockerStatus.SUCCESS
    assert res.image_name == "valid-img:v1"
    assert any(isinstance(e, ArtifactEvidence) for e in res.evidence)


def test_10_invalid_image_name_rejected(test_docker_service):
    """10. Invalid image name (spaces, uppercase, special characters) is rejected."""
    for invalid_name in ["Invalid Name:v1", "UPPERCASE:1", "test@img", "-leading-dash", ""]:
        res = test_docker_service.build_image(image_name=invalid_name)
        assert res.success is False
        assert res.status in (DockerStatus.INVALID_INPUT, DockerStatus.REJECTED)


def test_11_image_tag_injection_rejected(test_docker_service):
    """11. Image tag with shell injection or option injection is rejected."""
    for bad_tag in ["app:1.0;rm -rf /", "app:1.0`whoami`", "app:$(whoami)", "app:--privileged"]:
        res = test_docker_service.build_image(image_name=bad_tag)
        assert res.success is False
        assert res.status in (DockerStatus.INVALID_INPUT, DockerStatus.REJECTED)


def test_12_arbitrary_build_arguments_rejected():
    """12. Arbitrary build arguments are rejected in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.BUILD_IMAGE,
            image_name="test:v1",
            build_args={"--network": "host", "--secret": "id=mysec"},  # type: ignore
        )


def test_13_arbitrary_registry_reference_rejected(test_docker_service):
    """13. Arbitrary remote registry URLs / schemes are rejected in V1."""
    for remote_ref in ["https://registry.evil.com/app:v1", "http://docker.io/app:v1"]:
        res = test_docker_service.build_image(image_name=remote_ref)
        assert res.success is False
        assert res.status in (DockerStatus.INVALID_INPUT, DockerStatus.REJECTED)


def test_14_output_limit_enforced(test_docker_service):
    """14. Output bounding limits excessively large build stdout/stderr."""
    test_docker_service.simulate_large_output = True
    res = test_docker_service.build_image(image_name="large-output:1.0")
    assert res.success is True
    assert res.output_truncated is True
    assert len(res.stdout) <= test_docker_service.MAX_OUTPUT_CHARS + 100
    assert "[STDOUT TRUNCATED]" in res.stdout


def test_15_build_timeout_enforced(docker_workspace):
    """15. Build timeout is enforced when exceeded."""
    res = DevTestDockerService(workspace=docker_workspace).build_image(
        image_name="timeout-img:1.0",
        timeout_seconds=400.0,  # exceeds maximum 300s
    )
    assert res.success is False
    assert res.status == DockerStatus.REJECTED
    assert "Timeout" in str(res.error_message)


# -----------------------------------------------------------------------------
# 4. Container Execution Tests (16-33)
# -----------------------------------------------------------------------------

def test_16_valid_container_request(test_docker_service):
    """16. Valid container run request from built or approved image succeeds."""
    build_res = test_docker_service.build_image(image_name="runner-app:1.0")
    assert build_res.success is True

    run_res = test_docker_service.run_container(
        image_name="runner-app:1.0",
        command=["node", "index.js"],
        environment={"APP_ENV": "test"},
    )
    assert run_res.success is True
    assert run_res.status == DockerStatus.SUCCESS
    assert run_res.exit_code == 0
    assert any(isinstance(e, TestEvidence) for e in run_res.evidence)


def test_17_unauthorized_image_rejected(test_docker_service):
    """17. Running an unapproved, unbuilt image is rejected with NOT_AUTHORIZED."""
    res = test_docker_service.run_container(image_name="untrusted-random-image:latest")
    assert res.success is False
    assert res.status == DockerStatus.NOT_AUTHORIZED
    assert "NOT_AUTHORIZED" in str(res.error_message)


def test_18_arbitrary_command_restrictions(test_docker_service):
    """18. Non-list command strings or arbitrary CLI arguments are rejected."""
    test_docker_service.build_image(image_name="my-app:1.0")
    res = test_docker_service.run_container(
        image_name="my-app:1.0",
        command="bash -c 'rm -rf /'",  # type: ignore
    )
    assert res.success is False
    assert res.status in (DockerStatus.INVALID_INPUT, DockerStatus.REJECTED)


def test_19_shell_injection_rejected(test_docker_service):
    """19. Shell injection syntax within command tokens is rejected."""
    test_docker_service.build_image(image_name="my-app:1.0")
    for bad_cmd in [
        ["node", "index.js", ";", "rm", "-rf", "/"],
        ["node", "index.js", "&&", "cat", "/etc/shadow"],
        ["node", "`whoami`"],
        ["node", "$PWD"],
    ]:
        res = test_docker_service.run_container(
            image_name="my-app:1.0",
            command=bad_cmd,
        )
        assert res.success is False
        assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


def test_20_privileged_mode_rejected():
    """20. Privileged container mode is forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            privileged=True,  # type: ignore
        )


def test_21_capability_modification_rejected():
    """21. Capability additions (--cap-add) are forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            cap_add=["SYS_ADMIN"],  # type: ignore
        )


def test_22_host_network_rejected():
    """22. Host networking (--network=host) is forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            network_mode="host",  # type: ignore
        )


def test_23_host_pid_rejected():
    """23. Host PID namespace (--pid=host) is forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            pid_mode="host",  # type: ignore
        )


def test_24_host_ipc_rejected():
    """24. Host IPC namespace (--ipc=host) is forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            ipc_mode="host",  # type: ignore
        )


def test_25_volume_mount_rejected():
    """25. Volume mounts (-v, --mount) are forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            volumes=["/etc:/etc"],  # type: ignore
        )


def test_26_docker_socket_mount_rejected():
    """26. Docker socket mounting is strictly forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            bind_mounts=["/var/run/docker.sock:/var/run/docker.sock"],  # type: ignore
        )


def test_27_host_port_publishing_rejected():
    """27. Host port publishing (-p, --publish) is forbidden in DockerRequest schema."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            image_name="my-app:1.0",
            ports={"80/tcp": 8080},  # type: ignore
        )


def test_28_arbitrary_environment_injection_rejected(test_docker_service):
    """28. Host secret keys and dangerous environment variables are rejected."""
    test_docker_service.build_image(image_name="my-app:1.0")
    for bad_env in [
        {"PATH": "/custom/path"},
        {"AWS_SECRET_ACCESS_KEY": "secret123"},
        {"OPENAI_API_KEY": "sk-12345"},
        {"GITHUB_TOKEN": "ghp_123"},
        {"DOCKER_HOST": "tcp://1.2.3.4"},
        {"123INVALID": "val"},
    ]:
        res = test_docker_service.run_container(
            image_name="my-app:1.0",
            environment=bad_env,
        )
        assert res.success is False
        assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


def test_29_timeout_enforced(test_docker_service):
    """29. Container timeout is enforced and returns TIMEOUT status."""
    test_docker_service.build_image(image_name="my-app:1.0")
    test_docker_service.simulate_container_timeout = True
    res = test_docker_service.run_container(
        image_name="my-app:1.0",
        timeout_seconds=5.0,
    )
    assert res.success is False
    assert res.status == DockerStatus.TIMEOUT
    assert res.timed_out is True


def test_30_output_limit_enforced(test_docker_service):
    """30. Container output limit truncation is enforced."""
    test_docker_service.build_image(image_name="my-app:1.0")
    test_docker_service.simulate_large_output = True
    res = test_docker_service.run_container(image_name="my-app:1.0")
    assert res.success is True
    assert res.output_truncated is True
    assert len(res.stdout) <= test_docker_service.MAX_OUTPUT_CHARS + 100


def test_31_cleanup_after_success(test_docker_service):
    """31. Container is cleaned up after successful execution."""
    test_docker_service.build_image(image_name="my-app:1.0")
    res = test_docker_service.run_container(
        image_name="my-app:1.0",
        container_name="test-clean-success",
    )
    assert res.success is True
    # Verify container is not lingering in active state
    inspect_res = test_docker_service.inspect_container("test-clean-success")
    assert inspect_res.status == DockerStatus.CONTAINER_NOT_FOUND


def test_32_cleanup_after_failure(test_docker_service):
    """32. Container is cleaned up after execution failure."""
    test_docker_service.build_image(image_name="my-app:1.0")
    test_docker_service.simulate_container_failure = True
    res = test_docker_service.run_container(
        image_name="my-app:1.0",
        container_name="test-clean-failure",
    )
    assert res.success is False
    inspect_res = test_docker_service.inspect_container("test-clean-failure")
    assert inspect_res.status == DockerStatus.CONTAINER_NOT_FOUND


def test_33_cleanup_after_timeout(test_docker_service):
    """33. Container is cleaned up after timeout."""
    test_docker_service.build_image(image_name="my-app:1.0")
    test_docker_service.simulate_container_timeout = True
    res = test_docker_service.run_container(
        image_name="my-app:1.0",
        container_name="test-clean-timeout",
    )
    assert res.success is False
    assert res.status == DockerStatus.TIMEOUT
    inspect_res = test_docker_service.inspect_container("test-clean-timeout")
    assert inspect_res.status == DockerStatus.CONTAINER_NOT_FOUND


# -----------------------------------------------------------------------------
# 5. Resource Controls Tests (34-36)
# -----------------------------------------------------------------------------

def test_34_memory_limit_above_maximum_rejected(test_docker_service):
    """34. Memory limit exceeding maximum (1g / 1024m) is rejected."""
    test_docker_service.build_image(image_name="my-app:1.0")
    for bad_mem in ["2g", "2048m", "1025m", "invalid_mem", "-512m"]:
        res = test_docker_service.run_container(
            image_name="my-app:1.0",
            memory_limit=bad_mem,
        )
        assert res.success is False
        assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


def test_35_cpu_limit_above_maximum_rejected(test_docker_service):
    """35. CPU limit exceeding maximum (2.0) or below minimum (0.1) is rejected."""
    test_docker_service.build_image(image_name="my-app:1.0")
    for bad_cpu in [2.5, 4.0, 0.0, -1.0, 10.0]:
        res = test_docker_service.run_container(
            image_name="my-app:1.0",
            cpu_limit=bad_cpu,
        )
        assert res.success is False
        assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


def test_36_timeout_above_maximum_rejected(test_docker_service):
    """36. Timeout exceeding maximum (300.0s) or <= 0 is rejected."""
    test_docker_service.build_image(image_name="my-app:1.0")
    for bad_timeout in [301.0, 600.0, 0.0, -10.0]:
        res = test_docker_service.run_container(
            image_name="my-app:1.0",
            timeout_seconds=bad_timeout,
        )
        assert res.success is False
        assert res.status in (DockerStatus.REJECTED, DockerStatus.INVALID_INPUT)


# -----------------------------------------------------------------------------
# 6. Container Lifecycle Tests (37-40)
# -----------------------------------------------------------------------------

def test_37_stop_container(test_docker_service):
    """37. Stopping an active container transitions state and returns CONTAINER_STOPPED."""
    # Simulate a running container in service
    test_docker_service._containers["my-running-c"] = {
        "id": "cid123",
        "name": "my-running-c",
        "image": "node:alpine",
        "status": "running",
        "running": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    res = test_docker_service.stop_container(container_name="my-running-c")
    assert res.success is True
    assert res.status == DockerStatus.CONTAINER_STOPPED
    assert test_docker_service._containers["my-running-c"]["running"] is False


def test_38_remove_container(test_docker_service):
    """38. Removing a container deletes it and returns CONTAINER_REMOVED."""
    test_docker_service._containers["my-stopped-c"] = {
        "id": "cid456",
        "name": "my-stopped-c",
        "image": "node:alpine",
        "status": "exited",
        "running": False,
    }
    res = test_docker_service.remove_container(container_name="my-stopped-c")
    assert res.success is True
    assert res.status == DockerStatus.CONTAINER_REMOVED
    assert "my-stopped-c" not in test_docker_service._containers


def test_39_inspect_container(test_docker_service):
    """39. Inspecting a container returns structured ContainerInspectionResult."""
    test_docker_service._containers["my-inspect-c"] = {
        "id": "cid789",
        "name": "my-inspect-c",
        "image": "node:alpine",
        "status": "running",
        "running": True,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    res = test_docker_service.inspect_container(container_name="my-inspect-c")
    assert res.success is True
    assert res.status == DockerStatus.SUCCESS
    assert res.inspection is not None
    assert res.inspection.container_id == "cid789"
    assert res.inspection.running is True


def test_40_nonexistent_container_handled(test_docker_service):
    """40. Operations on nonexistent container return CONTAINER_NOT_FOUND cleanly."""
    res_stop = test_docker_service.stop_container(container_name="nonexistent-c")
    assert res_stop.success is False
    assert res_stop.status == DockerStatus.CONTAINER_NOT_FOUND

    res_rm = test_docker_service.remove_container(container_name="nonexistent-c")
    assert res_rm.success is False
    assert res_rm.status == DockerStatus.CONTAINER_NOT_FOUND

    res_inspect = test_docker_service.inspect_container(container_name="nonexistent-c")
    assert res_inspect.success is False
    assert res_inspect.status == DockerStatus.CONTAINER_NOT_FOUND


# -----------------------------------------------------------------------------
# 7. Security Implementation Tests (41-50)
# -----------------------------------------------------------------------------

def test_41_no_shell_true_in_implementation():
    """41. Verify implementation does NOT use shell=True anywhere."""
    from executive_twins.docker import docker_service as ds_module
    src = inspect.getsource(ds_module)
    assert "shell=True" not in src


def test_42_no_os_system_in_implementation():
    """42. Verify implementation does NOT use os.system()."""
    from executive_twins.docker import docker_service as ds_module
    src = inspect.getsource(ds_module)
    assert "os.system(" not in src


def test_43_no_eval_in_implementation():
    """43. Verify implementation does NOT use eval()."""
    from executive_twins.docker import docker_service as ds_module
    src = inspect.getsource(ds_module)
    assert "eval(" not in src


def test_44_no_exec_in_implementation():
    """44. Verify implementation does NOT use exec()."""
    from executive_twins.docker import docker_service as ds_module
    src = inspect.getsource(ds_module)
    assert "exec(" not in src


def test_45_no_arbitrary_docker_command_string():
    """45. Verify DockerRequest strictly forbids raw/arbitrary command strings."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.CHECK_AVAILABILITY,
            raw_command="docker run ubuntu",  # type: ignore
        )


def test_46_no_arbitrary_docker_cli_arguments(test_docker_service):
    """46. IDockerService public interface has no generic run/execute CLI method."""
    assert not hasattr(test_docker_service, "execute")
    assert not hasattr(test_docker_service, "run")
    assert not hasattr(test_docker_service, "execute_docker")
    assert not hasattr(test_docker_service, "run_docker")


def test_47_no_host_path_access():
    """47. Verify DockerRequest forbids host volume and bind mount properties."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            host_path="/",  # type: ignore
        )


def test_48_no_docker_socket_access():
    """48. Verify DockerRequest forbids docker socket binding properties."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            docker_socket="/var/run/docker.sock",  # type: ignore
        )


def test_49_no_privileged_execution():
    """49. Verify privileged container parameters cannot be passed."""
    with pytest.raises(Exception):
        DockerRequest(
            operation=DockerOperationType.RUN_CONTAINER,
            privileged=True,  # type: ignore
        )


def test_50_no_remote_manipulation(test_docker_service):
    """50. Remote registry push, login, daemon controls are not exposed."""
    assert not hasattr(test_docker_service, "push_image")
    assert not hasattr(test_docker_service, "login")
    assert not hasattr(test_docker_service, "daemon_control")


# -----------------------------------------------------------------------------
# 8. Specialist Execution Engine Integration Tests (51-56)
# -----------------------------------------------------------------------------

@pytest.fixture
def specialist_setup(docker_workspace):
    """Set up registry, workspace adapter, docker adapter, handlers, and engine."""
    ws_adapter = DevTestWorkspaceAdapter()
    ws_adapter._active_workspaces[docker_workspace.workspace_id] = docker_workspace

    docker_adapter = DevDockerServiceAdapter(
        workspace_adapter=ws_adapter,
        use_mock=True,
        approved_images={"node:alpine", "python:3.11-slim"},
    )

    # Specialists: 1 authorized (Web Dev), 1 unauthorized (Data Analyst), 1 inactive
    web_dev = SpecialistMetadata(
        specialist_id="spec-web-dev",
        name="Web Development Specialist",
        authorized_tools=["docker", "git", "code_generator", "static_analyzer"],
        capabilities=[
            Capability(name="docker_availability", description="Docker availability check"),
            Capability(name="docker_build", description="Docker image build"),
            Capability(name="docker_run", description="Docker container run"),
            Capability(name="docker_stop", description="Docker container stop"),
            Capability(name="docker_remove", description="Docker container removal"),
            Capability(name="docker_inspect", description="Docker container inspection"),
        ],
        status=SpecialistStatus.ACTIVE,
    )

    unauthorized_spec = SpecialistMetadata(
        specialist_id="spec-data-analyst",
        name="Data Analyst Specialist",
        authorized_tools=["data_analyzer"],
        capabilities=[],
        status=SpecialistStatus.ACTIVE,
    )

    inactive_spec = SpecialistMetadata(
        specialist_id="spec-inactive-web-dev",
        name="Inactive Web Specialist",
        authorized_tools=["docker"],
        capabilities=[
            Capability(name="docker_availability", description="Docker availability check"),
        ],
        status=SpecialistStatus.INACTIVE,
    )

    registry = InMemorySpecialistRegistryAdapter()
    registry.register_specialist(web_dev)
    registry.register_specialist(unauthorized_spec)
    registry.register_specialist(inactive_spec)

    engine = SpecialistExecutionEngine(registry_client=registry)
    engine.register_handler(DockerAvailabilityCapabilityHandler(docker_adapter))
    engine.register_handler(DockerBuildCapabilityHandler(docker_adapter))
    engine.register_handler(DockerRunCapabilityHandler(docker_adapter))
    engine.register_handler(DockerStopCapabilityHandler(docker_adapter))
    engine.register_handler(DockerRemoveCapabilityHandler(docker_adapter))
    engine.register_handler(DockerInspectCapabilityHandler(docker_adapter))

    adapter = SpecialistExecutionAdapter(execution_engine=engine)
    return {
        "engine": engine,
        "adapter": adapter,
        "docker_adapter": docker_adapter,
        "workspace_id": docker_workspace.workspace_id,
    }


def test_51_authorized_specialist_can_invoke_docker_capability(specialist_setup):
    """51. Authorized Web Development Specialist can execute docker capabilities."""
    req = DelegationRequest(
        delegation_id="del-docker-01",
        parent_task_id="task-docker-01",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Verify Docker availability",
        task="docker_availability",
        required_capabilities=["docker_availability"],
        inputs={"workspace_id": specialist_setup["workspace_id"]},
        expected_output="Docker availability report",
        security_context=SecurityContext(is_authenticated=True, security_level="standard"),
    )
    result: DelegationResult = specialist_setup["adapter"].execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED
    assert "available" in result.output.lower()


def test_52_unauthorized_specialist_blocked(specialist_setup):
    """52. Unauthorized specialist is blocked with NOT_AUTHORIZED."""
    req = DelegationRequest(
        delegation_id="del-docker-02",
        parent_task_id="task-docker-02",
        executive_twin_id="twin-cto",
        specialist_id="spec-data-analyst",
        objective="Unauthorized docker build",
        task="docker_build",
        required_capabilities=["docker_build"],
        inputs={
            "workspace_id": specialist_setup["workspace_id"],
            "image_name": "app:1.0",
        },
        expected_output="Docker build result",
        security_context=SecurityContext(is_authenticated=True, security_level="standard"),
    )
    result: DelegationResult = specialist_setup["adapter"].execute_delegation(req)
    assert result.status == "FAILED"
    assert "AUTHORIZATION_DENIED" in result.output


def test_53_inactive_specialist_blocked(specialist_setup):
    """53. Inactive specialist is blocked from executing Docker capabilities."""
    req = DelegationRequest(
        delegation_id="del-docker-03",
        parent_task_id="task-docker-03",
        executive_twin_id="twin-cto",
        specialist_id="spec-inactive-web-dev",
        objective="Inactive docker check",
        task="docker_availability",
        required_capabilities=["docker_availability"],
        inputs={"workspace_id": specialist_setup["workspace_id"]},
        expected_output="Docker availability report",
        security_context=SecurityContext(is_authenticated=True, security_level="standard"),
    )
    result: DelegationResult = specialist_setup["adapter"].execute_delegation(req)
    assert result.status == "FAILED"
    assert "CAPABILITY_UNAVAILABLE" in result.output or "inactive" in result.output


def test_54_correct_handler_routing(specialist_setup):
    """54. DelegationRequest correctly routes to DockerBuildCapabilityHandler."""
    req = DelegationRequest(
        delegation_id="del-docker-04",
        parent_task_id="task-docker-04",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Build test image",
        task="docker_build",
        required_capabilities=["docker_build"],
        inputs={
            "workspace_id": specialist_setup["workspace_id"],
            "image_name": "test-build:1.0",
            "dockerfile_path": "Dockerfile",
            "build_context": ".",
        },
        expected_output="Docker build result",
        security_context=SecurityContext(is_authenticated=True, security_level="standard"),
    )
    result: DelegationResult = specialist_setup["adapter"].execute_delegation(req)
    assert result.status == "SUCCESS"
    assert "Successfully built image" in result.output
    assert "docker://test-build:1.0" in result.artifacts


def test_55_evidence_generated(specialist_setup):
    """55. Successful Docker capability execution produces empirical ExecutionLogEvidence."""
    req = DelegationRequest(
        delegation_id="del-docker-05",
        parent_task_id="task-docker-05",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Build image with evidence",
        task="docker_build",
        required_capabilities=["docker_build"],
        inputs={
            "workspace_id": specialist_setup["workspace_id"],
            "image_name": "evidence-img:1.0",
        },
        expected_output="Docker build result",
        security_context=SecurityContext(is_authenticated=True, security_level="standard"),
    )
    result: DelegationResult = specialist_setup["adapter"].execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.evidence is not None
    assert len(result.evidence.items) > 0
    assert any(isinstance(e, ExecutionLogEvidence) for e in result.evidence.items)


def test_56_verification_evidence_generated(specialist_setup):
    """56. Successful Docker capability execution produces VerificationEvidence."""
    req = DelegationRequest(
        delegation_id="del-docker-06",
        parent_task_id="task-docker-06",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Check availability with verification evidence",
        task="docker_availability",
        required_capabilities=["docker_availability"],
        inputs={"workspace_id": specialist_setup["workspace_id"]},
        expected_output="Docker availability report",
        security_context=SecurityContext(is_authenticated=True, security_level="standard"),
    )
    result: DelegationResult = specialist_setup["adapter"].execute_delegation(req)
    assert result.status == "SUCCESS"
    assert any(isinstance(e, VerificationEvidence) for e in result.evidence.items)


# -----------------------------------------------------------------------------
# 9. Regression Tests (57-62)
# -----------------------------------------------------------------------------

def test_57_specialist_execution_engine_remains_functional():
    """57. Core SpecialistExecutionEngine default handlers remain functional."""
    registry = InMemorySpecialistRegistryAdapter()
    spec = SpecialistMetadata(
        specialist_id="spec-core-test",
        name="Core Tester",
        authorized_tools=["static_analyzer"],
        capabilities=[Capability(name="code_analysis", description="Code analysis")],
        status=SpecialistStatus.ACTIVE,
    )
    registry.register_specialist(spec)
    engine = SpecialistExecutionEngine(registry_client=registry)
    adapter = SpecialistExecutionAdapter(execution_engine=engine)

    req = DelegationRequest(
        delegation_id="del-core-01",
        parent_task_id="task-core-01",
        executive_twin_id="twin-cto",
        specialist_id="spec-core-test",
        objective="Run static analysis",
        task="code_analysis",
        required_capabilities=["code_analysis"],
        inputs={"source_code_path": "src/app.py"},
        expected_output="Code analysis report",
        security_context=SecurityContext(is_authenticated=True, security_level="standard"),
    )
    res = adapter.execute_delegation(req)
    assert res.status == "SUCCESS"


def test_58_workspace_remains_functional(docker_workspace):
    """58. Workspace operations remain functional."""
    res_write = docker_workspace.write_file("test.txt", "content")
    assert res_write.success is True
    res_read = docker_workspace.read_file("test.txt")
    assert res_read.success is True
    assert res_read.content == "content"


def test_59_files_api_remains_functional(docker_workspace):
    """59. FileService operations remain functional."""
    file_service = FileService(workspace=docker_workspace)
    res = file_service.list_files()
    assert res.success is True


def test_60_command_execution_remains_functional(docker_workspace):
    """60. ControlledCommandExecutor remains functional."""
    executor = ControlledCommandExecutor(workspace=docker_workspace)
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "unittest", "--help"],
        workspace_id=docker_workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is True


def test_61_git_integration_remains_functional(docker_workspace):
    """61. ControlledGitService remains functional."""
    git_service = ControlledGitService(workspace=docker_workspace)
    res = git_service.status()
    # Workspace has no .git folder, so NOT_A_REPOSITORY is expected and verified
    assert res.status == "NOT_A_REPOSITORY"


def test_62_full_test_suite_passes(test_docker_service):
    """62. Verify overall Docker service lifecycle and execution integrity."""
    # Build image
    build_res = test_docker_service.build_image(image_name="full-lifecycle:1.0")
    assert build_res.success is True

    # Run container
    run_res = test_docker_service.run_container(
        image_name="full-lifecycle:1.0",
        command=["node", "index.js"],
    )
    assert run_res.success is True
    assert run_res.status == DockerStatus.SUCCESS
