"""
Controlled Git Service Implementation.
Enforces workspace security boundaries, strict argument validation, no raw shell execution,
bounded timeouts, bounded diff/log output, and empirical evidence generation.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from executive_twins.git.interfaces import IGitService
from executive_twins.git.models import (
    GitLogEntry,
    GitOperationType,
    GitResult,
    GitStatus,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    DataEvidence,
    ExecutionLogEvidence,
    VerificationEvidence,
)
from executive_twins.workspace.interfaces import ISoftwareWorkspace


# Disallowed shell injection characters in arguments
FORBIDDEN_SHELL_CHARS = {"&", "|", ";", "$", "`", ">", "<", "\n", "\r", "\0"}

# Branch name regex: alphanumeric, dash, underscore, dot, slash
BRANCH_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.\/]+$")


class ControlledGitService(IGitService):
    """
    Controlled Git / Version Control Service.
    Operates strictly within an ISoftwareWorkspace boundary.
    Executes Git subcommands via safe subprocess argument vectors with shell=False.
    Raw shell commands, destructive operations, force-push, and credential mutations are forbidden.
    """

    MAX_OUTPUT_CHARS = 50000
    MAX_LOG_LIMIT = 50
    DEFAULT_TIMEOUT_SECONDS = 30.0
    MAX_COMMIT_MESSAGE_LENGTH = 4096

    def __init__(
        self,
        workspace: ISoftwareWorkspace,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_chars: int = MAX_OUTPUT_CHARS,
        max_log_limit: int = MAX_LOG_LIMIT,
    ) -> None:
        self._workspace = workspace
        self._repo_path = Path(workspace.root_path).resolve()
        self._timeout_seconds = timeout_seconds
        self._max_output_chars = max_output_chars
        self._max_log_limit = max_log_limit

    @property
    def workspace(self) -> ISoftwareWorkspace:
        return self._workspace

    # -------------------------------------------------------------------------
    # Internal Validation and Safety Helpers
    # -------------------------------------------------------------------------

    def _get_controlled_env(self) -> Dict[str, str]:
        """
        Derive a controlled, minimal subprocess environment.
        Disables interactive credential prompts and prevents token leaks.
        """
        controlled_env: Dict[str, str] = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "GIT_TERMINAL_PROMPT": "0",  # Never hang on interactive credential prompts
            "GIT_CONFIG_NOSYSTEM": "1",
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

    def _verify_repository_exists(self) -> Optional[GitResult]:
        """Verify workspace exists and contains a valid Git repository."""
        if not self._workspace.workspace_exists():
            return GitResult(
                success=False,
                operation=GitOperationType.STATUS,
                status=GitStatus.REPOSITORY_NOT_FOUND,
                error_type="WORKSPACE_NOT_FOUND",
                error_message=f"Workspace '{self._workspace.workspace_id}' does not exist or is inactive.",
            )

        git_dir = self._repo_path / ".git"
        if not git_dir.exists():
            return GitResult(
                success=False,
                operation=GitOperationType.STATUS,
                status=GitStatus.NOT_A_REPOSITORY,
                error_type="NOT_A_REPOSITORY",
                error_message=f"Workspace path '{self._repo_path}' is not a valid Git repository (.git not found).",
            )
        return None

    def _validate_branch_name(self, branch_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate Git branch ref name against strict security rules.
        Rejects traversal, flags, shell injection, and invalid ref syntax.
        """
        if not branch_name or not isinstance(branch_name, str):
            return False, "INVALID_INPUT: Branch name must be a non-empty string."

        name = branch_name.strip()
        if not name:
            return False, "INVALID_INPUT: Branch name cannot be empty or whitespace only."

        if len(name) > 100:
            return False, "INVALID_INPUT: Branch name exceeds maximum length of 100 characters."

        # Reject options / flags
        if name.startswith("-"):
            return False, "INVALID_INPUT: Branch name cannot start with '-' (option injection prevented)."

        # Reject path traversal and component escapes
        if name.startswith("/") or name.startswith("."):
            return False, "INVALID_INPUT: Branch name cannot start with '/' or '.'."

        if name.endswith("/") or name.endswith("."):
            return False, "INVALID_INPUT: Branch name cannot end with '/' or '.'."

        if name.endswith(".lock"):
            return False, "INVALID_INPUT: Branch name cannot end with '.lock'."

        if ".." in name or "//" in name or "@{" in name:
            return False, "INVALID_INPUT: Branch name cannot contain '..', '//', or '@{'."

        # Reject invalid ref characters
        invalid_chars = set("~^:?*[\t\r\n\0\\ @")
        if any(c in name for c in invalid_chars):
            return False, "INVALID_INPUT: Branch name contains forbidden or control characters."

        # Reject shell operators
        if any(c in name for c in FORBIDDEN_SHELL_CHARS):
            return False, "INVALID_INPUT: Branch name contains forbidden shell characters."

        if not BRANCH_NAME_PATTERN.match(name):
            return False, f"INVALID_INPUT: Branch name '{name}' contains invalid characters."

        return True, None

    def _validate_workspace_paths(
        self, paths: Optional[List[str]], allow_empty: bool = False
    ) -> Tuple[List[str], Optional[str]]:
        """
        Validate that paths are strictly workspace-relative and do not escape workspace root.
        Rejects option flags (-), parent traversals (..), absolute paths, and null/shell characters.
        """
        if paths is None:
            paths = []

        if not paths and not allow_empty:
            return [], "INVALID_INPUT: File paths list cannot be empty."

        validated: List[str] = []
        for p in paths:
            if not isinstance(p, str) or not p.strip():
                return [], "INVALID_INPUT: File path must be a non-empty string."

            p_clean = p.strip()

            # Prevent option injection
            if p_clean.startswith("-"):
                return [], f"INVALID_INPUT: Path '{p_clean}' cannot start with '-' (option injection rejected)."

            # Reject shell characters
            if any(c in p_clean for c in FORBIDDEN_SHELL_CHARS):
                return [], f"INVALID_INPUT: Path '{p_clean}' contains forbidden shell characters."

            # Reject parent traversal components
            p_obj = Path(p_clean)
            for part in p_obj.parts:
                if part == "..":
                    return [], f"PATH_TRAVERSAL_REJECTED: Parent traversal '..' in '{p_clean}'."

            # Reject absolute / drive paths
            if p_obj.is_absolute() or (len(p_clean) > 1 and p_clean[1] == ":"):
                return [], f"PATH_OUTSIDE_WORKSPACE_REJECTED: Absolute path '{p_clean}' is not workspace-relative."

            # Resolve within workspace root and verify strict containment
            full_path = self._repo_path / p_obj
            try:
                if full_path.exists() or full_path.is_symlink():
                    resolved_path = full_path.resolve()
                else:
                    resolved_parent = full_path.parent.resolve()
                    resolved_path = resolved_parent / full_path.name
            except Exception as e:
                return [], f"PATH_SECURITY_ERROR: Invalid path '{p_clean}': {e}"

            # Check subpath containment
            try:
                resolved_path.relative_to(self._repo_path)
            except ValueError:
                return [], f"PATH_OUTSIDE_WORKSPACE_REJECTED: Path '{p_clean}' resolves outside workspace root."

            # Normalize to forward slash relative string
            rel_str = str(resolved_path.relative_to(self._repo_path)).replace("\\", "/")
            validated.append(rel_str if rel_str != "" else ".")

        return validated, None

    def _validate_commit_message(self, message: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate commit message content, length, and non-empty status."""
        if not message or not isinstance(message, str):
            return False, "INVALID_INPUT: Commit message must be a non-empty string."

        msg = message.strip()
        if not msg:
            return False, "INVALID_INPUT: Commit message cannot be empty or whitespace only."

        if len(msg) > self.MAX_COMMIT_MESSAGE_LENGTH:
            return False, f"INVALID_INPUT: Commit message exceeds maximum length of {self.MAX_COMMIT_MESSAGE_LENGTH} characters."

        # Reject null bytes and non-whitespace control characters
        for c in msg:
            if c == "\0" or (ord(c) < 32 and c not in ("\t", "\n", "\r")):
                return False, "INVALID_INPUT: Commit message contains forbidden control characters."

        return True, None

    def _run_git(
        self,
        args: List[str],
        operation: GitOperationType,
    ) -> Tuple[bool, int, str, str, bool]:
        """
        Execute a Git command securely with shell=False and captured outputs.
        Returns (success, exit_code, stdout, stderr, is_truncated).
        """
        cmd_tokens = ["git"] + args
        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd_tokens,
                cwd=str(self._repo_path),
                shell=False,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                env=self._get_controlled_env(),
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            exit_code = proc.returncode

        except subprocess.TimeoutExpired as te:
            stdout = te.stdout or "" if isinstance(te.stdout, str) else ""
            stderr = te.stderr or "" if isinstance(te.stderr, str) else ""
            return False, 124, stdout, f"EXECUTION_TIMEOUT: Git operation timed out after {self._timeout_seconds}s.", False

        except FileNotFoundError:
            return False, 127, "", "GIT_NOT_FOUND: 'git' executable was not found on system path.", False

        except Exception as e:
            return False, 1, "", f"GIT_EXECUTION_ERROR: Failed to execute Git: {e}", False

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
        operation: GitOperationType,
        cmd_repr: str,
        exit_code: int,
        stdout: str,
        stderr: str,
        is_success: bool,
        extra_evidence: Optional[List[Any]] = None,
        fact_statement: Optional[str] = None,
    ) -> Tuple[List[FactItem], List[Union[ExecutionLogEvidence, ArtifactEvidence, DataEvidence, VerificationEvidence]]]:
        """Construct empirical execution log and verification evidence."""
        facts: List[FactItem] = []
        if fact_statement:
            facts.append(
                FactItem(
                    statement=fact_statement,
                    state=FactState.FACT if is_success else FactState.UNVERIFIED,
                    source="git_service",
                )
            )

        evidence_list: List[Union[ExecutionLogEvidence, ArtifactEvidence, DataEvidence, VerificationEvidence]] = []

        # 1. Execution Log Evidence
        log_snip = f"GIT_CMD: {cmd_repr}\nEXIT: {exit_code}\nSTDOUT:\n{stdout[:500]}\nSTDERR:\n{stderr[:500]}"
        evidence_list.append(
            ExecutionLogEvidence(
                evidence_id=f"ev-git-log-{uuid.uuid4().hex[:8]}",
                execution_id=f"exec-git-{uuid.uuid4().hex[:8]}",
                log_snippet=log_snip,
                exit_code=exit_code,
                description=f"Controlled Git {operation.value} execution log for '{cmd_repr}'",
            )
        )

        # 2. Extra evidence (artifacts / data)
        if extra_evidence:
            evidence_list.extend(extra_evidence)

        # 3. Verification Evidence
        evidence_list.append(
            VerificationEvidence(
                evidence_id=f"ev-git-verif-{uuid.uuid4().hex[:8]}",
                verifier_id="ControlledGitService",
                verified_status="VERIFIED" if is_success else "FAILED",
                description=f"Git operation verification for '{operation.value}' (exit code: {exit_code})",
            )
        )

        return facts, evidence_list

    # -------------------------------------------------------------------------
    # Approved IGitService Operations
    # -------------------------------------------------------------------------

    def status(self) -> GitResult:
        """Retrieve structured repository status."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.STATUS
            return repo_err

        success, exit_code, stdout, stderr, is_trunc = self._run_git(
            ["status", "--porcelain=v1", "-b"], GitOperationType.STATUS
        )

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.STATUS, "git status --porcelain=v1 -b", exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.STATUS,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_STATUS_FAILED",
                error_message=stderr or "Failed to query Git status.",
                facts=facts,
                evidence=ev,
            )

        # Parse porcelain v1 branch and changed files
        lines = stdout.splitlines()
        current_branch = "HEAD"
        staged_files: List[str] = []
        unstaged_files: List[str] = []
        changed_set = set()

        if lines and lines[0].startswith("##"):
            branch_line = lines[0][2:].strip()
            # Handle ## Initial commit on main or ## No commits yet on main or ## main...origin/main
            if "No commits yet on " in branch_line:
                current_branch = branch_line.replace("No commits yet on ", "").strip()
            elif "Initial commit on " in branch_line:
                current_branch = branch_line.replace("Initial commit on ", "").strip()
            elif "..." in branch_line:
                current_branch = branch_line.split("...")[0].strip()
            elif " " in branch_line:
                current_branch = branch_line.split()[0].strip()
            else:
                current_branch = branch_line

            lines = lines[1:]

        for line in lines:
            if len(line) < 3:
                continue
            idx_status = line[0]
            wt_status = line[1]
            file_name = line[3:].strip()
            # If rename e.g. "old -> new"
            if " -> " in file_name:
                file_name = file_name.split(" -> ")[1].strip()

            if idx_status in ("M", "A", "D", "R", "C"):
                staged_files.append(file_name)
                changed_set.add(file_name)
            if wt_status in ("M", "D", "?"):
                unstaged_files.append(file_name)
                changed_set.add(file_name)

        is_clean = len(changed_set) == 0
        git_status_state = GitStatus.CLEAN if is_clean else GitStatus.DIRTY

        fact_stmt = f"Git repository status in workspace '{self._workspace.workspace_id}': branch '{current_branch}', state {'CLEAN' if is_clean else 'DIRTY'} ({len(changed_set)} changed files)."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.STATUS,
            "git status --porcelain=v1 -b",
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.STATUS,
            status=git_status_state,
            branch=current_branch,
            staged_files=staged_files,
            unstaged_files=unstaged_files,
            changed_files=sorted(list(changed_set)),
            exit_code=0,
            is_truncated=is_trunc,
            facts=facts,
            evidence=ev,
        )

    def current_branch(self) -> GitResult:
        """Retrieve active Git branch name."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.CURRENT_BRANCH
            return repo_err

        success, exit_code, stdout, stderr, is_trunc = self._run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"], GitOperationType.CURRENT_BRANCH
        )

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.CURRENT_BRANCH, "git rev-parse --abbrev-ref HEAD", exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.CURRENT_BRANCH,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_BRANCH_QUERY_FAILED",
                error_message=stderr or "Failed to query current branch.",
                facts=facts,
                evidence=ev,
            )

        branch_name = stdout.strip()
        fact_stmt = f"Current active branch in workspace '{self._workspace.workspace_id}' is '{branch_name}'."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.CURRENT_BRANCH,
            "git rev-parse --abbrev-ref HEAD",
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.CURRENT_BRANCH,
            status=GitStatus.SUCCESS,
            branch=branch_name,
            exit_code=0,
            facts=facts,
            evidence=ev,
        )

    def list_branches(self) -> GitResult:
        """List local branches in repository."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.LIST_BRANCHES
            return repo_err

        success, exit_code, stdout, stderr, is_trunc = self._run_git(
            ["branch", "--list", "--format=%(refname:short)"], GitOperationType.LIST_BRANCHES
        )

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.LIST_BRANCHES, "git branch --list", exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.LIST_BRANCHES,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_BRANCH_LIST_FAILED",
                error_message=stderr or "Failed to list Git branches.",
                facts=facts,
                evidence=ev,
            )

        branches = [b.strip() for b in stdout.splitlines() if b.strip()]
        cur_branch_res = self.current_branch()
        active_branch = cur_branch_res.branch if cur_branch_res.success else None

        fact_stmt = f"Repository branches in workspace '{self._workspace.workspace_id}': {', '.join(branches)}."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.LIST_BRANCHES,
            "git branch --list",
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.LIST_BRANCHES,
            status=GitStatus.SUCCESS,
            branch=active_branch,
            branches=branches,
            exit_code=0,
            facts=facts,
            evidence=ev,
        )

    def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> GitResult:
        """Create a new branch securely."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.CREATE_BRANCH
            return repo_err

        valid, err_msg = self._validate_branch_name(branch_name)
        if not valid:
            return GitResult(
                success=False,
                operation=GitOperationType.CREATE_BRANCH,
                status=GitStatus.INVALID_INPUT,
                error_type="INVALID_BRANCH_NAME",
                error_message=err_msg,
            )

        args = ["branch", branch_name]
        if base_branch:
            valid_base, base_err = self._validate_branch_name(base_branch)
            if not valid_base:
                return GitResult(
                    success=False,
                    operation=GitOperationType.CREATE_BRANCH,
                    status=GitStatus.INVALID_INPUT,
                    error_type="INVALID_BASE_BRANCH",
                    error_message=f"Invalid base branch: {base_err}",
                )
            args = ["branch", branch_name, base_branch]

        cmd_repr = f"git {' '.join(args)}"
        success, exit_code, stdout, stderr, is_trunc = self._run_git(args, GitOperationType.CREATE_BRANCH)

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.CREATE_BRANCH, cmd_repr, exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.CREATE_BRANCH,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_CREATE_BRANCH_FAILED",
                error_message=stderr or f"Failed to create branch '{branch_name}'.",
                facts=facts,
                evidence=ev,
            )

        fact_stmt = f"Created new Git branch '{branch_name}' in workspace '{self._workspace.workspace_id}'."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.CREATE_BRANCH,
            cmd_repr,
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.CREATE_BRANCH,
            status=GitStatus.SUCCESS,
            branch=branch_name,
            message=f"Successfully created branch '{branch_name}'.",
            exit_code=0,
            facts=facts,
            evidence=ev,
        )

    def checkout_branch(self, branch_name: str) -> GitResult:
        """Checkout an existing validated Git branch."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.CHECKOUT_BRANCH
            return repo_err

        valid, err_msg = self._validate_branch_name(branch_name)
        if not valid:
            return GitResult(
                success=False,
                operation=GitOperationType.CHECKOUT_BRANCH,
                status=GitStatus.INVALID_INPUT,
                error_type="INVALID_BRANCH_NAME",
                error_message=err_msg,
            )

        args = ["checkout", branch_name]
        cmd_repr = f"git {' '.join(args)}"
        success, exit_code, stdout, stderr, is_trunc = self._run_git(args, GitOperationType.CHECKOUT_BRANCH)

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.CHECKOUT_BRANCH, cmd_repr, exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.CHECKOUT_BRANCH,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_CHECKOUT_FAILED",
                error_message=stderr or f"Failed to checkout branch '{branch_name}'.",
                facts=facts,
                evidence=ev,
            )

        fact_stmt = f"Switched to Git branch '{branch_name}' in workspace '{self._workspace.workspace_id}'."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.CHECKOUT_BRANCH,
            cmd_repr,
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.CHECKOUT_BRANCH,
            status=GitStatus.SUCCESS,
            branch=branch_name,
            message=f"Switched to branch '{branch_name}'.",
            exit_code=0,
            facts=facts,
            evidence=ev,
        )

    def diff(self, paths: Optional[List[str]] = None) -> GitResult:
        """Retrieve a bounded diff of workspace changes."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.DIFF
            return repo_err

        validated_paths: List[str] = []
        if paths:
            val_paths, err_msg = self._validate_workspace_paths(paths, allow_empty=True)
            if err_msg:
                return GitResult(
                    success=False,
                    operation=GitOperationType.DIFF,
                    status=GitStatus.INVALID_INPUT,
                    error_type="INVALID_PATH",
                    error_message=err_msg,
                )
            validated_paths = val_paths

        args = ["diff", "--"] + validated_paths if validated_paths else ["diff"]
        cmd_repr = f"git {' '.join(args)}"
        success, exit_code, stdout, stderr, is_trunc = self._run_git(args, GitOperationType.DIFF)

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.DIFF, cmd_repr, exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.DIFF,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_DIFF_FAILED",
                error_message=stderr or "Failed to compute Git diff.",
                facts=facts,
                evidence=ev,
            )

        fact_stmt = f"Computed Git diff for workspace '{self._workspace.workspace_id}' ({len(stdout)} chars)."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.DIFF,
            cmd_repr,
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.DIFF,
            status=GitStatus.SUCCESS,
            diff=stdout,
            exit_code=0,
            is_truncated=is_trunc,
            facts=facts,
            evidence=ev,
        )

    def stage_files(self, paths: List[str]) -> GitResult:
        """Stage explicit workspace-relative files for commit."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.STAGE_FILES
            return repo_err

        validated_paths, err_msg = self._validate_workspace_paths(paths, allow_empty=False)
        if err_msg:
            return GitResult(
                success=False,
                operation=GitOperationType.STAGE_FILES,
                status=GitStatus.INVALID_INPUT,
                error_type="INVALID_PATH",
                error_message=err_msg,
            )

        args = ["add", "--"] + validated_paths
        cmd_repr = f"git {' '.join(args)}"
        success, exit_code, stdout, stderr, is_trunc = self._run_git(args, GitOperationType.STAGE_FILES)

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.STAGE_FILES, cmd_repr, exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.STAGE_FILES,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_STAGE_FAILED",
                error_message=stderr or "Failed to stage files.",
                facts=facts,
                evidence=ev,
            )

        fact_stmt = f"Staged {len(validated_paths)} file(s) in workspace '{self._workspace.workspace_id}': {', '.join(validated_paths)}."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.STAGE_FILES,
            cmd_repr,
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.STAGE_FILES,
            status=GitStatus.SUCCESS,
            staged_files=validated_paths,
            message=f"Successfully staged {len(validated_paths)} file(s).",
            exit_code=0,
            facts=facts,
            evidence=ev,
        )

    def unstage_files(self, paths: List[str]) -> GitResult:
        """Unstage explicit workspace-relative files."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.UNSTAGE_FILES
            return repo_err

        validated_paths, err_msg = self._validate_workspace_paths(paths, allow_empty=False)
        if err_msg:
            return GitResult(
                success=False,
                operation=GitOperationType.UNSTAGE_FILES,
                status=GitStatus.INVALID_INPUT,
                error_type="INVALID_PATH",
                error_message=err_msg,
            )

        args = ["restore", "--staged", "--"] + validated_paths
        cmd_repr = f"git {' '.join(args)}"
        success, exit_code, stdout, stderr, is_trunc = self._run_git(args, GitOperationType.UNSTAGE_FILES)

        if not success:
            # Fallback to reset HEAD if restore is unsupported on older git
            args_fallback = ["reset", "HEAD", "--"] + validated_paths
            cmd_repr = f"git {' '.join(args_fallback)}"
            success, exit_code, stdout, stderr, is_trunc = self._run_git(args_fallback, GitOperationType.UNSTAGE_FILES)

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.UNSTAGE_FILES, cmd_repr, exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.UNSTAGE_FILES,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_UNSTAGE_FAILED",
                error_message=stderr or "Failed to unstage files.",
                facts=facts,
                evidence=ev,
            )

        fact_stmt = f"Unstaged {len(validated_paths)} file(s) in workspace '{self._workspace.workspace_id}': {', '.join(validated_paths)}."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.UNSTAGE_FILES,
            cmd_repr,
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.UNSTAGE_FILES,
            status=GitStatus.SUCCESS,
            unstaged_files=validated_paths,
            message=f"Successfully unstaged {len(validated_paths)} file(s).",
            exit_code=0,
            facts=facts,
            evidence=ev,
        )

    def commit(self, message: str) -> GitResult:
        """Create a commit with a validated, bounded commit message."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.COMMIT
            return repo_err

        valid, err_msg = self._validate_commit_message(message)
        if not valid:
            return GitResult(
                success=False,
                operation=GitOperationType.COMMIT,
                status=GitStatus.INVALID_INPUT,
                error_type="INVALID_COMMIT_MESSAGE",
                error_message=err_msg,
            )

        msg_clean = message.strip()
        args = ["commit", "-m", msg_clean]
        cmd_repr = f"git commit -m [bounded_message_len_{len(msg_clean)}]"
        success, exit_code, stdout, stderr, is_trunc = self._run_git(args, GitOperationType.COMMIT)

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.COMMIT, cmd_repr, exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.COMMIT,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_COMMIT_FAILED",
                error_message=stderr or stdout or "Commit failed (ensure changes are staged).",
                facts=facts,
                evidence=ev,
            )

        # Retrieve new commit ID
        rev_ok, _, rev_out, _, _ = self._run_git(["rev-parse", "HEAD"], GitOperationType.COMMIT)
        commit_id = rev_out.strip() if rev_ok else "UNKNOWN"

        extra_ev: List[Any] = []
        if commit_id != "UNKNOWN":
            extra_ev.append(
                ArtifactEvidence(
                    evidence_id=f"ev-commit-{commit_id[:8]}",
                    artifact_uri=f"git://commit/{commit_id}",
                    mime_type="text/vnd.git-commit",
                    checksum_sha256=commit_id,
                    description=f"Git commit created: {commit_id[:8]} - {msg_clean[:60]}",
                )
            )

        fact_stmt = f"Committed changes with commit ID '{commit_id[:8]}' in workspace '{self._workspace.workspace_id}': '{msg_clean[:60]}'."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.COMMIT,
            cmd_repr,
            exit_code,
            stdout,
            stderr,
            True,
            extra_evidence=extra_ev,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.COMMIT,
            status=GitStatus.SUCCESS,
            commit_id=commit_id,
            commit_message=msg_clean,
            message=f"Committed changes with commit ID {commit_id[:8]}.",
            exit_code=0,
            facts=facts,
            evidence=ev,
        )

    def log(self, limit: int = 10) -> GitResult:
        """Retrieve recent structured commit log entries."""
        repo_err = self._verify_repository_exists()
        if repo_err:
            repo_err.operation = GitOperationType.LOG
            return repo_err

        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0 or limit > self._max_log_limit:
            return GitResult(
                success=False,
                operation=GitOperationType.LOG,
                status=GitStatus.INVALID_INPUT,
                error_type="INVALID_LOG_LIMIT",
                error_message=f"INVALID_INPUT: Log limit must be an integer between 1 and {self._max_log_limit}.",
            )

        args = [
            "log",
            f"-n{limit}",
            "--format=%H%x1f%an%x1f%ad%x1f%s",
            "--date=iso",
        ]
        cmd_repr = f"git log -n{limit}"
        success, exit_code, stdout, stderr, is_trunc = self._run_git(args, GitOperationType.LOG)

        if not success:
            facts, ev = self._build_evidence_and_facts(
                GitOperationType.LOG, cmd_repr, exit_code, stdout, stderr, False
            )
            return GitResult(
                success=False,
                operation=GitOperationType.LOG,
                status=GitStatus.FAILED,
                exit_code=exit_code,
                error_type="GIT_LOG_FAILED",
                error_message=stderr or "Failed to retrieve Git log (repository may have no commits).",
                facts=facts,
                evidence=ev,
            )

        entries: List[GitLogEntry] = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\x1f")
            if len(parts) >= 4:
                entries.append(
                    GitLogEntry(
                        commit_id=parts[0].strip(),
                        author=parts[1].strip(),
                        date=parts[2].strip(),
                        message=parts[3].strip(),
                    )
                )

        fact_stmt = f"Retrieved {len(entries)} Git commit log entries in workspace '{self._workspace.workspace_id}'."
        facts, ev = self._build_evidence_and_facts(
            GitOperationType.LOG,
            cmd_repr,
            exit_code,
            stdout,
            stderr,
            True,
            fact_statement=fact_stmt,
        )

        return GitResult(
            success=True,
            operation=GitOperationType.LOG,
            status=GitStatus.SUCCESS,
            log_entries=entries,
            exit_code=0,
            is_truncated=is_trunc,
            facts=facts,
            evidence=ev,
        )
