"""
Controlled Build & Test Command Executor.
Enforces strict command allowlists, shell syntax rejection, bounded timeouts,
output limits, and workspace boundary security.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Dict, List, Optional, Set, Tuple
import uuid

from executive_twins.command_execution.interfaces import ICommandExecutor
from executive_twins.command_execution.models import (
    CommandRequest,
    CommandResult,
    CommandStatus,
    CommandType,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.evidence import (
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)
from executive_twins.workspace.interfaces import ISoftwareWorkspace


# Shell injection and control characters strictly forbidden in executables and arguments
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
    "$(",
    "${",
    "<(",
    ">(",
    "eval ",
    "exec ",
    "system(",
]


class CommandSpecification:
    """
    Specification defining an approved combination of command type, executable,
    and argument structure.
    """

    def __init__(
        self,
        command_type: CommandType,
        executable: str,
        allowed_argument_prefixes: Optional[List[List[str]]] = None,
        allow_additional_args: bool = True,
        allowed_flags: Optional[Set[str]] = None,
    ) -> None:
        self.command_type = command_type
        self.executable = executable.lower()
        self.allowed_argument_prefixes = allowed_argument_prefixes or []
        self.allow_additional_args = allow_additional_args
        self.allowed_flags = allowed_flags or set()

    def matches(self, command_type: CommandType, executable: str, arguments: List[str]) -> bool:
        if self.command_type != command_type:
            return False
        if self.executable != executable.lower():
            return False

        if not self.allowed_argument_prefixes:
            return True

        for prefix in self.allowed_argument_prefixes:
            if len(arguments) >= len(prefix):
                if arguments[: len(prefix)] == prefix:
                    if not self.allow_additional_args and len(arguments) > len(prefix):
                        continue
                    return True
        return False


class CommandRegistry:
    """
    Centralized allowlist registry defining approved executables and argument patterns.
    """

    def __init__(self) -> None:
        self._specs: List[CommandSpecification] = []
        self._init_default_allowlist()

    def _init_default_allowlist(self) -> None:
        # 1. TEST commands
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.TEST,
                executable="python",
                allowed_argument_prefixes=[
                    ["-m", "pytest"],
                    ["-m", "unittest"],
                ],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.TEST,
                executable="pytest",
                allowed_argument_prefixes=[[]],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.TEST,
                executable="npm",
                allowed_argument_prefixes=[
                    ["test"],
                    ["run", "test"],
                ],
                allow_additional_args=True,
            )
        )

        # 2. BUILD commands
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.BUILD,
                executable="npm",
                allowed_argument_prefixes=[
                    ["run", "build"],
                    ["run", "compile"],
                ],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.BUILD,
                executable="python",
                allowed_argument_prefixes=[
                    ["-m", "build"],
                ],
                allow_additional_args=True,
            )
        )

        # 3. LINT commands
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.LINT,
                executable="npm",
                allowed_argument_prefixes=[
                    ["run", "lint"],
                ],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.LINT,
                executable="flake8",
                allowed_argument_prefixes=[[]],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.LINT,
                executable="ruff",
                allowed_argument_prefixes=[
                    ["check"],
                ],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.LINT,
                executable="python",
                allowed_argument_prefixes=[
                    ["-m", "flake8"],
                    ["-m", "ruff", "check"],
                ],
                allow_additional_args=True,
            )
        )

        # 4. TYPECHECK commands
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.TYPECHECK,
                executable="npm",
                allowed_argument_prefixes=[
                    ["run", "typecheck"],
                ],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.TYPECHECK,
                executable="mypy",
                allowed_argument_prefixes=[[]],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.TYPECHECK,
                executable="python",
                allowed_argument_prefixes=[
                    ["-m", "mypy"],
                ],
                allow_additional_args=True,
            )
        )

        # 5. PACKAGE commands
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.PACKAGE,
                executable="npm",
                allowed_argument_prefixes=[
                    ["pack"],
                ],
                allow_additional_args=True,
            )
        )
        self._specs.append(
            CommandSpecification(
                command_type=CommandType.PACKAGE,
                executable="python",
                allowed_argument_prefixes=[
                    ["-m", "build", "--wheel"],
                ],
                allow_additional_args=True,
            )
        )

    def register_specification(self, spec: CommandSpecification) -> None:
        """Register a new approved command specification."""
        self._specs.append(spec)

    def is_allowed(
        self, command_type: CommandType, executable: str, arguments: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """Validate whether the command matches an approved specification."""
        for spec in self._specs:
            if spec.matches(command_type, executable, arguments):
                return True, None

        return (
            False,
            f"INVALID_COMMAND: Combination of command_type='{command_type.value}', executable='{executable}', arguments={arguments} is not in the approved allowlist.",
        )


class ControlledCommandExecutor(ICommandExecutor):
    """
    Controlled Build & Test Command Executor.
    Runs approved commands inside a controlled ISoftwareWorkspace.
    Enforces security boundary, allowlist validation, shell operator rejection,
    path security, bounded timeouts, and output limits.
    """

    DEFAULT_TIMEOUT_SECONDS = 30.0
    MAX_TIMEOUT_SECONDS = 300.0
    MAX_OUTPUT_CHARS = 100_000

    def __init__(
        self,
        workspace: ISoftwareWorkspace,
        registry: Optional[CommandRegistry] = None,
    ) -> None:
        self._workspace = workspace
        self._registry = registry or CommandRegistry()

    @property
    def workspace(self) -> ISoftwareWorkspace:
        return self._workspace

    @property
    def registry(self) -> CommandRegistry:
        return self._registry

    def _validate_no_shell_operators(
        self, executable: str, arguments: List[str]
    ) -> Optional[str]:
        """Verify that no shell syntax or control characters exist in executable or arguments."""
        all_tokens = [executable] + list(arguments)
        for token in all_tokens:
            token_str = str(token)
            for pattern in FORBIDDEN_SHELL_PATTERNS:
                if pattern in token_str:
                    return (
                        f"SECURITY_SHELL_OPERATOR_REJECTED: Forbidden shell syntax or operator '{pattern}' "
                        f"detected in token '{token_str}'."
                    )
        return None

    def _validate_path_argument(self, path_arg: str, workspace_root: Path) -> Optional[str]:
        """Ensure path arguments stay within the workspace boundary."""
        if not path_arg or not path_arg.strip():
            return None

        # Check for explicit parent traversal
        path_obj = Path(path_arg)
        for part in path_obj.parts:
            if part == "..":
                return f"SECURITY_PATH_TRAVERSAL: Explicit parent traversal '..' rejected in argument '{path_arg}'."

        if path_obj.is_absolute():
            try:
                resolved = path_obj.resolve()
            except Exception as e:
                return f"SECURITY_PATH_TRAVERSAL: Invalid path '{path_arg}': {e}"

            try:
                resolved.relative_to(workspace_root)
            except ValueError:
                return (
                    f"SECURITY_PATH_TRAVERSAL: Absolute path '{path_arg}' resolves outside workspace root '{workspace_root}'."
                )
        else:
            full_path = workspace_root / path_obj
            try:
                resolved = full_path.resolve()
            except Exception as e:
                return f"SECURITY_PATH_TRAVERSAL: Invalid path '{path_arg}': {e}"

            try:
                resolved.relative_to(workspace_root)
            except ValueError:
                return (
                    f"SECURITY_PATH_TRAVERSAL: Path '{path_arg}' resolves outside workspace root '{workspace_root}'."
                )

        return None

    def _validate_all_path_arguments(
        self, request: CommandRequest, workspace_root: Path
    ) -> Optional[str]:
        """Validate explicit path arguments and any positional path-like arguments."""
        # 1. Explicit path arguments
        for path_arg in request.path_arguments:
            err = self._validate_path_argument(path_arg, workspace_root)
            if err:
                return err

        # 2. Inspect argument tokens that look like paths or files
        for arg in request.arguments:
            if arg.startswith("-"):
                continue
            if "/" in arg or "\\" in arg or arg.startswith(".") or arg.endswith((".py", ".js", ".ts", ".json", ".html", ".css", ".md", ".txt")):
                err = self._validate_path_argument(arg, workspace_root)
                if err:
                    return err

        return None

    def execute(self, request: CommandRequest) -> CommandResult:
        """
        Execute a controlled command within the workspace boundary.
        """
        start_time = time.perf_counter()

        # 1. Workspace existence check
        if not self._workspace.workspace_exists():
            return CommandResult(
                success=False,
                status=CommandStatus.FAILED,
                command_type=request.command_type,
                executable=request.executable,
                arguments=request.arguments,
                workspace_id=request.workspace_id,
                error_type="WORKSPACE_NOT_FOUND",
                error_message=f"WORKSPACE_NOT_FOUND: Workspace '{request.workspace_id}' does not exist or is inactive.",
            )

        workspace_root = Path(self._workspace.root_path).resolve()

        # 2. Reject shell operators and control syntax
        shell_err = self._validate_no_shell_operators(request.executable, request.arguments)
        if shell_err:
            return CommandResult(
                success=False,
                status=CommandStatus.REJECTED,
                command_type=request.command_type,
                executable=request.executable,
                arguments=request.arguments,
                workspace_id=request.workspace_id,
                error_type="SECURITY_SHELL_OPERATOR_REJECTED",
                error_message=shell_err,
            )

        # 3. Validate command against allowlist registry
        allowed, allow_err = self._registry.is_allowed(
            request.command_type, request.executable, request.arguments
        )
        if not allowed:
            return CommandResult(
                success=False,
                status=CommandStatus.INVALID_COMMAND,
                command_type=request.command_type,
                executable=request.executable,
                arguments=request.arguments,
                workspace_id=request.workspace_id,
                error_type="INVALID_COMMAND",
                error_message=allow_err or "Command not in approved allowlist.",
            )

        # 4. Validate path arguments against workspace boundary
        path_err = self._validate_all_path_arguments(request, workspace_root)
        if path_err:
            return CommandResult(
                success=False,
                status=CommandStatus.REJECTED,
                command_type=request.command_type,
                executable=request.executable,
                arguments=request.arguments,
                workspace_id=request.workspace_id,
                error_type="SECURITY_PATH_TRAVERSAL",
                error_message=path_err,
            )

        # 5. Enforce bounded timeout
        timeout_seconds = max(0.1, min(request.timeout_seconds, self.MAX_TIMEOUT_SECONDS))

        # 6. Controlled environment construction
        runtime_bin_dir = str(Path(sys.executable).parent)
        system_path = os.environ.get("PATH", "")
        effective_path = f"{runtime_bin_dir}{os.pathsep}{system_path}" if runtime_bin_dir else system_path

        controlled_env = {
            "PATH": effective_path,
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": os.environ.get("TEMP", ""),
            "TMP": os.environ.get("TMP", ""),
            "PYTHONPATH": str(workspace_root),
            "CI": "true",
        }
        # Retain necessary platform runtime variables on Windows/POSIX
        for var in ["PATHEXT", "COMSPEC", "WINDIR", "USERPROFILE", "HOME", "LANG", "LC_ALL"]:
            if var in os.environ:
                controlled_env[var] = os.environ[var]

        # 7. Execute process inside workspace root
        resolved_executable = request.executable
        if request.executable.lower() in ("python", "python3") and sys.executable:
            resolved_executable = sys.executable

        cmd_tokens = [resolved_executable] + list(request.arguments)
        try:
            proc = subprocess.run(
                cmd_tokens,
                cwd=str(workspace_root),
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=controlled_env,
            )
            duration = time.perf_counter() - start_time
            exit_code = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""

        except subprocess.TimeoutExpired as te:
            duration = time.perf_counter() - start_time
            stdout = te.stdout or "" if isinstance(te.stdout, str) else ""
            stderr = te.stderr or "" if isinstance(te.stderr, str) else ""
            return CommandResult(
                success=False,
                status=CommandStatus.TIMEOUT,
                command_type=request.command_type,
                executable=request.executable,
                arguments=request.arguments,
                workspace_id=request.workspace_id,
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                error_type="EXECUTION_TIMEOUT",
                error_message=f"EXECUTION_TIMEOUT: Command timed out after {timeout_seconds} seconds.",
            )

        except FileNotFoundError:
            duration = time.perf_counter() - start_time
            return CommandResult(
                success=False,
                status=CommandStatus.FAILED,
                command_type=request.command_type,
                executable=request.executable,
                arguments=request.arguments,
                workspace_id=request.workspace_id,
                exit_code=127,
                stdout="",
                stderr=f"Executable '{request.executable}' not found on system path.",
                duration_seconds=duration,
                error_type="EXECUTABLE_NOT_FOUND",
                error_message=f"EXECUTABLE_NOT_FOUND: Executable '{request.executable}' was not found.",
            )

        except Exception as e:
            duration = time.perf_counter() - start_time
            return CommandResult(
                success=False,
                status=CommandStatus.FAILED,
                command_type=request.command_type,
                executable=request.executable,
                arguments=request.arguments,
                workspace_id=request.workspace_id,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration_seconds=duration,
                error_type="PROCESS_ERROR",
                error_message=f"PROCESS_ERROR: Failed to execute process: {e}",
            )

        # 8. Output bounding
        is_truncated = False
        if len(stdout) > self.MAX_OUTPUT_CHARS:
            stdout = stdout[: self.MAX_OUTPUT_CHARS] + "\n... [STDOUT TRUNCATED]"
            is_truncated = True

        if len(stderr) > self.MAX_OUTPUT_CHARS:
            stderr = stderr[: self.MAX_OUTPUT_CHARS] + "\n... [STDERR TRUNCATED]"
            is_truncated = True

        # 9. Structure Result, Facts, and Evidence
        is_success = exit_code == 0
        status = CommandStatus.SUCCESS if is_success else CommandStatus.FAILED

        cmd_repr = f"{request.executable} {' '.join(request.arguments)}".strip()
        facts = [
            FactItem(
                statement=f"Executed command '{cmd_repr}' in workspace '{request.workspace_id}' (exit code: {exit_code}, duration: {duration:.2f}s).",
                state=FactState.FACT,
                source="command_executor",
            )
        ]

        evidence_list = []
        # Execution log evidence
        evidence_id = f"ev-log-{uuid.uuid4().hex[:8]}"
        log_snip = f"CMD: {cmd_repr}\nEXIT: {exit_code}\nSTDOUT:\n{stdout[:500]}\nSTDERR:\n{stderr[:500]}"
        evidence_list.append(
            ExecutionLogEvidence(
                evidence_id=evidence_id,
                execution_id=f"exec-{uuid.uuid4().hex[:8]}",
                log_snippet=log_snip,
                exit_code=exit_code,
                description=f"Controlled {request.command_type.value} execution log for '{cmd_repr}'",
            )
        )

        # Test evidence for TEST commands
        if request.command_type == CommandType.TEST and is_success:
            test_ev_id = f"ev-test-{uuid.uuid4().hex[:8]}"
            evidence_list.append(
                TestEvidence(
                    evidence_id=test_ev_id,
                    suite_name=cmd_repr,
                    tests_passed=1,
                    tests_failed=0,
                    description=f"Successful test execution for suite '{cmd_repr}'",
                )
            )

        # Verification evidence
        verif_ev_id = f"ev-verif-{uuid.uuid4().hex[:8]}"
        evidence_list.append(
            VerificationEvidence(
                evidence_id=verif_ev_id,
                verifier_id="ControlledCommandExecutor",
                verified_status="VERIFIED" if is_success else "FAILED",
                description=f"Execution verification for command '{cmd_repr}' (status: {status.value})",
            )
        )

        return CommandResult(
            success=is_success,
            status=status,
            command_type=request.command_type,
            executable=request.executable,
            arguments=request.arguments,
            workspace_id=request.workspace_id,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            is_truncated=is_truncated,
            error_type=None if is_success else "COMMAND_EXECUTION_FAILED",
            error_message=None if is_success else f"Command failed with exit code {exit_code}.",
            facts=facts,
            evidence=evidence_list,
        )
