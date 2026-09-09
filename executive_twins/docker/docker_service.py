"""
Controlled Docker Service Implementation.
Enforces strict workspace isolation, parameter validation, no raw shell execution,
container security restrictions, bounded resources/timeouts/outputs, and empirical evidence generation.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from executive_twins.docker.interfaces import IDockerService
from executive_twins.docker.models import (
    ContainerInspectionResult,
    DockerOperationType,
    DockerResult,
    DockerStatus,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    DataEvidence,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.workspace.interfaces import ISoftwareWorkspace


# Disallowed shell injection and control patterns
FORBIDDEN_SHELL_PATTERNS = [
    "&&",
    "||",
    ";",
    "|",
    ">",
    "<",
    "&",
    "$",
    "`",
    "\n",
    "\r",
    "\0",
    "$(",
    "${",
    "<(",
    ">(",
    "eval ",
    "exec ",
    "system(",
]

# Strict image name / tag validation (local images only, no dangerous characters or option flags).
# The tag part (after ':') must start with an alphanumeric character to prevent option injection like ':--flag'.
IMAGE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*(?::[a-z0-9][a-z0-9_.-]*)?$")

# Strict container name validation
CONTAINER_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")

# Strict environment variable key validation
ENV_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")

# Memory limit pattern: e.g. 128m, 512m, 1g
MEMORY_LIMIT_PATTERN = re.compile(r"^([1-9][0-9]*)([mMgG])$")

# Blocked host sensitive environment variable prefixes & exact names
BLOCKED_ENV_PREFIXES = (
    "AWS_",
    "AZURE_",
    "GITHUB_",
    "OPENAI_",
    "ANTHROPIC_",
    "DOCKER_",
    "SECRET",
    "KEY",
    "TOKEN",
    "PASSWORD",
    "CREDENTIAL",
    "SSH_",
)
BLOCKED_ENV_EXACT = {
    "PATH",
    "HOME",
    "USERPROFILE",
    "WINDIR",
    "SYSTEMROOT",
    "COMSPEC",
    "TEMP",
    "TMP",
}


class ControlledDockerService(IDockerService):
    """
    Controlled Docker Service.
    Enforces that specialist workers CANNOT execute arbitrary Docker CLI commands,
    mount host paths, access the Docker socket, run privileged containers, or bypass resource limits.
    All operations are strictly bounded and executed via subprocess with shell=False.
    """

    DEFAULT_TIMEOUT_SECONDS = 30.0
    MAX_TIMEOUT_SECONDS = 300.0
    MAX_OUTPUT_CHARS = 100_000
    MAX_MEMORY_BYTES = 1024 * 1024 * 1024  # 1GB maximum memory
    MAX_CPUS = 2.0
    MIN_CPUS = 0.1

    def __init__(
        self,
        workspace: Optional[ISoftwareWorkspace] = None,
        docker_executable: Optional[str] = None,
        approved_images: Optional[Set[str]] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_chars: int = MAX_OUTPUT_CHARS,
    ) -> None:
        self._workspace = workspace
        self._docker_executable = docker_executable or self._resolve_docker_binary()
        self._approved_images: Set[str] = set(approved_images or [])
        self._built_images: Set[str] = set()
        self._active_containers: Set[str] = set()
        self._default_timeout = timeout_seconds
        self._max_output_chars = max_output_chars

    @property
    def workspace(self) -> Optional[ISoftwareWorkspace]:
        return self._workspace

    # -------------------------------------------------------------------------
    # Internal Binary and Environment Resolution
    # -------------------------------------------------------------------------

    def _resolve_docker_binary(self) -> str:
        """Resolve docker executable path safely from system PATH."""
        binary = shutil.which("docker")
        return binary if binary else "docker"

    def _get_controlled_env(self) -> Dict[str, str]:
        """
        Construct a minimal, sanitized environment for Docker CLI execution.
        Prevents leaking host secrets, credentials, or API keys.
        """
        controlled_env: Dict[str, str] = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        }
        for var in [
            "PATHEXT",
            "COMSPEC",
            "WINDIR",
            "USERPROFILE",
            "HOME",
            "LANG",
            "LC_ALL",
            "TMP",
            "TEMP",
        ]:
            if var in os.environ:
                controlled_env[var] = os.environ[var]
        return controlled_env

    # -------------------------------------------------------------------------
    # Internal Validation Helpers
    # -------------------------------------------------------------------------

    def _validate_image_name(self, image_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate image name and tag.
        Enforces local image naming, rejects dangerous option flags, remote registry URLs,
        shell syntax, and invalid characters.
        """
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
        """
        Validate container name against strict alphanumeric and safe identifier rules.
        """
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
        """
        Validate specialist-supplied environment variables.
        Rejects host credential leaks, forbidden keys, and control characters.
        """
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

            # Block sensitive host keys and credential prefixes
            key_upper = key_clean.upper()
            if key_upper in BLOCKED_ENV_EXACT or any(key_upper.startswith(prefix) for prefix in BLOCKED_ENV_PREFIXES):
                return False, f"SECURITY_ERROR: Environment variable key '{key_clean}' is blocked to prevent credential/host leaks.", {}

            if len(val_clean) > 1024:
                return False, f"INVALID_INPUT: Environment value for '{key_clean}' exceeds maximum length of 1024 characters.", {}

            # Reject null bytes and non-printable control characters (except standard whitespace)
            for c in val_clean:
                if c == "\0" or (ord(c) < 32 and c not in ("\t", "\n", "\r")):
                    return False, f"INVALID_INPUT: Environment value for '{key_clean}' contains forbidden control characters.", {}

            cleaned[key_clean] = val_clean

        return True, None, cleaned

    def _validate_command(self, command: Optional[List[str]]) -> Tuple[bool, Optional[str]]:
        """
        Validate container execution command tokens.
        Command tokens run INSIDE the container only. Rejects shell injection patterns.
        """
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
        """
        Validate memory limit against maximum allowed bound (1GB).
        """
        if memory_limit is None:
            return True, None, "512m"

        if not isinstance(memory_limit, str):
            return False, "INVALID_INPUT: Memory limit must be a string (e.g. '512m', '1g').", ""

        mem_clean = memory_limit.strip()
        match = MEMORY_LIMIT_PATTERN.match(mem_clean)
        if not match:
            return False, f"INVALID_INPUT: Invalid memory limit format '{mem_clean}'. Must match e.g. '256m' or '1g'.", ""

        num = int(match.group(1))
        unit = match.group(2).lower()
        multiplier = 1024 * 1024 if unit == "m" else 1024 * 1024 * 1024
        total_bytes = num * multiplier

        if total_bytes > self.MAX_MEMORY_BYTES or total_bytes <= 0:
            return False, f"REJECTED: Memory limit '{mem_clean}' exceeds maximum allowed limit of 1g (1024m).", ""

        return True, None, mem_clean.lower()

    def _validate_cpu_limit(self, cpu_limit: Optional[float]) -> Tuple[bool, Optional[str], float]:
        """
        Validate CPU limit against safe bounds (0.1 to 2.0).
        """
        if cpu_limit is None:
            return True, None, 1.0

        if not isinstance(cpu_limit, (int, float)):
            return False, "INVALID_INPUT: CPU limit must be a number.", 0.0

        cpu_val = float(cpu_limit)
        if cpu_val < self.MIN_CPUS or cpu_val > self.MAX_CPUS:
            return False, f"REJECTED: CPU limit {cpu_val} is outside allowed range ({self.MIN_CPUS} to {self.MAX_CPUS}).", 0.0

        return True, None, cpu_val

    def _validate_timeout(self, timeout_seconds: Optional[float]) -> Tuple[bool, Optional[str], float]:
        """
        Validate timeout against maximum allowed duration (300.0 seconds).
        """
        if timeout_seconds is None:
            return True, None, self._default_timeout

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
        """
        Validate that a path resolves strictly inside the workspace root without traversal.
        """
        if not self._workspace or not self._workspace.workspace_exists():
            return False, "WORKSPACE_NOT_FOUND: Workspace is not configured or inactive.", None

        ws_root = Path(self._workspace.root_path).resolve()
        target = path_str.strip() if path_str and isinstance(path_str, str) else default_rel

        # Check for option injection
        if target.startswith("-"):
            return False, f"INVALID_INPUT: Path '{target}' cannot start with '-'.", None

        # Check for forbidden shell characters
        for pat in FORBIDDEN_SHELL_PATTERNS:
            if pat in target:
                return False, f"INVALID_INPUT: Path '{target}' contains forbidden character '{pat}'.", None

        # Check for explicit parent traversal
        p_obj = Path(target)
        for part in p_obj.parts:
            if part == "..":
                return False, f"PATH_TRAVERSAL_REJECTED: Parent traversal '..' rejected in '{target}'.", None

        # Check for absolute / drive-qualified paths
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

        # Strict containment check
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
    # Internal Process Execution
    # -------------------------------------------------------------------------

    def _run_docker(
        self,
        args: List[str],
        timeout_seconds: float,
        cwd: Optional[Path] = None,
    ) -> Tuple[bool, int, str, str, bool]:
        """
        Execute Docker CLI with shell=False, bounded timeout, and captured output.
        Returns: (success, exit_code, stdout, stderr, is_truncated).
        """
        cmd_tokens = [self._docker_executable] + args
        try:
            proc = subprocess.run(
                cmd_tokens,
                cwd=str(cwd) if cwd else None,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=self._get_controlled_env(),
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            exit_code = proc.returncode

        except subprocess.TimeoutExpired as te:
            stdout = te.stdout or "" if isinstance(te.stdout, str) else ""
            stderr = te.stderr or "" if isinstance(te.stderr, str) else ""
            return False, 124, stdout, f"EXECUTION_TIMEOUT: Docker operation timed out after {timeout_seconds}s.", False

        except FileNotFoundError:
            return False, 127, "", "DOCKER_UNAVAILABLE: Docker executable was not found on system PATH.", False

        except Exception as e:
            return False, 1, "", f"DOCKER_EXECUTION_ERROR: Failed to execute Docker CLI: {e}", False

        # Output truncation
        is_truncated = False
        if len(stdout) > self._max_output_chars:
            stdout = stdout[: self._max_output_chars] + "\n... [STDOUT TRUNCATED]"
            is_truncated = True

        if len(stderr) > self._max_output_chars:
            stderr = stderr[: self._max_output_chars] + "\n... [STDERR TRUNCATED]"
            is_truncated = True

        return (exit_code == 0), exit_code, stdout, stderr, is_truncated

    def _build_evidence_and_facts(
        self,
        operation: DockerOperationType,
        cmd_repr: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        is_success: bool,
        duration_seconds: float,
        timed_out: bool = False,
        extra_evidence: Optional[List[Any]] = None,
        fact_statement: Optional[str] = None,
        is_test_op: bool = False,
    ) -> Tuple[List[FactItem], List[Union[ExecutionLogEvidence, ArtifactEvidence, DataEvidence, TestEvidence, VerificationEvidence]]]:
        """Construct empirical execution log, test, and verification evidence."""
        facts: List[FactItem] = []
        if fact_statement:
            facts.append(
                FactItem(
                    statement=fact_statement,
                    state=FactState.FACT if is_success else FactState.UNVERIFIED,
                    source="docker_service",
                )
            )

        evidence_list: List[Union[ExecutionLogEvidence, ArtifactEvidence, DataEvidence, TestEvidence, VerificationEvidence]] = []

        # 1. Execution Log Evidence
        log_snip = f"DOCKER_OP: {operation.value}\nCMD: {cmd_repr}\nEXIT: {exit_code}\nTIMED_OUT: {timed_out}\nDURATION: {duration_seconds:.2f}s\nSTDOUT:\n{stdout[:500]}\nSTDERR:\n{stderr[:500]}"
        evidence_list.append(
            ExecutionLogEvidence(
                evidence_id=f"ev-docker-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-docker-{uuid.uuid4().hex[:8]}",
                log_snippet=log_snip,
                exit_code=exit_code,
                description=f"Controlled Docker {operation.value} execution log for '{cmd_repr}'",
            )
        )

        # 2. Test Evidence (when container is used for testing / verification)
        if is_test_op:
            evidence_list.append(
                TestEvidence(
                    evidence_id=f"ev-docker-test-{uuid.uuid4().hex[:8]}",
                    suite_name=f"container_exec:{cmd_repr}",
                    tests_passed=1 if is_success else 0,
                    tests_failed=0 if is_success else 1,
                    description=f"Container execution test result for '{cmd_repr}'",
                )
            )

        # 3. Extra evidence (e.g. ArtifactEvidence for built image)
        if extra_evidence:
            evidence_list.extend(extra_evidence)

        # 4. Verification Evidence
        evidence_list.append(
            VerificationEvidence(
                evidence_id=f"ev-docker-verif-{uuid.uuid4().hex[:8]}",
                verifier_id="ControlledDockerService",
                verified_status="VERIFIED" if is_success else "FAILED",
                description=f"Docker operation verification for '{operation.value}' (exit code: {exit_code})",
            )
        )

        return facts, evidence_list

    # -------------------------------------------------------------------------
    # Public IDockerService Operations
    # -------------------------------------------------------------------------

    def check_availability(self) -> DockerResult:
        """
        Verify whether the Docker CLI and Docker daemon are available and operational.
        """
        start_time = datetime.now(timezone.utc)
        t0 = time.perf_counter()

        success, exit_code, stdout, stderr, is_trunc = self._run_docker(
            ["version", "--format={{.Server.Version}}"],
            timeout_seconds=10.0,
        )
        duration = time.perf_counter() - t0
        end_time = datetime.now(timezone.utc)

        if not success or not stdout.strip():
            # Also check info to detect daemon not running
            msg = stderr.strip() or "Docker daemon is not running or unreachable."
            facts, ev = self._build_evidence_and_facts(
                DockerOperationType.CHECK_AVAILABILITY,
                "docker version",
                exit_code,
                stdout,
                stderr,
                False,
                duration,
                fact_statement="Docker daemon availability check: UNAVAILABLE.",
            )
            return DockerResult(
                success=False,
                operation=DockerOperationType.CHECK_AVAILABILITY,
                status=DockerStatus.DOCKER_UNAVAILABLE,
                message=f"DOCKER_UNAVAILABLE: {msg}",
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                started_at=start_time,
                finished_at=end_time,
                duration_seconds=duration,
                error_type="DOCKER_UNAVAILABLE",
                error_message=msg,
                facts=facts,
                evidence=ev,
            )

        server_version = stdout.strip()
        fact_stmt = f"Docker daemon is active and operational (version: {server_version})."
        facts, ev = self._build_evidence_and_facts(
            DockerOperationType.CHECK_AVAILABILITY,
            "docker version",
            0,
            stdout,
            stderr,
            True,
            duration,
            fact_statement=fact_stmt,
        )
        return DockerResult(
            success=True,
            operation=DockerOperationType.CHECK_AVAILABILITY,
            status=DockerStatus.SUCCESS,
            message=f"Docker is available (version: {server_version}).",
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            started_at=start_time,
            finished_at=end_time,
            duration_seconds=duration,
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
        """
        Build a Docker image from a workspace-contained Dockerfile and build context.
        """
        start_time = datetime.now(timezone.utc)
        t0 = time.perf_counter()

        # 1. Validate Image Name
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

        # 2. Validate Timeout
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

        # 3. Validate Workspace & Paths
        if not self._workspace or not self._workspace.workspace_exists():
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=DockerStatus.FAILED,
                error_type="WORKSPACE_NOT_FOUND",
                error_message=f"Workspace '{getattr(self._workspace, 'workspace_id', 'None')}' is not found or inactive.",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        ws_root = Path(self._workspace.root_path).resolve()

        # Validate Dockerfile path
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

        # Validate Build Context path
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

        # 4. Construct Controlled Docker Build Arguments
        # Relative paths from workspace root
        df_rel = str(resolved_df.relative_to(ws_root)).replace("\\", "/")
        bc_rel = str(resolved_bc.relative_to(ws_root)).replace("\\", "/")
        if bc_rel == "":
            bc_rel = "."

        args = [
            "build",
            "-f",
            df_rel,
            "-t",
            image_name,
            bc_rel,
        ]
        cmd_repr = f"docker build -f {df_rel} -t {image_name} {bc_rel}"

        # 5. Execute Build Subprocess
        success, exit_code, stdout, stderr, is_trunc = self._run_docker(
            args,
            timeout_seconds=timeout_val,
            cwd=ws_root,
        )
        duration = time.perf_counter() - t0
        end_time = datetime.now(timezone.utc)
        timed_out = (exit_code == 124)

        if not success:
            status = DockerStatus.TIMEOUT if timed_out else DockerStatus.IMAGE_BUILD_FAILED
            facts, ev = self._build_evidence_and_facts(
                DockerOperationType.BUILD_IMAGE,
                cmd_repr,
                exit_code,
                stdout,
                stderr,
                False,
                duration,
                timed_out=timed_out,
                fact_statement=f"Failed to build Docker image '{image_name}' (exit code: {exit_code}).",
            )
            return DockerResult(
                success=False,
                operation=DockerOperationType.BUILD_IMAGE,
                status=status,
                image_name=image_name,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                started_at=start_time,
                finished_at=end_time,
                duration_seconds=duration,
                timed_out=timed_out,
                output_truncated=is_trunc,
                error_type="IMAGE_BUILD_TIMEOUT" if timed_out else "IMAGE_BUILD_FAILED",
                error_message=stderr or f"Failed to build image '{image_name}'.",
                facts=facts,
                evidence=ev,
            )

        # Record built image in internal authorized set
        self._built_images.add(image_name)

        # Build Artifact Evidence
        art_evidence = [
            ArtifactEvidence(
                evidence_id=f"ev-art-img-{uuid.uuid4().hex[:8]}",
                artifact_uri=f"docker://{image_name}",
                mime_type="application/vnd.docker.container.image.v1+json",
                description=f"Built Docker image '{image_name}' in workspace '{getattr(self._workspace, 'workspace_id', '')}'",
            )
        ]

        fact_stmt = f"Successfully built Docker image '{image_name}' from '{df_rel}' in workspace '{getattr(self._workspace, 'workspace_id', '')}'."
        facts, ev = self._build_evidence_and_facts(
            DockerOperationType.BUILD_IMAGE,
            cmd_repr,
            0,
            stdout,
            stderr,
            True,
            duration,
            extra_evidence=art_evidence,
            fact_statement=fact_stmt,
        )

        return DockerResult(
            success=True,
            operation=DockerOperationType.BUILD_IMAGE,
            status=DockerStatus.SUCCESS,
            message=f"Successfully built image '{image_name}'.",
            image_name=image_name,
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            started_at=start_time,
            finished_at=end_time,
            duration_seconds=duration,
            output_truncated=is_trunc,
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
        """
        Run a bounded, isolated container from an authorized image.
        """
        start_time = datetime.now(timezone.utc)
        t0 = time.perf_counter()

        # 1. Validate Image Name
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

        # 2. Verify Image Authorization (must be built by service or explicitly approved)
        if image_name not in self._built_images and image_name not in self._approved_images:
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=DockerStatus.NOT_AUTHORIZED,
                image_name=image_name,
                error_type="UNAUTHORIZED_IMAGE",
                error_message=f"NOT_AUTHORIZED: Image '{image_name}' was not built by this controlled service and is not in the approved image allowlist.",
                started_at=start_time,
                finished_at=datetime.now(timezone.utc),
            )

        # 3. Validate / Generate Container Name
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

        # 4. Validate Command Tokens
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

        # 5. Validate Environment Variables
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

        # 6. Validate Resource Limits & Timeout
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

        # 7. Construct Hardened Docker Run Arguments
        # Strict isolation: no-new-privileges, network=none, pids limit, memory, cpu, NO privileged, NO volume mounts
        run_args = [
            "run",
            "--name",
            c_name,
            "--security-opt=no-new-privileges",
            "--network=none",
            "--pids-limit=100",
            f"--memory={mem_val}",
            f"--cpus={cpu_val}",
        ]
        # Environment variables
        for env_k, env_v in cleaned_env.items():
            run_args.extend(["-e", f"{env_k}={env_v}"])

        run_args.append(image_name)
        if command:
            run_args.extend(command)

        cmd_repr = f"docker {' '.join(run_args)}"
        self._active_containers.add(c_name)

        # 8. Execute Container Run
        success, exit_code, stdout, stderr, is_trunc = self._run_docker(
            run_args,
            timeout_seconds=timeout_val,
        )
        duration = time.perf_counter() - t0
        end_time = datetime.now(timezone.utc)
        timed_out = (exit_code == 124)

        # 9. Clean up container safely
        cleanup_err = None
        try:
            # Stop if still running, then remove
            if timed_out:
                self._run_docker(["stop", "-t", "2", c_name], timeout_seconds=5.0)
            self._run_docker(["rm", "-f", c_name], timeout_seconds=5.0)
            self._active_containers.discard(c_name)
        except Exception as ce:
            cleanup_err = str(ce)

        if not success:
            status = DockerStatus.TIMEOUT if timed_out else DockerStatus.CONTAINER_FAILED
            fact_stmt = f"Container '{c_name}' execution failed (image: '{image_name}', exit code: {exit_code}, timed_out: {timed_out})."
            facts, ev = self._build_evidence_and_facts(
                DockerOperationType.RUN_CONTAINER,
                cmd_repr,
                exit_code,
                stdout,
                stderr,
                False,
                duration,
                timed_out=timed_out,
                fact_statement=fact_stmt,
                is_test_op=True,
            )
            return DockerResult(
                success=False,
                operation=DockerOperationType.RUN_CONTAINER,
                status=status,
                image_name=image_name,
                container_name=c_name,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                started_at=start_time,
                finished_at=end_time,
                duration_seconds=duration,
                timed_out=timed_out,
                output_truncated=is_trunc,
                error_type="CONTAINER_TIMEOUT" if timed_out else "CONTAINER_FAILED",
                error_message=stderr or f"Container '{c_name}' execution failed.",
                facts=facts,
                evidence=ev,
            )

        fact_stmt = f"Container '{c_name}' executed successfully from image '{image_name}' (exit code: 0, duration: {duration:.2f}s)."
        facts, ev = self._build_evidence_and_facts(
            DockerOperationType.RUN_CONTAINER,
            cmd_repr,
            0,
            stdout,
            stderr,
            True,
            duration,
            fact_statement=fact_stmt,
            is_test_op=True,
        )

        return DockerResult(
            success=True,
            operation=DockerOperationType.RUN_CONTAINER,
            status=DockerStatus.SUCCESS,
            message=f"Container '{c_name}' completed execution successfully.",
            image_name=image_name,
            container_name=c_name,
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            started_at=start_time,
            finished_at=end_time,
            duration_seconds=duration,
            output_truncated=is_trunc,
            facts=facts,
            evidence=ev,
        )

    def stop_container(
        self,
        container_name: str,
        timeout_seconds: Optional[float] = 10.0,
    ) -> DockerResult:
        """
        Stop an active container created by the controlled service.
        """
        start_time = datetime.now(timezone.utc)
        t0 = time.perf_counter()

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

        to_val = int(timeout_seconds) if timeout_seconds and timeout_seconds > 0 else 10
        args = ["stop", "-t", str(to_val), container_name]
        cmd_repr = f"docker stop -t {to_val} {container_name}"

        success, exit_code, stdout, stderr, is_trunc = self._run_docker(
            args,
            timeout_seconds=float(to_val + 10),
        )
        duration = time.perf_counter() - t0
        end_time = datetime.now(timezone.utc)

        if not success:
            status = DockerStatus.CONTAINER_NOT_FOUND if "No such container" in stderr else DockerStatus.FAILED
            facts, ev = self._build_evidence_and_facts(
                DockerOperationType.STOP_CONTAINER,
                cmd_repr,
                exit_code,
                stdout,
                stderr,
                False,
                duration,
                fact_statement=f"Failed to stop container '{container_name}'.",
            )
            return DockerResult(
                success=False,
                operation=DockerOperationType.STOP_CONTAINER,
                status=status,
                container_name=container_name,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                started_at=start_time,
                finished_at=end_time,
                duration_seconds=duration,
                error_type="CONTAINER_STOP_FAILED",
                error_message=stderr or f"Failed to stop container '{container_name}'.",
                facts=facts,
                evidence=ev,
            )

        facts, ev = self._build_evidence_and_facts(
            DockerOperationType.STOP_CONTAINER,
            cmd_repr,
            0,
            stdout,
            stderr,
            True,
            duration,
            fact_statement=f"Stopped container '{container_name}'.",
        )
        return DockerResult(
            success=True,
            operation=DockerOperationType.STOP_CONTAINER,
            status=DockerStatus.CONTAINER_STOPPED,
            message=f"Container '{container_name}' was stopped.",
            container_name=container_name,
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            started_at=start_time,
            finished_at=end_time,
            duration_seconds=duration,
            facts=facts,
            evidence=ev,
        )

    def remove_container(
        self,
        container_name: str,
        force: bool = False,
    ) -> DockerResult:
        """
        Remove a container created by the controlled service.
        """
        start_time = datetime.now(timezone.utc)
        t0 = time.perf_counter()

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

        args = ["rm", "-f", container_name] if force else ["rm", container_name]
        cmd_repr = f"docker {' '.join(args)}"

        success, exit_code, stdout, stderr, is_trunc = self._run_docker(
            args,
            timeout_seconds=15.0,
        )
        duration = time.perf_counter() - t0
        end_time = datetime.now(timezone.utc)

        self._active_containers.discard(container_name)

        if not success:
            status = DockerStatus.CONTAINER_NOT_FOUND if "No such container" in stderr else DockerStatus.FAILED
            facts, ev = self._build_evidence_and_facts(
                DockerOperationType.REMOVE_CONTAINER,
                cmd_repr,
                exit_code,
                stdout,
                stderr,
                False,
                duration,
                fact_statement=f"Failed to remove container '{container_name}'.",
            )
            return DockerResult(
                success=False,
                operation=DockerOperationType.REMOVE_CONTAINER,
                status=status,
                container_name=container_name,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                started_at=start_time,
                finished_at=end_time,
                duration_seconds=duration,
                error_type="CONTAINER_REMOVE_FAILED",
                error_message=stderr or f"Failed to remove container '{container_name}'.",
                facts=facts,
                evidence=ev,
            )

        facts, ev = self._build_evidence_and_facts(
            DockerOperationType.REMOVE_CONTAINER,
            cmd_repr,
            0,
            stdout,
            stderr,
            True,
            duration,
            fact_statement=f"Removed container '{container_name}'.",
        )
        return DockerResult(
            success=True,
            operation=DockerOperationType.REMOVE_CONTAINER,
            status=DockerStatus.CONTAINER_REMOVED,
            message=f"Container '{container_name}' was removed.",
            container_name=container_name,
            exit_code=0,
            stdout=stdout,
            stderr=stderr,
            started_at=start_time,
            finished_at=end_time,
            duration_seconds=duration,
            facts=facts,
            evidence=ev,
        )

    def inspect_container(
        self,
        container_name: str,
    ) -> DockerResult:
        """
        Retrieve structured status and state inspection for a container.
        """
        start_time = datetime.now(timezone.utc)
        t0 = time.perf_counter()

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

        args = ["inspect", "--format={{json .}}", container_name]
        cmd_repr = f"docker inspect {container_name}"

        success, exit_code, stdout, stderr, is_trunc = self._run_docker(
            args,
            timeout_seconds=10.0,
        )
        duration = time.perf_counter() - t0
        end_time = datetime.now(timezone.utc)

        if not success:
            status = DockerStatus.CONTAINER_NOT_FOUND if "No such container" in stderr or "No such object" in stderr else DockerStatus.FAILED
            facts, ev = self._build_evidence_and_facts(
                DockerOperationType.INSPECT_CONTAINER,
                cmd_repr,
                exit_code,
                stdout,
                stderr,
                False,
                duration,
                fact_statement=f"Failed to inspect container '{container_name}'.",
            )
            return DockerResult(
                success=False,
                operation=DockerOperationType.INSPECT_CONTAINER,
                status=status,
                container_name=container_name,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                started_at=start_time,
                finished_at=end_time,
                duration_seconds=duration,
                error_type="CONTAINER_INSPECT_FAILED",
                error_message=stderr or f"Failed to inspect container '{container_name}'.",
                facts=facts,
                evidence=ev,
            )

        # Parse JSON inspection data
        try:
            data = json.loads(stdout.strip())
            c_id = data.get("Id", "")[:12]
            c_state = data.get("State", {})
            c_status = c_state.get("Status", "unknown")
            c_running = c_state.get("Running", False)
            c_exit = c_state.get("ExitCode")
            c_started = c_state.get("StartedAt")
            c_finished = c_state.get("FinishedAt")
            c_image = data.get("Config", {}).get("Image", "")

            inspection_obj = ContainerInspectionResult(
                container_id=c_id,
                container_name=container_name,
                image=c_image,
                status=c_status,
                running=c_running,
                exit_code=c_exit,
                started_at=c_started,
                finished_at=c_finished,
            )
        except Exception:
            inspection_obj = ContainerInspectionResult(
                container_id="",
                container_name=container_name,
                image="",
                status="unknown",
                running=False,
            )

        fact_stmt = f"Container '{container_name}' state: status='{inspection_obj.status}', running={inspection_obj.running}."
        facts, ev = self._build_evidence_and_facts(
            DockerOperationType.INSPECT_CONTAINER,
            cmd_repr,
            0,
            stdout,
            stderr,
            True,
            duration,
            fact_statement=fact_stmt,
        )

        return DockerResult(
            success=True,
            operation=DockerOperationType.INSPECT_CONTAINER,
            status=DockerStatus.SUCCESS,
            container_id=inspection_obj.container_id,
            container_name=container_name,
            image_name=inspection_obj.image,
            exit_code=0,
            inspection=inspection_obj,
            stdout=stdout,
            started_at=start_time,
            finished_at=end_time,
            duration_seconds=duration,
            facts=facts,
            evidence=ev,
        )
