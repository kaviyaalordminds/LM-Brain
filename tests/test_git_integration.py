"""
Comprehensive unit and security test suite for Controlled Git / Version Control Integration Layer.
Tests repository state, branches, diffs, staging, commits, logs, security guardrails,
evidence generation, and SpecialistExecutionEngine integration.
"""

from datetime import datetime
import inspect
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import List, Optional
import pytest

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionAdapter,
    SpecialistExecutionEngine,
)
from executive_twins.execution.security_guard import SecurityGuard
from executive_twins.git import (
    BaseGitCapabilityHandler,
    ControlledGitService,
    DevGitServiceAdapter,
    GitBranchCapabilityHandler,
    GitCommitCapabilityHandler,
    GitDiffCapabilityHandler,
    GitLogCapabilityHandler,
    GitLogEntry,
    GitOperationType,
    GitRequest,
    GitResult,
    GitStageCapabilityHandler,
    GitStatus,
    GitStatusCapabilityHandler,
    GitUnstageCapabilityHandler,
    IGitService,
)
from executive_twins.schemas.common import (
    FailureState,
    SecurityContext,
    SpecialistStatus,
    VerificationStatus,
)
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    ExecutionLogEvidence,
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
def git_workspace(temp_dir):
    """Create and initialize a LocalSoftwareWorkspace with a Git repository."""
    ws_path = os.path.join(temp_dir, "ws_git_test")
    ws = LocalSoftwareWorkspace(workspace_id="ws-git-01", root_path=ws_path)
    ws.create_workspace()

    # Initialize git repo with initial commit and identity
    subprocess.run(["git", "init"], cwd=ws_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Specialist"], cwd=ws_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "specialist@lordminds.internal"], cwd=ws_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=ws_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "core.safecrlf", "false"], cwd=ws_path, check=True, capture_output=True)

    # Initial file and commit
    readme_path = os.path.join(ws_path, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Git Workspace Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=ws_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=ws_path, check=True, capture_output=True)

    return ws


@pytest.fixture
def git_service(git_workspace):
    return ControlledGitService(workspace=git_workspace)


# ---------------------------------------------------------------------------
# 1. Repository State Tests (1-5)
# ---------------------------------------------------------------------------

def test_1_status_on_valid_repository(git_service):
    """1. Status on valid repository returns structured GitResult."""
    res = git_service.status()
    assert res.success is True
    assert res.operation == GitOperationType.STATUS
    assert res.status in (GitStatus.CLEAN, GitStatus.DIRTY)
    assert res.branch is not None
    assert isinstance(res.changed_files, list)


def test_2_status_on_clean_repository(git_service):
    """2. Status on clean repository returns CLEAN status and 0 changed files."""
    res = git_service.status()
    assert res.success is True
    assert res.status == GitStatus.CLEAN
    assert len(res.changed_files) == 0
    assert len(res.staged_files) == 0
    assert len(res.unstaged_files) == 0


def test_3_status_on_dirty_repository(git_workspace, git_service):
    """3. Status on dirty repository returns DIRTY status with staged and unstaged files."""
    git_workspace.write_file("new_file.txt", "content")
    res = git_service.status()
    assert res.success is True
    assert res.status == GitStatus.DIRTY
    assert "new_file.txt" in res.changed_files
    assert "new_file.txt" in res.unstaged_files


def test_4_current_branch(git_service):
    """4. Current branch returns the active branch name."""
    res = git_service.current_branch()
    assert res.success is True
    assert res.operation == GitOperationType.CURRENT_BRANCH
    assert res.status == GitStatus.SUCCESS
    assert res.branch in ("main", "master")


def test_5_list_branches(git_service):
    """5. List branches returns array of branch names."""
    res = git_service.list_branches()
    assert res.success is True
    assert res.operation == GitOperationType.LIST_BRANCHES
    assert res.status == GitStatus.SUCCESS
    assert len(res.branches) >= 1
    assert any(b in ("main", "master") for b in res.branches)


# ---------------------------------------------------------------------------
# 2. Branch Operations and Security Tests (6-13)
# ---------------------------------------------------------------------------

def test_6_create_valid_branch(git_service):
    """6. Create valid branch succeeds and appears in branch list."""
    res = git_service.create_branch("feature/auth-service")
    assert res.success is True
    assert res.status == GitStatus.SUCCESS
    assert res.branch == "feature/auth-service"

    list_res = git_service.list_branches()
    assert "feature/auth-service" in list_res.branches


def test_7_reject_empty_branch(git_service):
    """7. Reject empty or whitespace branch name."""
    res = git_service.create_branch("")
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT

    res2 = git_service.create_branch("   ")
    assert res2.success is False
    assert res2.status == GitStatus.INVALID_INPUT


def test_8_reject_malformed_branch(git_service):
    """8. Reject malformed branch names with forbidden characters."""
    bad_branches = ["branch with space", "feature~1", "feature^2", "feature:bad", "feature?test", "feature*glob", "feature[1]"]
    for bad in bad_branches:
        res = git_service.create_branch(bad)
        assert res.success is False
        assert res.status == GitStatus.INVALID_INPUT


def test_9_reject_traversal_like_branch(git_service):
    """9. Reject traversal-like branch names."""
    bad_branches = ["../escape", "feature/../bad", "..", "/root_branch", "branch.lock", "branch/"]
    for bad in bad_branches:
        res = git_service.create_branch(bad)
        assert res.success is False
        assert res.status == GitStatus.INVALID_INPUT


def test_10_reject_shell_injection_branch(git_service):
    """10. Reject shell-injection branch names."""
    injections = ["branch;rm -rf /", "feature$(whoami)", "feature`id`", "feat&&calc", "feat|touch", "feat>out"]
    for inj in injections:
        res = git_service.create_branch(inj)
        assert res.success is False
        assert res.status == GitStatus.INVALID_INPUT


def test_11_checkout_valid_existing_branch(git_service):
    """11. Checkout valid existing branch switches active branch."""
    git_service.create_branch("feature/checkout-test")
    res = git_service.checkout_branch("feature/checkout-test")
    assert res.success is True
    assert res.status == GitStatus.SUCCESS
    assert res.branch == "feature/checkout-test"

    cur = git_service.current_branch()
    assert cur.branch == "feature/checkout-test"


def test_12_reject_nonexistent_branch(git_service):
    """12. Reject checkout of nonexistent branch."""
    res = git_service.checkout_branch("nonexistent-branch-xyz")
    assert res.success is False
    assert res.status == GitStatus.FAILED


def test_13_reject_destructive_checkout(git_service):
    """13. Reject destructive checkout attempts like '.' or paths."""
    destructive_targets = [".", "-- .", "-f", "-B main", "HEAD~1 -- ."]
    for tgt in destructive_targets:
        res = git_service.checkout_branch(tgt)
        assert res.success is False
        assert res.status in (GitStatus.INVALID_INPUT, GitStatus.FAILED)


# ---------------------------------------------------------------------------
# 3. Diff Operations and Security Tests (14-20)
# ---------------------------------------------------------------------------

def test_14_diff_valid_repository(git_workspace, git_service):
    """14. Diff valid repository returns changes."""
    git_workspace.write_file("README.md", "# Modified Content\n")
    res = git_service.diff()
    assert res.success is True
    assert res.status == GitStatus.SUCCESS
    assert "Modified Content" in (res.diff or "")


def test_15_diff_specific_valid_file(git_workspace, git_service):
    """15. Diff specific valid file returns scoped diff."""
    git_workspace.write_file("README.md", "# Modified README\n")
    git_workspace.write_file("file2.txt", "file2 content\n")
    res = git_service.diff(paths=["README.md"])
    assert res.success is True
    assert res.status == GitStatus.SUCCESS
    assert "Modified README" in (res.diff or "")
    assert "file2 content" not in (res.diff or "")


def test_16_reject_diff_absolute_path(git_service):
    """16. Reject absolute outside path in diff."""
    abs_path = "C:\\Windows\\System32\\calc.exe" if os.name == "nt" else "/etc/passwd"
    res = git_service.diff(paths=[abs_path])
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_17_reject_diff_parent_traversal(git_service):
    """17. Reject '../' parent traversal in diff."""
    res = git_service.diff(paths=["../outside.txt"])
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_18_reject_diff_windows_traversal(git_service):
    """18. Reject Windows traversal in diff."""
    res = git_service.diff(paths=["..\\..\\secret.txt"])
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_19_reject_diff_symlink_escape(temp_dir, git_workspace, git_service):
    """19. Reject symlink escaping workspace root."""
    outside_file = os.path.join(temp_dir, "outside_target.txt")
    with open(outside_file, "w") as f:
        f.write("secret")
    symlink_path = os.path.join(git_workspace.root_path, "symlink_escape.txt")
    try:
        os.symlink(outside_file, symlink_path)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation requires elevated privileges on this Windows system.")

    res = git_service.diff(paths=["symlink_escape.txt"])
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_20_enforce_diff_output_limit(git_workspace):
    """20. Enforce bounded diff output and is_truncated flag."""
    bounded_service = ControlledGitService(workspace=git_workspace, max_output_chars=500)
    # Write a large modification
    large_content = "line " * 2000 + "\n"
    git_workspace.write_file("README.md", large_content)
    res = bounded_service.diff()
    assert res.success is True
    assert res.is_truncated is True
    assert len(res.diff) <= 700


# ---------------------------------------------------------------------------
# 4. Staging Operations and Security Tests (21-28)
# ---------------------------------------------------------------------------

def test_21_stage_explicit_file(git_workspace, git_service):
    """21. Stage explicit file successfully."""
    git_workspace.write_file("app.py", "print('hello')\n")
    res = git_service.stage_files(["app.py"])
    assert res.success is True
    assert res.status == GitStatus.SUCCESS
    assert "app.py" in res.staged_files

    st = git_service.status()
    assert "app.py" in st.staged_files


def test_22_stage_multiple_explicit_files(git_workspace, git_service):
    """22. Stage multiple explicit files."""
    git_workspace.write_file("f1.txt", "1")
    git_workspace.write_file("f2.txt", "2")
    res = git_service.stage_files(["f1.txt", "f2.txt"])
    assert res.success is True
    assert "f1.txt" in res.staged_files
    assert "f2.txt" in res.staged_files


def test_23_unstage_explicit_file(git_workspace, git_service):
    """23. Unstage explicit file successfully."""
    git_workspace.write_file("to_unstage.txt", "temp")
    git_service.stage_files(["to_unstage.txt"])
    res = git_service.unstage_files(["to_unstage.txt"])
    assert res.success is True
    assert "to_unstage.txt" in res.unstaged_files

    st = git_service.status()
    assert "to_unstage.txt" in st.unstaged_files


def test_24_reject_stage_outside_path(git_service):
    """24. Reject staging path outside workspace."""
    res = git_service.stage_files(["../../outside.py"])
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_25_reject_stage_path_beginning_with_dash(git_service):
    """25. Reject staging path beginning with '-'."""
    res = git_service.stage_files(["-A", "--all", "-f"])
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_26_reject_stage_shell_operators(git_service):
    """26. Reject staging path with shell operators."""
    res = git_service.stage_files(["file.py;rm -rf /", "file|calc"])
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_27_reject_stage_arbitrary_flags(git_service):
    """27. Reject arbitrary flags in stage/unstage."""
    res1 = git_service.stage_files(["--force"])
    assert res1.success is False
    res2 = git_service.unstage_files(["-p"])
    assert res2.success is False


def test_28_verify_staging_result(git_workspace, git_service):
    """28. Verify staging result contains facts and evidence."""
    git_workspace.write_file("verified.py", "x = 10")
    res = git_service.stage_files(["verified.py"])
    assert res.success is True
    assert len(res.facts) >= 1
    assert len(res.evidence) >= 2  # Log evidence + Verification evidence


# ---------------------------------------------------------------------------
# 5. Commit Operations and Security Tests (29-34)
# ---------------------------------------------------------------------------

def test_29_successful_commit(git_workspace, git_service):
    """29. Successful commit creates a new commit."""
    git_workspace.write_file("commit_test.py", "print('commit')")
    git_service.stage_files(["commit_test.py"])
    res = git_service.commit("Add commit_test.py feature")
    assert res.success is True
    assert res.status == GitStatus.SUCCESS
    assert res.commit_id is not None
    assert res.commit_message == "Add commit_test.py feature"


def test_30_commit_result_contains_commit_id(git_workspace, git_service):
    """30. Commit result contains valid SHA commit ID."""
    git_workspace.write_file("id_test.txt", "content")
    git_service.stage_files(["id_test.txt"])
    res = git_service.commit("Test commit ID")
    assert res.success is True
    assert len(res.commit_id) >= 7


def test_31_reject_invalid_commit_message(git_service):
    """31. Reject empty or invalid commit message."""
    res1 = git_service.commit("")
    assert res1.success is False
    assert res1.status == GitStatus.INVALID_INPUT

    res2 = git_service.commit("   ")
    assert res2.success is False
    assert res2.status == GitStatus.INVALID_INPUT


def test_32_reject_excessively_large_commit_message(git_service):
    """32. Reject excessively large commit message."""
    huge_msg = "A" * 5000
    res = git_service.commit(huge_msg)
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_33_prevent_option_injection_in_commit(git_workspace, git_service):
    """33. Prevent option injection in commit message."""
    git_workspace.write_file("opt_test.txt", "data")
    git_service.stage_files(["opt_test.txt"])
    # Commit message with flag syntax should be safely escaped as a string
    res = git_service.commit("--amend -m 'hacked'")
    assert res.success is True
    assert res.commit_message == "--amend -m 'hacked'"


def test_34_verify_repository_state_after_commit(git_workspace, git_service):
    """34. Verify repository state is CLEAN after staging and committing all changes."""
    git_workspace.write_file("clean_test.py", "val = 42")
    git_service.stage_files(["clean_test.py"])
    git_service.commit("Clean state check commit")

    st = git_service.status()
    assert st.success is True
    assert st.status == GitStatus.CLEAN
    assert len(st.changed_files) == 0


# ---------------------------------------------------------------------------
# 6. Log Operations and Bounding Tests (35-37)
# ---------------------------------------------------------------------------

def test_35_retrieve_bounded_log(git_workspace, git_service):
    """35. Retrieve bounded commit log entries."""
    for i in range(3):
        git_workspace.write_file(f"log_{i}.txt", f"data {i}")
        git_service.stage_files([f"log_{i}.txt"])
        git_service.commit(f"Commit #{i}")

    res = git_service.log(limit=2)
    assert res.success is True
    assert res.status == GitStatus.SUCCESS
    assert len(res.log_entries) == 2
    assert isinstance(res.log_entries[0], GitLogEntry)
    assert res.log_entries[0].commit_id is not None
    assert res.log_entries[0].message == "Commit #2"


def test_36_enforce_maximum_log_limit(git_service):
    """36. Enforce maximum log limit (reject > 50)."""
    res = git_service.log(limit=100)
    assert res.success is False
    assert res.status == GitStatus.INVALID_INPUT


def test_37_reject_invalid_log_limit(git_service):
    """37. Reject negative or zero log limit."""
    res_zero = git_service.log(limit=0)
    assert res_zero.success is False
    assert res_zero.status == GitStatus.INVALID_INPUT

    res_neg = git_service.log(limit=-5)
    assert res_neg.success is False
    assert res_neg.status == GitStatus.INVALID_INPUT


# ---------------------------------------------------------------------------
# 7. Security and Isolation Tests (38-49)
# ---------------------------------------------------------------------------

def test_38_no_shell_true_in_implementation():
    """38. Verify implementation does NOT use shell=True."""
    from executive_twins.git import git_service as gs_module
    src = inspect.getsource(gs_module)
    assert "shell=True" not in src
    assert "shell=False" in src


def test_39_no_os_system_in_implementation():
    """39. Verify implementation does NOT use os.system."""
    from executive_twins.git import git_service as gs_module
    src = inspect.getsource(gs_module)
    assert "os.system(" not in src


def test_40_no_eval_in_implementation():
    """40. Verify implementation does NOT use eval()."""
    from executive_twins.git import git_service as gs_module
    src = inspect.getsource(gs_module)
    assert "eval(" not in src


def test_41_no_exec_in_implementation():
    """41. Verify implementation does NOT use exec()."""
    from executive_twins.git import git_service as gs_module
    src = inspect.getsource(gs_module)
    assert "exec(" not in src


def test_42_no_arbitrary_command_string():
    """42. Verify GitRequest strictly forbids raw/arbitrary command strings."""
    with pytest.raises(Exception):
        GitRequest(
            operation=GitOperationType.STATUS,
            workspace_id="ws-1",
            raw_command="git status",  # type: ignore
        )


def test_43_no_arbitrary_git_executable_arguments(git_service):
    """43. ControlledGitService public interface has no generic run/execute method."""
    assert not hasattr(git_service, "execute")
    assert not hasattr(git_service, "run")
    assert not hasattr(git_service, "run_git")


def test_44_no_remote_manipulation(git_service):
    """44. Remote manipulation methods do not exist."""
    assert not hasattr(git_service, "remote_add")
    assert not hasattr(git_service, "remote_remove")
    assert not hasattr(git_service, "remote_set_url")


def test_45_no_force_push_capability(git_service):
    """45. Push and force-push capabilities are not implemented in V1."""
    assert not hasattr(git_service, "push")
    assert not hasattr(git_service, "force_push")


def test_46_no_destructive_reset(git_service):
    """46. Destructive reset --hard is not exposed."""
    assert not hasattr(git_service, "reset_hard")


def test_47_no_destructive_clean(git_service):
    """47. Destructive clean (-fd/-fdx) is not exposed."""
    assert not hasattr(git_service, "clean")


def test_48_no_credential_access(git_service):
    """48. Credential operations and config modifications are not exposed."""
    assert not hasattr(git_service, "config")
    assert not hasattr(git_service, "credential")


def test_49_no_arbitrary_environment_injection(git_service):
    """49. Subprocess environment is controlled internally without specialist injection."""
    env = git_service._get_controlled_env()
    assert env.get("GIT_TERMINAL_PROMPT") == "0"
    assert env.get("GIT_CONFIG_NOSYSTEM") == "1"


# ---------------------------------------------------------------------------
# 8. Specialist Execution Engine Integration Tests (50-55)
# ---------------------------------------------------------------------------

@pytest.fixture
def specialist_setup(git_workspace):
    """Set up registry, workspace adapter, git adapter, handlers, and engine."""
    ws_adapter = DevTestWorkspaceAdapter()
    ws_adapter._active_workspaces[git_workspace.workspace_id] = git_workspace

    git_adapter = DevGitServiceAdapter(workspace_adapter=ws_adapter)

    # Specialists: 1 authorized (Web Dev), 1 unauthorized (Data Analyst), 1 inactive
    web_dev = SpecialistMetadata(
        specialist_id="spec-web-dev",
        name="Web Development Specialist",
        authorized_tools=["git", "code_generator", "static_analyzer"],
        capabilities=[
            Capability(name="git_status", description="Git status inspection"),
            Capability(name="git_commit", description="Git commit creation"),
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
        specialist_id="spec-inactive",
        name="Inactive Specialist",
        authorized_tools=["git"],
        capabilities=[],
        status=SpecialistStatus.INACTIVE,
    )

    registry = InMemorySpecialistRegistryAdapter()
    registry.register_specialist(web_dev)
    registry.register_specialist(unauthorized_spec)
    registry.register_specialist(inactive_spec)

    engine = SpecialistExecutionEngine(registry_client=registry)
    # Register Git handlers
    engine.register_handler(GitStatusCapabilityHandler(adapter=git_adapter))
    engine.register_handler(GitBranchCapabilityHandler(adapter=git_adapter))
    engine.register_handler(GitDiffCapabilityHandler(adapter=git_adapter))
    engine.register_handler(GitStageCapabilityHandler(adapter=git_adapter))
    engine.register_handler(GitUnstageCapabilityHandler(adapter=git_adapter))
    engine.register_handler(GitCommitCapabilityHandler(adapter=git_adapter))
    engine.register_handler(GitLogCapabilityHandler(adapter=git_adapter))

    return engine, git_workspace


def test_50_authorized_specialist_can_execute_git_capability(specialist_setup):
    """50. Authorized specialist can execute Git capability through SpecialistExecutionEngine."""
    engine, workspace = specialist_setup
    req = DelegationRequest(
        delegation_id="del-git-01",
        parent_task_id="task-git-01",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Inspect Git status",
        task="Check Git status of workspace",
        required_capabilities=["git_status"],
        inputs={"workspace_id": workspace.workspace_id},
        expected_output="Git status summary",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    result = engine.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.verification_status == VerificationStatus.VERIFIED
    assert "Branch:" in result.output


def test_51_unauthorized_specialist_is_blocked(specialist_setup):
    """51. Unauthorized specialist is blocked with AUTHORIZATION_DENIED."""
    engine, workspace = specialist_setup
    req = DelegationRequest(
        delegation_id="del-git-02",
        parent_task_id="task-git-02",
        executive_twin_id="twin-cto",
        specialist_id="spec-data-analyst",
        objective="Inspect Git status unauthorized",
        task="Check Git status",
        required_capabilities=["git_status"],
        inputs={"workspace_id": workspace.workspace_id},
        expected_output="Git status summary",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert result.verification_status == VerificationStatus.FAILED
    assert "AUTHORIZATION_DENIED" in result.output


def test_52_inactive_specialist_is_blocked(specialist_setup):
    """52. Inactive specialist is blocked from executing Git capability."""
    engine, workspace = specialist_setup
    req = DelegationRequest(
        delegation_id="del-git-03",
        parent_task_id="task-git-03",
        executive_twin_id="twin-cto",
        specialist_id="spec-inactive",
        objective="Inspect Git status inactive",
        task="Check Git status",
        required_capabilities=["git_status"],
        inputs={"workspace_id": workspace.workspace_id},
        expected_output="Git status summary",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    result = engine.execute_delegation(req)
    assert result.status == "FAILED"
    assert "CAPABILITY_UNAVAILABLE" in result.output


def test_53_handler_routes_to_correct_git_operation(specialist_setup):
    """53. Handlers correctly route to commit and log operations through engine."""
    engine, workspace = specialist_setup
    workspace.write_file("route_test.txt", "route data")

    # 1. Stage via engine
    stage_req = DelegationRequest(
        delegation_id="del-git-stage",
        parent_task_id="task-git-stage",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Stage changes",
        task="Stage changes",
        required_capabilities=["git_stage"],
        inputs={"workspace_id": workspace.workspace_id, "paths": ["route_test.txt"]},
        expected_output="Staging confirmation",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    res_stage = engine.execute_delegation(stage_req)
    assert res_stage.status == "SUCCESS"

    # 2. Commit via engine
    commit_req = DelegationRequest(
        delegation_id="del-git-commit",
        parent_task_id="task-git-commit",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Commit changes",
        task="Commit changes",
        required_capabilities=["git_commit"],
        inputs={"workspace_id": workspace.workspace_id, "message": "Engine routed commit"},
        expected_output="Commit confirmation",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    res_commit = engine.execute_delegation(commit_req)
    assert res_commit.status == "SUCCESS"

    # 3. Log via engine
    log_req = DelegationRequest(
        delegation_id="del-git-log",
        parent_task_id="task-git-log",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="View log",
        task="View commit history",
        required_capabilities=["git_log"],
        inputs={"workspace_id": workspace.workspace_id, "limit": 5},
        expected_output="Log summary",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    res_log = engine.execute_delegation(log_req)
    assert res_log.status == "SUCCESS"
    assert "Engine routed commit" in res_log.output


def test_54_evidence_is_generated(specialist_setup):
    """54. Evidence is generated and attached to delegation result."""
    engine, workspace = specialist_setup
    req = DelegationRequest(
        delegation_id="del-git-ev",
        parent_task_id="task-git-ev",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Evidence check",
        task="Check Git status with evidence",
        required_capabilities=["git_status"],
        inputs={"workspace_id": workspace.workspace_id},
        expected_output="Status summary",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    result = engine.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert result.evidence is not None
    assert result.evidence.contains_category(EvidenceCategory.EXECUTION_LOG)
    assert result.evidence.contains_category(EvidenceCategory.VERIFICATION)


def test_55_verification_evidence_is_generated(specialist_setup):
    """55. Verification evidence confirms empirical execution."""
    engine, workspace = specialist_setup
    req = DelegationRequest(
        delegation_id="del-git-verif",
        parent_task_id="task-git-verif",
        executive_twin_id="twin-cto",
        specialist_id="spec-web-dev",
        objective="Verification check",
        task="Check Git status verification",
        required_capabilities=["git_status"],
        inputs={"workspace_id": workspace.workspace_id},
        expected_output="Status summary",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    result = engine.execute_delegation(req)
    verif_items = result.evidence.get_by_category(EvidenceCategory.VERIFICATION)
    assert len(verif_items) >= 1
    assert any(v.verified_status == "VERIFIED" for v in verif_items)  # type: ignore


# ---------------------------------------------------------------------------
# 9. Regression and Integrity Tests (56-60)
# ---------------------------------------------------------------------------

def test_56_existing_specialist_execution_engine_remains_functional():
    """56. Existing standard capabilities remain functional in SpecialistExecutionEngine."""
    spec = SpecialistMetadata(
        specialist_id="spec-analyzer",
        name="Code Quality Specialist",
        authorized_tools=["static_analyzer"],
        capabilities=[Capability(name="code_analysis", description="Static code analysis")],
        status=SpecialistStatus.ACTIVE,
    )
    registry = InMemorySpecialistRegistryAdapter()
    registry.register_specialist(spec)
    engine = SpecialistExecutionEngine(registry_client=registry)

    req = DelegationRequest(
        delegation_id="del-reg-01",
        parent_task_id="task-reg-01",
        executive_twin_id="twin-cto",
        specialist_id="spec-analyzer",
        objective="Code analysis",
        task="Analyze source file",
        required_capabilities=["code_analysis"],
        inputs={"source_code_path": "src/main.py"},
        expected_output="Analysis result",
        security_context=SecurityContext(caller_id="cmo-twin", is_authenticated=True),
    )
    result = engine.execute_delegation(req)
    assert result.status == "SUCCESS"
    assert "Static code analysis completed" in result.output


def test_57_existing_workspace_tests_remain_functional(git_workspace):
    """57. Existing workspace operations remain fully functional."""
    res = git_workspace.write_file("test_ws.txt", "ws content")
    assert res.success is True
    read_res = git_workspace.read_file("test_ws.txt")
    assert read_res.success is True
    assert read_res.content == "ws content"


def test_58_existing_files_api_remains_functional(git_workspace):
    """58. Existing FileService remains functional in workspace."""
    from executive_twins.files.file_service import FileService
    fs = FileService(workspace=git_workspace)
    res = fs.create_file("file_api.txt", "file content")
    assert res.success is True
    read_res = fs.read_file("file_api.txt")
    assert read_res.success is True
    assert read_res.content == "file content"


def test_59_existing_command_execution_remains_functional(git_workspace):
    """59. Existing ControlledCommandExecutor remains functional in workspace."""
    from executive_twins.command_execution import (
        CommandRequest,
        CommandType,
        ControlledCommandExecutor,
    )
    git_workspace.write_file("test_script.py", "def test_val(): assert 1 == 1")
    executor = ControlledCommandExecutor(workspace=git_workspace)
    req = CommandRequest(
        command_type=CommandType.TEST,
        executable="python",
        arguments=["-m", "pytest", "test_script.py"],
        workspace_id=git_workspace.workspace_id,
    )
    res = executor.execute(req)
    assert res.success is True
    assert res.exit_code == 0


def test_60_not_a_repository_handling(temp_dir):
    """60. Non-git workspace returns NOT_A_REPOSITORY failure result."""
    non_git_path = os.path.join(temp_dir, "non_git_ws")
    ws = LocalSoftwareWorkspace(workspace_id="ws-nongit-01", root_path=non_git_path)
    ws.create_workspace()
    service = ControlledGitService(workspace=ws)

    res = service.status()
    assert res.success is False
    assert res.status == GitStatus.NOT_A_REPOSITORY
