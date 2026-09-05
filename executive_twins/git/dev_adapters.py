"""
DEV/TEST adapters and registered Git capability execution handlers.
Used for local development and testing without production cloud containers.
"""

from typing import Dict, List, Optional, Tuple

from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.git.git_service import ControlledGitService
from executive_twins.git.interfaces import IGitService
from executive_twins.git.models import GitResult, GitStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import SpecialistMetadata
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


class DevGitServiceAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Manages ControlledGitService instances for active workspaces.
    THIS IS NOT THE PRODUCTION SANDBOX CONTAINER INTEGRATION.
    """

    def __init__(self, workspace_adapter: DevTestWorkspaceAdapter) -> None:
        self.workspace_adapter = workspace_adapter
        self._active_services: Dict[str, IGitService] = {}

    def get_git_service(self, workspace_id: str) -> Optional[IGitService]:
        """Get or create a ControlledGitService for a workspace."""
        if workspace_id in self._active_services:
            return self._active_services[workspace_id]

        workspace = self.workspace_adapter.get_workspace(workspace_id)
        if not workspace or not workspace.workspace_exists():
            return None

        service = ControlledGitService(workspace=workspace)
        self._active_services[workspace_id] = service
        return service


class BaseGitCapabilityHandler(BaseCapabilityHandler):
    """Abstract base capability handler for controlled Git operations."""
    required_tool = "git"

    def __init__(self, adapter: DevGitServiceAdapter) -> None:
        self.adapter = adapter

    def _get_service(self, workspace_id: str) -> Tuple[Optional[IGitService], Optional[CapabilityHandlerOutput]]:
        if not workspace_id:
            return None, CapabilityHandlerOutput(
                success=False,
                output_text=f"{self.capability_name.upper()}_FAILED: Missing workspace_id.",
                errors=["Missing workspace_id."],
            )
        service = self.adapter.get_git_service(workspace_id)
        if not service:
            return None, CapabilityHandlerOutput(
                success=False,
                output_text=f"{self.capability_name.upper()}_FAILED: Workspace '{workspace_id}' not found or inactive.",
                errors=[f"Workspace '{workspace_id}' not found or inactive."],
            )
        return service, None


class GitStatusCapabilityHandler(BaseGitCapabilityHandler):
    """Approved Capability Execution Handler for repository status inspection."""
    capability_name = "git_status"
    required_params = ["workspace_id"]
    allowed_params = ["workspace_id"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res: GitResult = service.status()
        if not res.success:
            err_msg = res.error_message or "Git status query failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_STATUS_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        status_summary = f"Branch: {res.branch}, State: {res.status.value}, Changed files: {len(res.changed_files)}"
        return CapabilityHandlerOutput(
            success=True,
            output_text=status_summary,
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class GitBranchCapabilityHandler(BaseGitCapabilityHandler):
    """Approved Capability Execution Handler for branch listing, creation, and checkout."""
    capability_name = "git_branch"
    required_params = ["workspace_id"]
    allowed_params = ["workspace_id", "action", "branch_name", "base_branch"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        action = str(request.inputs.get("action", "list")).lower()
        branch_name = request.inputs.get("branch_name")
        base_branch = request.inputs.get("base_branch")

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        if action == "create":
            if not branch_name:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text="GIT_BRANCH_FAILED: Parameter 'branch_name' is required for create action.",
                    errors=["Missing 'branch_name' for branch creation."],
                )
            res = service.create_branch(branch_name=str(branch_name), base_branch=base_branch)

        elif action == "checkout":
            if not branch_name:
                return CapabilityHandlerOutput(
                    success=False,
                    output_text="GIT_BRANCH_FAILED: Parameter 'branch_name' is required for checkout action.",
                    errors=["Missing 'branch_name' for checkout."],
                )
            res = service.checkout_branch(branch_name=str(branch_name))

        elif action == "current":
            res = service.current_branch()

        else:  # default "list"
            res = service.list_branches()

        if not res.success:
            err_msg = res.error_message or "Git branch operation failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_BRANCH_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        if action == "list":
            out_text = f"Branches: {', '.join(res.branches)} (active: {res.branch})"
        elif action == "current":
            out_text = f"Current branch: {res.branch}"
        else:
            out_text = res.message or f"Branch operation '{action}' completed successfully."

        return CapabilityHandlerOutput(
            success=True,
            output_text=out_text,
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class GitDiffCapabilityHandler(BaseGitCapabilityHandler):
    """Approved Capability Execution Handler for repository diff inspection."""
    capability_name = "git_diff"
    required_params = ["workspace_id"]
    allowed_params = ["workspace_id", "paths"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        paths = request.inputs.get("paths")
        if isinstance(paths, str):
            paths = [paths]
        elif not isinstance(paths, list):
            paths = None

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res: GitResult = service.diff(paths=paths)
        if not res.success:
            err_msg = res.error_message or "Git diff computation failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_DIFF_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.diff or "",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class GitStageCapabilityHandler(BaseGitCapabilityHandler):
    """Approved Capability Execution Handler for staging explicit workspace files."""
    capability_name = "git_stage"
    required_params = ["workspace_id", "paths"]
    allowed_params = ["workspace_id", "paths"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        paths = request.inputs.get("paths", [])
        if isinstance(paths, str):
            paths = [paths]
        elif not isinstance(paths, list):
            paths = []

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res: GitResult = service.stage_files(paths=paths)
        if not res.success:
            err_msg = res.error_message or "Git staging failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_STAGE_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.message or f"Staged {len(res.staged_files)} file(s).",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class GitUnstageCapabilityHandler(BaseGitCapabilityHandler):
    """Approved Capability Execution Handler for unstaging explicit workspace files."""
    capability_name = "git_unstage"
    required_params = ["workspace_id", "paths"]
    allowed_params = ["workspace_id", "paths"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        paths = request.inputs.get("paths", [])
        if isinstance(paths, str):
            paths = [paths]
        elif not isinstance(paths, list):
            paths = []

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res: GitResult = service.unstage_files(paths=paths)
        if not res.success:
            err_msg = res.error_message or "Git unstaging failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_UNSTAGE_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.message or f"Unstaged {len(res.unstaged_files)} file(s).",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class GitCommitCapabilityHandler(BaseGitCapabilityHandler):
    """Approved Capability Execution Handler for creating Git commits."""
    capability_name = "git_commit"
    required_params = ["workspace_id"]
    allowed_params = ["workspace_id", "message", "commit_message"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        msg = request.inputs.get("message") or request.inputs.get("commit_message")
        if not msg:
            return CapabilityHandlerOutput(
                success=False,
                output_text="GIT_COMMIT_FAILED: Missing required parameter 'message'.",
                errors=["Missing required parameter 'message'."],
            )

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res: GitResult = service.commit(message=str(msg))
        if not res.success:
            err_msg = res.error_message or "Git commit failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_COMMIT_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.message or f"Commit created successfully ({res.commit_id}).",
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )


class GitLogCapabilityHandler(BaseGitCapabilityHandler):
    """Approved Capability Execution Handler for commit history log retrieval."""
    capability_name = "git_log"
    required_params = ["workspace_id"]
    allowed_params = ["workspace_id", "limit"]

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", ""))
        limit_val = request.inputs.get("limit", 10)
        try:
            limit = int(limit_val)
        except (ValueError, TypeError):
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_LOG_FAILED: Invalid limit parameter '{limit_val}'.",
                errors=[f"Invalid limit parameter '{limit_val}'."],
            )

        service, err_out = self._get_service(ws_id)
        if err_out:
            return err_out

        res: GitResult = service.log(limit=limit)
        if not res.success:
            err_msg = res.error_message or "Git log retrieval failed."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"GIT_LOG_FAILED: {err_msg}",
                facts=res.facts,
                errors=[err_msg],
                additional_evidence=res.evidence,
            )

        lines = [f"{e.commit_id[:8]} - {e.author}: {e.message}" for e in res.log_entries]
        out_text = f"Retrieved {len(lines)} commit(s):\n" + "\n".join(lines)
        return CapabilityHandlerOutput(
            success=True,
            output_text=out_text,
            facts=res.facts,
            errors=[],
            additional_evidence=res.evidence,
        )
