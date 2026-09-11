"""
DEV/TEST adapters and registered Files API capability execution handlers.
Used for local development and testing without production cloud containers.
"""

from typing import Any, Dict, Optional

from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.files.file_service import FileService
from executive_twins.files.interfaces import IFileService
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import SpecialistMetadata
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


class DevFileServiceAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Manages FileService instances for workspaces.
    THIS IS NOT THE PRODUCTION SANDBOX CONTAINER INTEGRATION.
    """

    def __init__(self, workspace_adapter: DevTestWorkspaceAdapter) -> None:
        self.workspace_adapter = workspace_adapter
        self._active_file_services: Dict[str, IFileService] = {}

    def get_file_service(self, workspace_id: str) -> Optional[IFileService]:
        """Get or create a FileService instance for a workspace."""
        if not workspace_id:
            workspace_id = "default"
        if workspace_id in self._active_file_services:
            return self._active_file_services[workspace_id]

        workspace = self.workspace_adapter.get_workspace(workspace_id)
        if not workspace or not workspace.workspace_exists():
            if workspace and not workspace.workspace_exists():
                workspace.create_workspace()
            elif not workspace:
                workspace = self.workspace_adapter.create_workspace(workspace_id)

        file_service = FileService(workspace=workspace)
        self._active_file_services[workspace_id] = file_service
        return file_service


class FileCreateCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Execution Handler for file creation operations.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    Executes bounded workspace file creation.
    """

    capability_name = "file_create"
    required_tool = "file_service"
    required_params = ["workspace_id", "relative_path", "content"]
    allowed_params = [
        "workspace_id",
        "relative_path",
        "content",
        "overwrite",
        "path",
        "code",
        "target_file",
    ]

    def __init__(self, file_adapter: DevFileServiceAdapter) -> None:
        self.file_adapter = file_adapter

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "workspace_id" not in inputs or not inputs["workspace_id"]:
            inputs["workspace_id"] = "default"
        if "relative_path" not in inputs and "path" in inputs:
            inputs["relative_path"] = inputs["path"]
        if "relative_path" not in inputs and "target_file" in inputs:
            inputs["relative_path"] = inputs["target_file"]
        if "content" not in inputs and "code" in inputs:
            inputs["content"] = inputs["code"]
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        rel_path = str(
            request.inputs.get(
                "relative_path",
                request.inputs.get("path", request.inputs.get("target_file", "")),
            )
        )
        content = str(request.inputs.get("content", request.inputs.get("code", "")))
        overwrite = bool(request.inputs.get("overwrite", True))

        file_service = self.file_adapter.get_file_service(ws_id)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"CREATE_FAILED: File service for workspace '{ws_id}' not found or inactive.",
                errors=[f"Workspace '{ws_id}' not found or inactive."],
            )

        res = file_service.create_file(rel_path, content, overwrite=overwrite)
        if not res.success:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"CREATE_FAILED: {res.error_message}",
                errors=[res.error_message or "Create operation failed."],
            )

        artifacts = [res.artifact.artifact_uri] if res.artifact else []
        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully created file '{res.relative_path}' in workspace '{ws_id}'.",
            facts=res.facts,
            artifacts=artifacts,
            additional_evidence=res.evidence,
        )


class FileReadCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Execution Handler for file read operations.
    """

    capability_name = "file_read"
    required_tool = "file_service"
    required_params = ["workspace_id", "relative_path"]
    allowed_params = ["workspace_id", "relative_path", "path", "target_file"]

    def __init__(self, file_adapter: DevFileServiceAdapter) -> None:
        self.file_adapter = file_adapter

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "workspace_id" not in inputs or not inputs["workspace_id"]:
            inputs["workspace_id"] = "default"
        if "relative_path" not in inputs and "path" in inputs:
            inputs["relative_path"] = inputs["path"]
        if "relative_path" not in inputs and "target_file" in inputs:
            inputs["relative_path"] = inputs["target_file"]
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        rel_path = str(
            request.inputs.get(
                "relative_path",
                request.inputs.get("path", request.inputs.get("target_file", "")),
            )
        )

        file_service = self.file_adapter.get_file_service(ws_id)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"READ_FAILED: File service for workspace '{ws_id}' not found or inactive.",
                errors=[f"Workspace '{ws_id}' not found or inactive."],
            )

        res = file_service.read_file(rel_path)
        if not res.success:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"READ_FAILED: {res.error_message}",
                errors=[res.error_message or "Read operation failed."],
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=res.content or "",
            facts=res.facts,
        )


class FileUpdateCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Execution Handler for file update operations.
    """

    capability_name = "file_update"
    required_tool = "file_service"
    required_params = ["workspace_id", "relative_path", "content"]
    allowed_params = [
        "workspace_id",
        "relative_path",
        "content",
        "path",
        "target_file",
        "code",
    ]

    def __init__(self, file_adapter: DevFileServiceAdapter) -> None:
        self.file_adapter = file_adapter

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "workspace_id" not in inputs or not inputs["workspace_id"]:
            inputs["workspace_id"] = "default"
        if "relative_path" not in inputs and "path" in inputs:
            inputs["relative_path"] = inputs["path"]
        if "relative_path" not in inputs and "target_file" in inputs:
            inputs["relative_path"] = inputs["target_file"]
        if "content" not in inputs and "code" in inputs:
            inputs["content"] = inputs["code"]
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        rel_path = str(
            request.inputs.get(
                "relative_path",
                request.inputs.get("path", request.inputs.get("target_file", "")),
            )
        )
        content = str(request.inputs.get("content", request.inputs.get("code", "")))

        file_service = self.file_adapter.get_file_service(ws_id)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"UPDATE_FAILED: File service for workspace '{ws_id}' not found or inactive.",
                errors=[f"Workspace '{ws_id}' not found or inactive."],
            )

        res = file_service.update_file(rel_path, content)
        if not res.success:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"UPDATE_FAILED: {res.error_message}",
                errors=[res.error_message or "Update operation failed."],
            )

        artifacts = [res.artifact.artifact_uri] if res.artifact else []
        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully updated file '{res.relative_path}' in workspace '{ws_id}'.",
            facts=res.facts,
            artifacts=artifacts,
            additional_evidence=res.evidence,
        )


class FileDeleteCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Execution Handler for file deletion operations.
    """

    capability_name = "file_delete"
    required_tool = "file_service"
    required_params = ["workspace_id", "relative_path"]
    allowed_params = ["workspace_id", "relative_path", "path", "target_file"]

    def __init__(self, file_adapter: DevFileServiceAdapter) -> None:
        self.file_adapter = file_adapter

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "workspace_id" not in inputs or not inputs["workspace_id"]:
            inputs["workspace_id"] = "default"
        if "relative_path" not in inputs and "path" in inputs:
            inputs["relative_path"] = inputs["path"]
        if "relative_path" not in inputs and "target_file" in inputs:
            inputs["relative_path"] = inputs["target_file"]
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        rel_path = str(
            request.inputs.get(
                "relative_path",
                request.inputs.get("path", request.inputs.get("target_file", "")),
            )
        )

        file_service = self.file_adapter.get_file_service(ws_id)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DELETE_FAILED: File service for workspace '{ws_id}' not found or inactive.",
                errors=[f"Workspace '{ws_id}' not found or inactive."],
            )

        res = file_service.delete_file(rel_path)
        if not res.success:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"DELETE_FAILED: {res.error_message}",
                errors=[res.error_message or "Delete operation failed."],
            )

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully deleted file '{res.relative_path}' from workspace '{ws_id}'.",
            facts=res.facts,
        )


class FileListCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Execution Handler for file listing operations.
    """

    capability_name = "file_list"
    required_tool = "file_service"
    required_params = ["workspace_id"]
    allowed_params = ["workspace_id", "relative_path", "path"]

    def __init__(self, file_adapter: DevFileServiceAdapter) -> None:
        self.file_adapter = file_adapter

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "workspace_id" not in inputs or not inputs["workspace_id"]:
            inputs["workspace_id"] = "default"
        if "relative_path" not in inputs and "path" in inputs:
            inputs["relative_path"] = inputs["path"]
        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        ws_id = str(request.inputs.get("workspace_id", "default") or "default")
        rel_path = str(request.inputs.get("relative_path", request.inputs.get("path", "")))
        if rel_path == ".":
            rel_path = ""

        file_service = self.file_adapter.get_file_service(ws_id)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"LIST_FAILED: File service for workspace '{ws_id}' not found or inactive.",
                errors=[f"Workspace '{ws_id}' not found or inactive."],
            )

        res = file_service.list_files(rel_path)
        if not res.success:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"LIST_FAILED: {res.error_message}",
                errors=[res.error_message or "List operation failed."],
            )

        file_names = [f.relative_path for f in res.files]
        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Listed {len(file_names)} items: {', '.join(file_names) if file_names else '(empty workspace)'}",
            facts=res.facts,
        )
