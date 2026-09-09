"""
DEV/TEST adapters and registered Docker capability execution handlers.
Provides deterministic simulated Docker services for testing and concrete capability handlers
for integration with SpecialistExecutionEngine and SecurityGuard.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from executive_twins.docker.docker_service import (
    BLOCKED_ENV_EXACT,
    BLOCKED_ENV_PREFIXES,
    CONTAINER_NAME_PATTERN,
    ENV_KEY_PATTERN,
    FORBIDDEN_SHELL_PATTERNS,
    IMAGE_NAME_PATTERN,
    MEMORY_LIMIT_PATTERN,
    ControlledDockerService,
)
from executive_twins.docker.interfaces import IDockerService
from executive_twins.docker.models import (
    ContainerInspectionResult,
    DockerOperationType,
    DockerResult,
    DockerStatus,
)
from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import SpecialistMetadata
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter
from executive_twins.workspace.interfaces import ISoftwareWorkspace


class DevTestDockerService(IDockerService):
    """
    High-fidelity deterministic simulated Docker service for DEV/TEST environments.
    Strictly applies the identical security checks, path validations, and resource bounds
    as ControlledDockerService without requiring an active host Docker daemon.
    """

    DEFAULT_TIMEOUT_SECONDS = 30.0
    MAX_TIMEOUT_SECONDS = 300.0
    MAX_OUTPUT_CHARS = 100_000
    MAX_MEMORY_BYTES = 1024 * 1024 * 1024
    MAX_CPUS = 2.0
    MIN_CPUS = 0.1

    def __init__(
        self,
        workspace: Optional[ISoftwareWorkspace] = None,
        approved_images: Optional[Set[str]] = None,
        simulate_docker_unavailable: bool = False,
    ) -> None:
        self._workspace = workspace
        self._approved_images: Set[str] = set(approved_images or [])
        self._built_images: Set[str] = set()
        self._containers: Dict[str, Dict[str, Any]] = {}
        self.simulate_docker_unavailable = simulate_docker_unavailable
        self.simulate_build_failure = False
        self.simulate_container_timeout = False
        self.simulate_container_failure = False
        self.simulate_large_output = False

    @property
    def workspace(self) -> Optional[ISoftwareWorkspace]:
        return self._workspace

    # -------------------------------------------------------------------------
    # Validation Helpers
    # -------------------------------------------------------------------------

    def _validate_image_name(self, image_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not image_name or not isinstance(image_name, str):
            return False, "INVALID_INPUT: Image name must be a non-empty string."

        name = image_name.strip()
        if not name:
            return False, "INVALID_INPUT: Image name cannot be empty or whitespace only."

        if len(name) > 128:
            return False, "INVALID_INPUT: Image name exceeds maximum length of 128 characters."

        if name.startswith("-"):
            return False, "INVALID_INPUT: Image name cannot start with '-' (option injection prevented)."

        for pat in FORBIDDEN_SHELL_PATTERNS:
            if pat in name:
                return False, f"INVALID_INPUT: Image name contains forbidden shell pattern '{pat}'."

        if "://" in name or name.startswith("/") or name.endswith("/"):
            return False, "INVALID_INPUT: Remote URL schemes and path-like registry references are rejected in V1."

        if not IMAGE_NAME_PATTERN.match(name):
            return False, f"INVALID_INPUT: Image name '{name}' does not match allowed local image format."

        return True, None

    def _validate_container_name(self, container_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not container_name or not isinstance(container_name, str):
            return False, "INVALID_INPUT: Container name must be a non-empty string."

        name = container_name.strip()
        if not name:
            return False, "INVALID_INPUT: Container name cannot be empty or whitespace only."

        if len(name) > 64:
            return False, "INVALID_INPUT: Container name exceeds maximum length of 64 characters."

        if name.startswith("-"):
            return False, "INVALID_INPUT: Container name cannot start with '-' (option injection prevented)."

        for pat in FORBIDDEN_SHELL_PATTERNS:
            if pat in name:
                return False, f"INVALID_INPUT: Container name contains forbidden shell pattern '{pat}'."

        if not CONTAINER_NAME_PATTERN.match(name):
            return False, f"INVALID_INPUT: Container name '{name}' contains invalid characters."

        return True, None

    def _validate_environment(
        self, environment: Optional[Dict[str, str]]
    ) -> Tuple[bool, Optional[str], Dict[str, str]]:
        if environment is None:
            return True, None, {}

        if not isinstance(environment, dict):
            return False, "INVALID_INPUT: Environment variables must be a key-value dictionary.", {}

        cleaned: Dict[str, str] = {}
        for k, v in environment.items():
            if not isinstance(k, str) or not isinstance(v, str):
                return False, "INVALID_INPUT: Environment keys and values must be strings.", {}

            key_clean = k.strip()
            val_clean = v

            if not ENV_KEY_PATTERN.match(key_clean):
                return False, f"INVALID_INPUT: Environment variable key '{key_clean}' is invalid.", {}

            key_upper = key_clean.upper()
            if key_upper in BLOCKED_ENV_EXACT or any(key_upper.startswith(prefix) for prefix in BLOCKED_ENV_PREFIXES):
                return False, f"SECURITY_ERROR: Environment variable key '{key_clean}' is blocked to prevent credential/host leaks.", {}

            if len(val_clean) > 1024:
                return False, f"INVALID_INPUT: Environment value for '{key_clean}' exceeds maximum length of 1024 characters.", {}

            for c in val_clean:
                if c == "\0" or (ord(c) < 32 and c not in ("\t", "\n", "\r")):
                    return False, f"INVALID_INPUT: Environment value for '{key_clean}' contains forbidden control characters.", {}

            cleaned[key_clean] = val_clean

        return True, None, cleaned

    def _validate_command(self, command: Optional[List[str]]) -> Tuple[bool, Optional[str]]:
        if command is None:
            return True, None

        if not isinstance(command, list):
            return False, "INVALID_INPUT: Command must be a structured list of string tokens."

        for token in command:
            if not isinstance(token, str):
                return False, "INVALID_INPUT: All command tokens must be strings."

            for pat in FORBIDDEN_SHELL_PATTERNS:
                if pat in token:
                    return False, f"SECURITY_ERROR: Command token '{token}' contains forbidden shell operator '{pat}'."

        return True, None

    def _validate_memory_limit(self, memory_limit: Optional[str]) -> Tuple[bool, Optional[str], str]:
        if memory_limit is None:
            return True, None, "512m"

        if not isinstance(memory_limit, str):
            return False, "INVALID_INPUT: Memory limit must be a string.", ""

        mem_clean = memory_limit.strip()
        match = MEMORY_LIMIT_PATTERN.match(mem_clean)
        if not match:
            return False, f"INVALID_INPUT: Invalid memory limit format '{mem_clean}'.", ""

        num = int(match.group(1))
        unit = match.group(2).lower()
        multiplier = 1024 * 1024 if unit == "m" else 1024 * 1024 * 1024
        total_bytes = num * multiplier

        if total_bytes > self.MAX_MEMORY_BYTES or total_bytes <= 0:
            return False, f"REJECTED: Memory limit '{mem_clean}' exceeds maximum allowed limit of 1g (1024m).", ""

        return True, None, mem_clean.lower()

    def _validate_cpu_limit(self, cpu_limit: Optional[float]) -> Tuple[bool, Optional[str], float]:
        if cpu_limit is None:
            return True, None, 1.0

        if not isinstance(cpu_limit, (int, float)):
            return False, "INVALID_INPUT: CPU limit must be a number.", 0.0

        cpu_val = float(cpu_limit)
        if cpu_val < self.MIN_CPUS or cpu_val > self.MAX_CPUS:
            return False, f"REJECTED: CPU limit {cpu_val} is outside allowed range ({self.MIN_CPUS} to {self.MAX_CPUS}).", 0.0

        return True, None, cpu_val

    def _validate_timeout(self, timeout_seconds: Optional[float]) -> Tuple[bool, Optional[str], float]:
        if timeout_seconds is None:
            return True, None, self.DEFAULT_TIMEOUT_SECONDS

        if not isinstance(timeout_seconds, (int, float)):
            return False, "INVALID_INPUT: Timeout must be a number.", 0.0

        timeout_val = float(timeout_seconds)
        if timeout_val <= 0.0 or timeout_val > self.MAX_TIMEOUT_SECONDS:
            return False, f"REJECTED: Timeout {timeout_val}s is outside allowed range (0.1s to {self.MAX_TIMEOUT_SECONDS}s).", 0.0

        return True, None, timeout_val

    def _validate_workspace_path(
        self,
        path_str: Optional[str],
        default_rel: str = ".",
        must_exist: bool = True,
        is_file: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        if not self._workspace or not self._workspace.workspace_exists():
            return False, "WORKSPACE_NOT_FOUND: Workspace is not configured or inactive.", None

        ws_root = Path(self._workspace.root_path).resolve()
        target = path_str.strip() if path_str and isinstance(path_str, str) else default_rel

        if target.startswith("-"):
            return False, f"INVALID_INPUT: Path '{target}' cannot start with '-'.", None

        for pat in FORBIDDEN_SHELL_PATTERNS:
            if pat in target:
                return False, f"INVALID_INPUT: Path '{target}' contains forbidden character '{pat}'.", None

        p_obj = Path(target)
        for part in p_obj.parts:
            if part == "..":
                return False, f"PATH_TRAVERSAL_REJECTED: Parent traversal '..' rejected in '{target}'.", None

        if p_obj.is_absolute() or (len(target) > 1 and target[1] == ":"):
            return False, f"PATH_OUTSIDE_WORKSPACE_REJECTED: Absolute path '{target}' is not workspace-relative.", None

        full_path = ws_root / p_obj
        try:
            if full_path.exists() or full_path.is_symlink():
                resolved_path = full_path.resolve()
            else:
                resolved_parent = full_path.parent.resolve()
                resolved_path = resolved_parent / full_path.name
        except Exception as e:
            return False, f"PATH_SECURITY_ERROR: Invalid path '{target}': {e}", None

        try:
            resolved_path.relative_to(ws_root)
        except ValueError:
            return False, f"PATH_OUTSIDE_WORKSPACE_REJECTED: Path '{target}' escapes workspace root.", None

        if must_exist and not resolved_path.exists():
            return False, f"PATH_NOT_FOUND: Path '{target}' does not exist inside workspace.", None

        if is_file and must_exist and not resolved_path.is_file():
            return False, f"INVALID_INPUT: Path '{target}' is not a valid file.", None

        return True, None, resolved_path

    # -------------------------------------------------------------------------
    # Public IDockerService Operations
    # -------------------------------------------------------------------------

    def check_availability(self) -> DockerResult:
        start_time = datetime.now(timezone.utc)
        if self.simulate_docker_unavailable:
            return DockerResult(
                success=False,
                operation=DockerOperationType.CHECK_AVAILABILITY,
                status=DockerStatus.DOCKER_UNAVAILABLE,
                message="DOCKER_UNAVAILABLE: Docker daemon is not running.",
                error_type="DOCKER_UNAVAILABLE",
                error_message="Docker daemon is not running.",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        facts = [
            FactItem(
                statement="Docker daemon is active and operational (simulated v24.0.7).",
                state=FactState.FACT,
                source="docker_service",
            )
        ]
        ev = [
            ExecutionLogEvidence(
                evidence_id=f"ev-docker-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-docker-{uuid.uuid4().hex[:8]}",
                log_snippet="DOCKER_OP: CHECK_AVAILABILITY\nEXIT: 0\nSTDOUT: 24.0.7",
                exit_code=0,
                description="Controlled Docker availability check log",
            ),
            VerificationEvidence(
                evidence_id=f"ev-docker-verif-{uuid.uuid4().hex[:8]}",
                verifier_id="DevTestDockerService",
                verified_status="VERIFIED",
                description="Docker availability verified",
            ),
        ]
        return DockerResult(
            success=True,
            operation=DockerOperationType.CHECK_AVAILABILITY,
            status=DockerStatus.SUCCESS,
            message="Docker is available (simulated v24.0.7).",
            exit_code=0,
            stdout="24.0.7",
            started_at=start_time,
            finished_at=datetime.now(timezone.utc),
            facts=facts,
            evidence=ev,
        )

    def build_image(
        self,
        image_name: str,
        dockerfile_path: str = "Dockerfile",
        build_context: str = ".",
        timeout_seconds: Optional[float] = None,
    ) -> DockerResult:
        start_time = datetime.now(timezone.utc)

        valid_img, img_err = self._validate_image_name(image_name)
        if not valid_img:
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=DockerStatus.INVALID_INPUT,
                error_type="INVALID_IMAGE_NAME",
                error_message=img_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        valid_to, to_err, timeout_val = self._validate_timeout(timeout_seconds)
        if not valid_to:
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=DockerStatus.REJECTED,
                error_type="INVALID_TIMEOUT",
                error_message=to_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        if not self._workspace or not self._workspace.workspace_exists():
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=DockerStatus.FAILED,
                error_type="WORKSPACE_NOT_FOUND",
                error_message=f"Workspace '{getattr(self._workspace, 'workspace_id', 'None')}' not found.",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        valid_df, df_err, resolved_df = self._validate_workspace_path(
            dockerfile_path, default_rel="Dockerfile", must_exist=True, is_file=True
        )
        if not valid_df:
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=DockerStatus.REJECTED if "TRAVERSAL" in str(df_err) or "OUTSIDE" in str(df_err) else DockerStatus.INVALID_INPUT,
                error_type="INVALID_DOCKERFILE_PATH",
                error_message=df_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        valid_bc, bc_err, resolved_bc = self._validate_workspace_path(
            build_context, default_rel=".", must_exist=True, is_file=False
        )
        if not valid_bc:
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=DockerStatus.REJECTED if "TRAVERSAL" in str(bc_err) or "OUTSIDE" in str(bc_err) else DockerStatus.INVALID_INPUT,
                error_type="INVALID_BUILD_CONTEXT",
                error_message=bc_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        if self.simulate_build_failure:
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=DockerStatus.IMAGE_BUILD_FAILED,
                image_name=image_name,
                exit_code=1,
                stderr="SIMULATED_BUILD_FAILURE: Step failed.",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
                error_type="IMAGE_BUILD_FAILED",
                error_message="SIMULATED_BUILD_FAILURE: Step failed.",
            )

        self._built_images.add(image_name)
        img_id = f"sha256:{hashlib.sha256(image_name.encode()).hexdigest()[:12]}"
        build_output = f"Step 1/2 : FROM node:alpine\nStep 2/2 : CMD node index.js\nSuccessfully built {img_id}\nSuccessfully tagged {image_name}"
        is_trunc = False
        if self.simulate_large_output:
            build_output = build_output + ("\n" + "A" * 120_000)
            build_output = build_output[: self.MAX_OUTPUT_CHARS] + "\n... [STDOUT TRUNCATED]"
            is_trunc = True

        facts = [
            FactItem(
                statement=f"Successfully built Docker image '{image_name}' ({img_id}).",
                state=FactState.FACT,
                source="docker_service",
            )
        ]
        ev = [
            ExecutionLogEvidence(
                evidence_id=f"ev-docker-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-docker-{uuid.uuid4().hex[:8]}",
                log_snippet=f"DOCKER_OP: BUILD_IMAGE\nCMD: docker build -t {image_name} .\nEXIT: 0",
                exit_code=0,
                description=f"Docker image build log for '{image_name}'",
            ),
            ArtifactEvidence(
                evidence_id=f"ev-art-img-{uuid.uuid4().hex[:8]}",
                artifact_uri=f"docker://{image_name}",
                mime_type="application/vnd.docker.container.image.v1+json",
                description=f"Built Docker image artifact '{image_name}'",
            ),
            VerificationEvidence(
                evidence_id=f"ev-docker-verif-{uuid.uuid4().hex[:8]}",
                verifier_id="DevTestDockerService",
                verified_status="VERIFIED",
                description=f"Docker image build verified for '{image_name}'",
            ),
        ]
        return DockerResult(
            success=True,
            operation=DockerOperationType.BUILD_IMAGE,
            status=DockerStatus.SUCCESS,
            message=f"Successfully built image '{image_name}'.",
            image_id=img_id,
            image_name=image_name,
            exit_code=0,
            stdout=build_output,
            output_truncated=is_trunc,
            started_at=start_time,
            finished_at=datetime.now(timezone.utc),
            duration_seconds=0.1,
            facts=facts,
            evidence=ev,
        )

    def run_container(
        self,
        image_name: str,
        container_name: Optional[str] = None,
        command: Optional[List[str]] = None,
        environment: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[float] = None,
        memory_limit: Optional[str] = None,
        cpu_limit: Optional[float] = None,
    ) -> DockerResult:
        start_time = datetime.now(timezone.utc)

        valid_img, img_err = self._validate_image_name(image_name)
        if not valid_img:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.INVALID_INPUT,
                error_type="INVALID_IMAGE_NAME",
                error_message=img_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        if image_name not in self._built_images and image_name not in self._approved_images:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.NOT_AUTHORIZED,
                image_name=image_name,
                error_type="UNAUTHORIZED_IMAGE",
                error_message=f"NOT_AUTHORIZED: Image '{image_name}' was not built by this service and is not in approved allowlist.",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        c_name = container_name
        if not c_name:
            ws_id = getattr(self._workspace, "workspace_id", "ws")
            c_name = f"cws-{re.sub(r'[^a-zA-Z0-9]', '', ws_id)[:8]}-{uuid.uuid4().hex[:8]}"
        else:
            valid_cn, cn_err = self._validate_container_name(c_name)
            if not valid_cn:
                return DockerResult(
                    success=False,
                    operation=DockerOperationType.RUN_CONTAINER,
                    status=DockerStatus.INVALID_INPUT,
                    error_type="INVALID_CONTAINER_NAME",
                    error_message=cn_err,
                    started_at=start_time,
                    finished_at=datetime.now(timezone.utc),
                )

        valid_cmd, cmd_err = self._validate_command(command)
        if not valid_cmd:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.REJECTED,
                error_type="SECURITY_COMMAND_REJECTED",
                error_message=cmd_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        valid_env, env_err, cleaned_env = self._validate_environment(environment)
        if not valid_env:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.REJECTED if "SECURITY" in str(env_err) else DockerStatus.INVALID_INPUT,
                error_type="INVALID_ENVIRONMENT",
                error_message=env_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        valid_mem, mem_err, mem_val = self._validate_memory_limit(memory_limit)
        if not valid_mem:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.REJECTED if "REJECTED" in str(mem_err) else DockerStatus.INVALID_INPUT,
                error_type="INVALID_MEMORY_LIMIT",
                error_message=mem_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        valid_cpu, cpu_err, cpu_val = self._validate_cpu_limit(cpu_limit)
        if not valid_cpu:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.REJECTED if "REJECTED" in str(cpu_err) else DockerStatus.INVALID_INPUT,
                error_type="INVALID_CPU_LIMIT",
                error_message=cpu_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        valid_to, to_err, timeout_val = self._validate_timeout(timeout_seconds)
        if not valid_to:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.REJECTED,
                error_type="INVALID_TIMEOUT",
                error_message=to_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        c_id = uuid.uuid4().hex[:12]
        self._containers[c_name] = {
            "id": c_id,
            "name": c_name,
            "image": image_name,
            "status": "running",
            "running": True,
            "started_at": start_time.isoformat(),
        }

        if self.simulate_container_timeout:
            self._containers[c_name]["status"] = "exited"
            self._containers[c_name]["running"] = False
            self._containers.pop(c_name, None)
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.TIMEOUT,
                image_name=image_name,
                container_id=c_id,
                container_name=c_name,
                timed_out=True,
                exit_code=124,
                stderr=f"EXECUTION_TIMEOUT: Container '{c_name}' timed out after {timeout_val}s.",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
                error_type="CONTAINER_TIMEOUT",
                error_message=f"EXECUTION_TIMEOUT: Container '{c_name}' timed out after {timeout_val}s.",
            )

        if self.simulate_container_failure:
            self._containers[c_name]["status"] = "exited"
            self._containers[c_name]["running"] = False
            self._containers.pop(c_name, None)
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.CONTAINER_FAILED,
                image_name=image_name,
                container_id=c_id,
                container_name=c_name,
                exit_code=1,
                stderr="CONTAINER_EXECUTION_ERROR: Process exited with status 1",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
                error_type="CONTAINER_FAILED",
                error_message="Process exited with status 1",
            )

        cmd_str = " ".join(command) if command else ""
        stdout_msg = f"Container output for {image_name}: {cmd_str}\nStatus: PASS"
        is_trunc = False
        if self.simulate_large_output:
            stdout_msg = stdout_msg + ("\n" + "B" * 120_000)
            stdout_msg = stdout_msg[: self.MAX_OUTPUT_CHARS] + "\n... [STDOUT TRUNCATED]"
            is_trunc = True

        self._containers[c_name]["status"] = "exited"
        self._containers[c_name]["running"] = False
        self._containers.pop(c_name, None)

        facts = [
            FactItem(
                statement=f"Container '{c_name}' completed execution successfully (exit code: 0).",
                state=FactState.FACT,
                source="docker_service",
            )
        ]
        ev = [
            ExecutionLogEvidence(
                evidence_id=f"ev-docker-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-docker-{uuid.uuid4().hex[:8]}",
                log_snippet=f"DOCKER_OP: RUN_CONTAINER\nCONTAINER: {c_name}\nEXIT: 0\nSTDOUT:\n{stdout_msg[:200]}",
                exit_code=0,
                description=f"Container run execution log for '{c_name}'",
            ),
            TestEvidence(
                evidence_id=f"ev-docker-test-{uuid.uuid4().hex[:8]}",
                suite_name=f"container_exec:{image_name}",
                tests_passed=1,
                tests_failed=0,
                description=f"Container test verification for '{image_name}'",
            ),
            VerificationEvidence(
                evidence_id=f"ev-docker-verif-{uuid.uuid4().hex[:8]}",
                verifier_id="DevTestDockerService",
                verified_status="VERIFIED",
                description=f"Container execution verified for '{c_name}'",
            ),
        ]

        return DockerResult(
            success=True,
            operation=DockerOperationType.RUN_CONTAINER,
            status=DockerStatus.SUCCESS,
            message=f"Container '{c_name}' completed execution successfully.",
            image_name=image_name,
            container_id=c_id,
            container_name=c_name,
            exit_code=0,
            stdout=stdout_msg,
            output_truncated=is_trunc,
            started_at=start_time,
            finished_at=datetime.now(timezone.utc),
            duration_seconds=0.1,
            facts=facts,
            evidence=ev,
        )

    def stop_container(
        self,
        container_name: str,
        timeout_seconds: Optional[float] = 10.0,
    ) -> DockerResult:
        start_time = datetime.now(timezone.utc)
        valid_cn, cn_err = self._validate_container_name(container_name)
        if not valid_cn:
            return DockerResult(
                success=False,
                operation=DockerOperationType.STOP_CONTAINER,
                status=DockerStatus.INVALID_INPUT,
                error_type="INVALID_CONTAINER_NAME",
                error_message=cn_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        if container_name not in self._containers:
            return DockerResult(
                success=False,
                operation=DockerOperationType.STOP_CONTAINER,
                status=DockerStatus.CONTAINER_NOT_FOUND,
                container_name=container_name,
                error_type="CONTAINER_NOT_FOUND",
                error_message=f"No such container: '{container_name}'",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        self._containers[container_name]["running"] = False
        self._containers[container_name]["status"] = "exited"

        facts = [
            FactItem(
                statement=f"Stopped container '{container_name}'.",
                state=FactState.FACT,
                source="docker_service",
            )
        ]
        ev = [
            ExecutionLogEvidence(
                evidence_id=f"ev-docker-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-docker-{uuid.uuid4().hex[:8]}",
                log_snippet=f"DOCKER_OP: STOP_CONTAINER\nCONTAINER: {container_name}\nEXIT: 0",
                exit_code=0,
                description=f"Container stop log for '{container_name}'",
            )
        ]
        return DockerResult(
            success=True,
            operation=DockerOperationType.STOP_CONTAINER,
            status=DockerStatus.CONTAINER_STOPPED,
            message=f"Container '{container_name}' was stopped.",
            container_name=container_name,
            exit_code=0,
            started_at=start_time,
            finished_at=datetime.now(timezone.utc),
            facts=facts,
            evidence=ev,
        )

    def remove_container(
        self,
        container_name: str,
        force: bool = False,
    ) -> DockerResult:
        start_time = datetime.now(timezone.utc)
        valid_cn, cn_err = self._validate_container_name(container_name)
        if not valid_cn:
            return DockerResult(
                success=False,
                operation=DockerOperationType.REMOVE_CONTAINER,
                status=DockerStatus.INVALID_INPUT,
                error_type="INVALID_CONTAINER_NAME",
                error_message=cn_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        if container_name not in self._containers:
            return DockerResult(
                success=False,
                operation=DockerOperationType.REMOVE_CONTAINER,
                status=DockerStatus.CONTAINER_NOT_FOUND,
                container_name=container_name,
                error_type="CONTAINER_NOT_FOUND",
                error_message=f"No such container: '{container_name}'",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        self._containers.pop(container_name, None)

        facts = [
            FactItem(
                statement=f"Removed container '{container_name}'.",
                state=FactState.FACT,
                source="docker_service",
            )
        ]
        ev = [
            ExecutionLogEvidence(
                evidence_id=f"ev-docker-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-docker-{uuid.uuid4().hex[:8]}",
                log_snippet=f"DOCKER_OP: REMOVE_CONTAINER\nCONTAINER: {container_name}\nEXIT: 0",
                exit_code=0,
                description=f"Container remove log for '{container_name}'",
            )
        ]
        return DockerResult(
            success=True,
            operation=DockerOperationType.REMOVE_CONTAINER,
            status=DockerStatus.CONTAINER_REMOVED,
            message=f"Container '{container_name}' was removed.",
            container_name=container_name,
            exit_code=0,
            started_at=start_time,
            finished_at=datetime.now(timezone.utc),
            facts=facts,
            evidence=ev,
        )

    def inspect_container(
        self,
        container_name: str,
    ) -> DockerResult:
        start_time = datetime.now(timezone.utc)
        valid_cn, cn_err = self._validate_container_name(container_name)
        if not valid_cn:
            return DockerResult(
                success=False,
                operation=DockerOperationType.INSPECT_CONTAINER,
                status=DockerStatus.INVALID_INPUT,
                error_type="INVALID_CONTAINER_NAME",
                error_message=cn_err,
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        if container_name not in self._containers:
            return DockerResult(
                success=False,
                operation=DockerOperationType.INSPECT_CONTAINER,
                status=DockerStatus.CONTAINER_NOT_FOUND,
                container_name=container_name,
                error_type="CONTAINER_NOT_FOUND",
                error_message=f"No such container: '{container_name}'",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        c_info = self._containers[container_name]
        inspection_obj = ContainerInspectionResult(
            container_id=c_info["id"],
            container_name=container_name,
            image=c_info["image"],
            status=c_info["status"],
            running=c_info["running"],
            started_at=c_info.get("started_at"),
        )

        facts = [
            FactItem(
                statement=f"Container '{container_name}' state: status='{inspection_obj.status}', running={inspection_obj.running}.",
                state=FactState.FACT,
                source="docker_service",
            )
        ]
        ev = [
            ExecutionLogEvidence(
                evidence_id=f"ev-docker-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-docker-{uuid.uuid4().hex[:8]}",
                log_snippet=f"DOCKER_OP: INSPECT_CONTAINER\nCONTAINER: {container_name}\nSTATE: {inspection_obj.status}",
                exit_code=0,
                description=f"Container inspection log for '{container_name}'",
            )
        ]
        return DockerResult(
            success=True,
            operation=DockerOperationType.INSPECT_CONTAINER,
            status=DockerStatus.SUCCESS,
            container_id=inspection_obj.container_id,
            container_name=container_name,
            image_name=inspection_obj.image,
            exit_code=0,
            inspection=inspection_obj,
            started_at=start_time,
            finished_at=datetime.now(timezone.utc),
            facts=facts,
            evidence=ev,
        )


class DevDockerServiceAdapter:
    """
    DEV/TEST Adapter: Manages IDockerService instances for active workspaces.
    Supports either DevTestDockerService (deterministic test simulation) or ControlledDockerService.
    """

    def __init__(
        self,
        workspace_adapter: Optional[DevTestWorkspaceAdapter] = None,
        use_mock: bool = True,
        approved_images: Optional[Set[str]] = None,
    ) -> None:
        self.workspace_adapter = workspace_adapter or DevTestWorkspaceAdapter()
        self.use_mock = use_mock
        self.approved_images = set(approved_images or [])
        self._active_services: Dict[str, IDockerService] = {}
        self._global_service: Optional[IDockerService] = None

    def get_docker_service(self, workspace_id: Optional[str] = None) -> Optional[IDockerService]:
        """Get or create an IDockerService for a workspace or global context."""
        if not workspace_id:
            if not self._global_service:
                if self.use_mock:
                    self._global_service = DevTestDockerService(
                        workspace=None, approved_images=self.approved_images
                    )
                else:
                    self._global_service = ControlledDockerService(
                        workspace=None, approved_images=self.approved_images
                    )
            return self._global_service

        if workspace_id in self._active_services:
            return self._active_services[workspace_id]

        workspace = self.workspace_adapter.get_workspace(workspace_id)
        if not workspace or not workspace.workspace_exists():
            return None

        if self.use_mock:
            service: IDockerService = DevTestDockerService(
                workspace=workspace, approved_images=self.approved_images
            )
        else:
            service = ControlledDockerService(
                workspace=workspace, approved_images=self.approved_images
            )

        self._active_services[workspace_id] = service
        return service


# =============================================================================
# Registered Capability Handlers for SpecialistExecutionEngine
# =============================================================================

class BaseDockerCapabilityHandler(BaseCapabilityHandler):
    """Abstract base capability handler for controlled Docker operations."""
    required_tool = "docker"

    def __init__(self, adapter: DevDockerServiceAdapter) -> None:
        self.adapter = adapter

    def _get_service(
        self, workspace_id: Optional[str] = None
    ) -> Tuple[Optional[IDockerService], Optional[CapabilityHandlerOutput]]:
        service = self.adapter.get_docker_service(workspace_id)
        if not service:
            return None, CapabilityHandlerOutput(
                success=False,
                output_text=f"{self.capability_name.upper()}_FAILED: Workspace '{workspace_id}' not found or inactive.",
                errors=[f"Workspace '{workspace_id}' not found or inactive."],
            )
        return service, None


class DockerAvailabilityCapabilityHandler(BaseDockerCapabilityHandler):
    """Approved Capability Execution Handler for Docker availability verification."""
    capability_name = "docker_availability"
    required_params = []
    allowed_params = ["workspace_id"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = request.inputs.get("workspace_id")
        service, err_out = self._get_service(str(ws_id) if ws_id else None)
        if err_out:
            return err_out

        res = service.check_availability()
        if not res.success:
            err_msg = res.error_message or "Docker availability check failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DOCKER_AVAILABILITY_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.message or "Docker is available.",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class DockerBuildCapabilityHandler(BaseDockerCapabilityHandler):
    """Approved Capability Execution Handler for building workspace Docker images."""
    capability_name = "docker_build"
    required_params = ["workspace_id", "image_name"]
    allowed_params = ["workspace_id", "image_name", "dockerfile_path", "build_context", "timeout_seconds"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        image_name = str(request.inputs.get("image_name", ""))
        dockerfile_path = str(request.inputs.get("dockerfile_path", "Dockerfile"))
        build_context = str(request.inputs.get("build_context", "."))
        timeout_seconds = request.inputs.get("timeout_seconds")

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res = service.build_image(
            image_name=image_name,
            dockerfile_path=dockerfile_path,
            build_context=build_context,
            timeout_seconds=float(timeout_seconds) if timeout_seconds is not None else None,
        )

        if not res.success:
            err_msg = res.error_message or f"Docker image build failed for '{image_name}'."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DOCKER_BUILD_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        artifacts = [f"docker://{image_name}"]
        return CapabilityHandlerOutput(
            success=True,
            output_text=res.message or f"Successfully built image '{image_name}'.",
            facts=res.facts,
            artifacts=artifacts,
            errors=[],
            additional_evidence=res.evidence,
        )


class DockerRunCapabilityHandler(BaseDockerCapabilityHandler):
    """Approved Capability Execution Handler for running controlled containers."""
    capability_name = "docker_run"
    required_params = ["workspace_id", "image_name"]
    allowed_params = [
        "workspace_id",
        "image_name",
        "container_name",
        "command",
        "environment",
        "timeout_seconds",
        "memory_limit",
        "cpu_limit",
    ]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        image_name = str(request.inputs.get("image_name", ""))
        container_name = request.inputs.get("container_name")
        command = request.inputs.get("command")
        environment = request.inputs.get("environment")
        timeout_seconds = request.inputs.get("timeout_seconds")
        memory_limit = request.inputs.get("memory_limit")
        cpu_limit = request.inputs.get("cpu_limit")

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res = service.run_container(
            image_name=image_name,
            container_name=str(container_name) if container_name else None,
            command=command if isinstance(command, list) else None,
            environment=environment if isinstance(environment, dict) else None,
            timeout_seconds=float(timeout_seconds) if timeout_seconds is not None else None,
            memory_limit=str(memory_limit) if memory_limit else None,
            cpu_limit=float(cpu_limit) if cpu_limit is not None else None,
        )

        if not res.success:
            err_msg = res.error_message or f"Container execution failed for '{image_name}'."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DOCKER_RUN_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.stdout or res.message or f"Container executed successfully for '{image_name}'.",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class DockerStopCapabilityHandler(BaseDockerCapabilityHandler):
    """Approved Capability Execution Handler for stopping active containers."""
    capability_name = "docker_stop"
    required_params = ["workspace_id", "container_name"]
    allowed_params = ["workspace_id", "container_name", "timeout_seconds"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        container_name = str(request.inputs.get("container_name", ""))
        timeout_seconds = request.inputs.get("timeout_seconds")

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res = service.stop_container(
            container_name=container_name,
            timeout_seconds=float(timeout_seconds) if timeout_seconds is not None else 10.0,
        )

        if not res.success:
            err_msg = res.error_message or f"Failed to stop container '{container_name}'."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DOCKER_STOP_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.message or f"Container '{container_name}' was stopped.",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class DockerRemoveCapabilityHandler(BaseDockerCapabilityHandler):
    """Approved Capability Execution Handler for removing containers."""
    capability_name = "docker_remove"
    required_params = ["workspace_id", "container_name"]
    allowed_params = ["workspace_id", "container_name", "force"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        container_name = str(request.inputs.get("container_name", ""))
        force = bool(request.inputs.get("force", False))

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res = service.remove_container(
            container_name=container_name,
            force=force,
        )

        if not res.success:
            err_msg = res.error_message or f"Failed to remove container '{container_name}'."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DOCKER_REMOVE_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.message or f"Container '{container_name}' was removed.",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class DockerInspectCapabilityHandler(BaseDockerCapabilityHandler):
    """Approved Capability Execution Handler for inspecting containers."""
    capability_name = "docker_inspect"
    required_params = ["workspace_id", "container_name"]
    allowed_params = ["workspace_id", "container_name"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        container_name = str(request.inputs.get("container_name", ""))

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res = service.inspect_container(container_name=container_name)

        if not res.success:
            err_msg = res.error_message or f"Failed to inspect container '{container_name}'."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DOCKER_INSPECT_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        status_text = f"Container '{container_name}' state: status='{res.inspection.status}', running={res.inspection.running}" if res.inspection else "Inspection succeeded."
        return CapabilityHandlerOutput(
            success=True,
            output_text=status_text,
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )
