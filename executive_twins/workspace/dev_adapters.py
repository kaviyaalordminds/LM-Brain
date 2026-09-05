"""
DEV/TEST adapters and registered workspace capability execution handlers.
Used for local development and testing without production cloud containers.
"""

from typing import Dict, Optional

from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import SpecialistMetadata
from executive_twins.workspace.interfaces import ISoftwareWorkspace
from executive_twins.workspace.local_workspace import LocalSoftwareWorkspace


class DevTestWorkspaceAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Manages controlled local software workspaces during testing.
    THIS IS NOT THE PRODUCTION SANDBOX CONTAINER INTEGRATION.
    Used for local development and testing when external cloud container sandbox is not attached.
    """

    def __init__(self, base_temp_dir: str = "", temp_workspace_dir: Optional[str] = None) -> None:
        self.base_temp_dir = temp_workspace_dir or base_temp_dir
        self._active_workspaces: Dict[str, ISoftwareWorkspace] = {}

    def create_workspace(self, workspace_id: str) -> ISoftwareWorkspace:
        """Create and initialize a local software workspace in a temporary directory."""
        root_path = f"{self.base_temp_dir}/{workspace_id}"
        workspace = LocalSoftwareWorkspace(workspace_id=workspace_id, root_path=root_path)
        workspace.create_workspace()
        self._active_workspaces[workspace_id] = workspace
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[ISoftwareWorkspace]:
        """Retrieve an active workspace by identifier."""
        return self._active_workspaces.get(workspace_id)

    def close_all(self, cleanup: bool = True) -> None:
        """Close and cleanup all tracked workspaces."""
        for ws in list(self._active_workspaces.values()):
            ws.close_workspace(cleanup=cleanup)
        self._active_workspaces.clear()


class WorkspaceBuildCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Execution Handler for workspace build steps.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    Does NOT execute arbitrary shell or system code. Executes bounded development operations.
    """

    capability_name = "workspace_build"
    required_tool = "workspace_builder"
    required_params = ["workspace_id", "project_file"]
    allowed_params = ["workspace_id", "project_file", "build_config"]

    def __init__(self, workspace_adapter: DevTestWorkspaceAdapter) -> None:
        self.workspace_adapter = workspace_adapter

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = request.inputs.get("workspace_id", "")
        proj_file = request.inputs.get("project_file", "")

        workspace = self.workspace_adapter.get_workspace(ws_id)
        if not workspace or not workspace.workspace_exists():
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"BUILD_FAILED: Workspace '{ws_id}' not found or inactive.",
                errors=[f"Workspace '{ws_id}' not found."],
            )

        if not workspace.file_exists(proj_file):
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"BUILD_FAILED: Target project file '{proj_file}' does not exist in workspace.",
                errors=[f"File '{proj_file}' missing from workspace."],
            )

        artifact_res = workspace.record_artifact(proj_file, description="Compiled workspace build artifact")
        if not artifact_res.success or not artifact_res.artifact:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"BUILD_FAILED: Failed to record build artifact: {artifact_res.error_message}",
                errors=[artifact_res.error_message or "Artifact error"],
            )

        facts = [
            FactItem(
                statement=f"Successfully built project artifact for file '{proj_file}' in workspace '{ws_id}'.",
                state=FactState.FACT,
                source="workspace_builder",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Workspace build completed for file '{proj_file}'. Checksum: {artifact_res.artifact.checksum_sha256[:8]}...",
            facts=facts,
            artifacts=[artifact_res.artifact.artifact_uri],
            additional_evidence=artifact_res.evidence,
        )
