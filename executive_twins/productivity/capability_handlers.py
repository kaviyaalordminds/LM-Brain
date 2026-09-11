"""
Productivity Integration Capability Handlers.
Implements bounded capability handlers for artifact export and storage.
EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
All file operations delegate strictly to sandboxed IFileService.
"""

from typing import Any, Dict, List, Optional
import uuid

from executive_twins.execution.capability_execution_engine import (
    BaseCapabilityHandler,
    CapabilityHandlerOutput,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.productivity.dev_adapters import DevTestProductivityAdapter
from executive_twins.productivity.models import (
    ExportFormat,
    ExportRequest,
    StorageProvider,
    StorageRequest,
    SyncStatus,
    _validate_safe_relative_path,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import SpecialistMetadata


def _get_mime_type(fmt: ExportFormat) -> str:
    """Return appropriate MIME type for target export format."""
    if fmt == ExportFormat.MARKDOWN:
        return "text/markdown"
    if fmt == ExportFormat.HTML:
        return "text/html"
    if fmt == ExportFormat.CSV:
        return "text/csv"
    if fmt == ExportFormat.TSV:
        return "text/tab-separated-values"
    return "text/plain"


def _parse_provider(raw: Any) -> StorageProvider:
    if isinstance(raw, StorageProvider):
        return raw
    val = str(raw).upper().replace(" ", "_").replace("-", "_")
    if val in StorageProvider.__members__:
        return StorageProvider[val]
    for member in StorageProvider:
        if member.value == val or member.name == val:
            return member
    return StorageProvider.LOCAL


def _parse_export_format(raw: Any) -> ExportFormat:
    if isinstance(raw, ExportFormat):
        return raw
    val = str(raw).upper().replace(" ", "_").replace("-", "_")
    if val in ExportFormat.__members__:
        return ExportFormat[val]
    for member in ExportFormat:
        if member.value == val or member.name == val:
            return member
    return ExportFormat.ORIGINAL


class ProductivityArtifactExportCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for exporting workspace artifacts to target formats and logical providers.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "artifact_export"
    required_tool = "file_service"
    required_params = ["source_relative_path"]
    allowed_params = [
        "source_relative_path",
        "source_workspace",
        "destination_relative_path",
        "destination_workspace",
        "workspace_id",
        "provider",
        "requested_format",
        "format",
        "overwrite",
        "metadata",
        "tags",
    ]

    def __init__(
        self,
        file_adapter: Optional[DevFileServiceAdapter] = None,
        productivity_adapter: Optional[DevTestProductivityAdapter] = None,
    ) -> None:
        self.file_adapter = file_adapter
        self.productivity_adapter = productivity_adapter or DevTestProductivityAdapter()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "source_relative_path" not in inputs or not inputs["source_relative_path"]:
            return "Missing required parameter 'source_relative_path' for capability 'artifact_export'."

        try:
            _validate_safe_relative_path(str(inputs["source_relative_path"]))
            if inputs.get("destination_relative_path"):
                _validate_safe_relative_path(str(inputs["destination_relative_path"]))
        except ValueError as e:
            return f"Invalid path for 'artifact_export': {str(e)}"

        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        src_path = str(request.inputs.get("source_relative_path", ""))
        src_ws = str(request.inputs.get("workspace_id") or request.inputs.get("source_workspace", "default") or "default")
        dest_path = request.inputs.get("destination_relative_path")
        dest_ws = request.inputs.get("destination_workspace") or src_ws
        provider = _parse_provider(request.inputs.get("provider", StorageProvider.LOCAL))
        req_fmt = _parse_export_format(request.inputs.get("requested_format", request.inputs.get("format", ExportFormat.ORIGINAL)))
        overwrite = bool(request.inputs.get("overwrite", True))

        if self.file_adapter is None:
            return CapabilityHandlerOutput(
                success=False,
                output_text="EXECUTION_ERROR: FileService adapter is not available for artifact export.",
                errors=["No FileService adapter configured."],
            )

        file_service = self.file_adapter.get_file_service(src_ws)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"EXECUTION_ERROR: Workspace '{src_ws}' not found.",
                errors=[f"Workspace '{src_ws}' not found."],
            )

        export_req = ExportRequest(
            source_workspace=src_ws,
            source_relative_path=src_path,
            destination_workspace=dest_ws,
            destination_relative_path=dest_path,
            provider=provider,
            requested_format=req_fmt,
            overwrite=overwrite,
            metadata=request.inputs.get("metadata", {}),
            tags=request.inputs.get("tags", []),
        )

        result = self.productivity_adapter.export_artifact(export_req, file_service)

        if result.status != SyncStatus.SUCCESS or result.destination_artifact is None:
            err_msg = result.error_message or f"Export failed with status {result.status.value}."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"EXPORT_FAILED: {err_msg}",
                errors=[err_msg],
            )

        art_ev = ArtifactEvidence(
            evidence_id=f"ev-prod-exp-{request.delegation_id[:8]}",
            artifact_uri=result.destination_artifact,
            description=f"Exported artifact from '{result.source_artifact}' to '{result.destination_artifact}' in format '{result.format.value}'",
            mime_type=_get_mime_type(result.format),
            checksum_sha256=result.checksum_sha256,
        )

        verif_ev = VerificationEvidence(
            evidence_id=f"ev-prod-verif-{request.delegation_id[:8]}",
            verifier_id="productivity_exporter",
            verified_status="VERIFIED",
            description=f"Verified deterministic export of '{src_path}' to '{result.destination_artifact}' with checksum {result.checksum_sha256[:8] if result.checksum_sha256 else 'N/A'}.",
        )

        facts = [
            FactItem(
                statement=f"Exported workspace artifact '{src_path}' to '{result.destination_artifact}' in '{result.format.value}' format via provider '{result.provider.value}'.",
                state=FactState.FACT,
                source="productivity_integration",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully exported artifact to '{result.destination_artifact}' in format '{result.format.value}'.",
            facts=facts,
            artifacts=[result.destination_artifact],
            errors=[],
            additional_evidence=[art_ev, verif_ev],
        )


class ProductivityArtifactStorageCapabilityHandler(BaseCapabilityHandler):
    """
    Approved Capability Handler for storing and moving workspace artifacts across logical storage locations.
    EXECUTION SAFETY: Registered within SpecialistExecutionEngine boundary.
    All file operations delegate to sandboxed FileService.
    """

    capability_name = "productivity_storage"
    required_tool = "file_service"
    required_params = ["source_relative_path"]
    allowed_params = [
        "source_relative_path",
        "source_workspace",
        "destination_relative_path",
        "destination_workspace",
        "workspace_id",
        "provider",
        "overwrite",
        "metadata",
        "tags",
    ]

    def __init__(
        self,
        file_adapter: Optional[DevFileServiceAdapter] = None,
        productivity_adapter: Optional[DevTestProductivityAdapter] = None,
    ) -> None:
        self.file_adapter = file_adapter
        self.productivity_adapter = productivity_adapter or DevTestProductivityAdapter()

    def validate_parameters(self, inputs: Dict[str, Any]) -> Optional[str]:
        if "source_relative_path" not in inputs or not inputs["source_relative_path"]:
            return "Missing required parameter 'source_relative_path' for capability 'productivity_storage'."

        try:
            _validate_safe_relative_path(str(inputs["source_relative_path"]))
            if inputs.get("destination_relative_path"):
                _validate_safe_relative_path(str(inputs["destination_relative_path"]))
        except ValueError as e:
            return f"Invalid path for 'productivity_storage': {str(e)}"

        return super().validate_parameters(inputs)

    def execute(
        self, request: DelegationRequest, specialist: SpecialistMetadata
    ) -> CapabilityHandlerOutput:
        src_path = str(request.inputs.get("source_relative_path", ""))
        src_ws = str(request.inputs.get("workspace_id") or request.inputs.get("source_workspace", "default") or "default")
        dest_path = request.inputs.get("destination_relative_path")
        dest_ws = request.inputs.get("destination_workspace") or src_ws
        provider = _parse_provider(request.inputs.get("provider", StorageProvider.LOCAL))
        overwrite = bool(request.inputs.get("overwrite", True))

        if self.file_adapter is None:
            return CapabilityHandlerOutput(
                success=False,
                output_text="EXECUTION_ERROR: FileService adapter is not available for artifact storage.",
                errors=["No FileService adapter configured."],
            )

        file_service = self.file_adapter.get_file_service(src_ws)
        if not file_service:
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"EXECUTION_ERROR: Workspace '{src_ws}' not found.",
                errors=[f"Workspace '{src_ws}' not found."],
            )

        storage_req = StorageRequest(
            source_workspace=src_ws,
            source_relative_path=src_path,
            destination_workspace=dest_ws,
            destination_relative_path=dest_path,
            provider=provider,
            overwrite=overwrite,
            metadata=request.inputs.get("metadata", {}),
            tags=request.inputs.get("tags", []),
        )

        result = self.productivity_adapter.store_artifact(storage_req, file_service)

        if result.status != SyncStatus.SUCCESS or result.destination_artifact is None:
            err_msg = result.error_message or f"Storage failed with status {result.status.value}."
            return CapabilityHandlerOutput(
                success=False,
                output_text=f"STORAGE_FAILED: {err_msg}",
                errors=[err_msg],
            )

        art_ev = ArtifactEvidence(
            evidence_id=f"ev-prod-store-{request.delegation_id[:8]}",
            artifact_uri=result.destination_artifact,
            description=f"Stored artifact from '{result.source_artifact}' into '{result.destination_artifact}'",
            checksum_sha256=result.checksum_sha256,
        )

        verif_ev = VerificationEvidence(
            evidence_id=f"ev-prod-store-verif-{request.delegation_id[:8]}",
            verifier_id="productivity_storage",
            verified_status="VERIFIED",
            description=f"Verified storage placement of '{src_path}' to '{result.destination_artifact}' with checksum {result.checksum_sha256[:8] if result.checksum_sha256 else 'N/A'}.",
        )

        facts = [
            FactItem(
                statement=f"Stored workspace artifact '{src_path}' to destination '{result.destination_artifact}' via provider '{result.provider.value}'.",
                state=FactState.FACT,
                source="productivity_integration",
            )
        ]

        return CapabilityHandlerOutput(
            success=True,
            output_text=f"Successfully stored artifact at '{result.destination_artifact}'.",
            facts=facts,
            artifacts=[result.destination_artifact],
            errors=[],
            additional_evidence=[art_ev, verif_ev],
        )
