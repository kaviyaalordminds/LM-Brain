"""
Controlled Files API implementation.
Acts as a thin service layer over ISoftwareWorkspace abstraction.
Enforces workspace security boundaries and typed operational results.
"""

from pathlib import Path
from typing import List, Optional

from executive_twins.files.interfaces import IFileService
from executive_twins.files.models import (
    FileMetadata,
    FileOperationResult,
    FileOperationType,
)
from executive_twins.workspace.interfaces import ISoftwareWorkspace
from executive_twins.workspace.models import WorkspaceOperationType


class FileService(IFileService):
    """
    Controlled Files API Service.
    Thin wrapper over ISoftwareWorkspace enforcing typed results and security isolation.
    Does NOT provide direct host filesystem access or arbitrary execution capabilities.
    """

    def __init__(self, workspace: ISoftwareWorkspace) -> None:
        self._workspace = workspace

    @property
    def workspace(self) -> ISoftwareWorkspace:
        return self._workspace

    def _build_metadata(
        self, relative_path: str, size_bytes: int, is_dir: bool, mtime, sha256: Optional[str]
    ) -> FileMetadata:
        file_name = Path(relative_path).name or relative_path
        return FileMetadata(
            relative_path=relative_path,
            file_name=file_name,
            size_bytes=size_bytes,
            is_directory=is_dir,
            modified_at=mtime,
            checksum_sha256=sha256,
            workspace_id=self._workspace.workspace_id,
        )

    def create_file(
        self, relative_path: str, content: str, overwrite: bool = False
    ) -> FileOperationResult:
        if not relative_path or not relative_path.strip():
            return FileOperationResult(
                success=False,
                operation=FileOperationType.CREATE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message="INVALID_PATH: Path cannot be empty.",
                error_type="INVALID_PATH",
            )

        if not overwrite and self._workspace.file_exists(relative_path):
            return FileOperationResult(
                success=False,
                operation=FileOperationType.CREATE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=f"FILE_ALREADY_EXISTS: File '{relative_path}' already exists and overwrite is False.",
                error_type="FILE_ALREADY_EXISTS",
            )

        res = self._workspace.write_file(relative_path, content, overwrite=overwrite)
        if not res.success:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.CREATE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=res.error_message,
                error_type=res.error_type or "OPERATION_FAILED",
            )

        meta_res = self.get_file_metadata(res.relative_path or relative_path)
        meta = meta_res.metadata if meta_res.success else None

        return FileOperationResult(
            success=True,
            operation=FileOperationType.CREATE,
            workspace_id=self._workspace.workspace_id,
            relative_path=res.relative_path or relative_path,
            metadata=meta,
            artifact=res.artifact,
            facts=res.facts,
            evidence=res.evidence,
        )

    def read_file(self, relative_path: str) -> FileOperationResult:
        if not relative_path or not relative_path.strip():
            return FileOperationResult(
                success=False,
                operation=FileOperationType.READ,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message="INVALID_PATH: Path cannot be empty.",
                error_type="INVALID_PATH",
            )

        # Check if target is a directory before attempting read
        meta_res = self.get_file_metadata(relative_path)
        if meta_res.success and meta_res.metadata and meta_res.metadata.is_directory:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.READ,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=f"IS_DIRECTORY: Cannot read directory '{relative_path}' as a file.",
                error_type="IS_DIRECTORY",
            )

        res = self._workspace.read_file(relative_path)
        if not res.success:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.READ,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=res.error_message,
                error_type=res.error_type or "OPERATION_FAILED",
            )

        return FileOperationResult(
            success=True,
            operation=FileOperationType.READ,
            workspace_id=self._workspace.workspace_id,
            relative_path=res.relative_path or relative_path,
            content=res.content,
            facts=res.facts,
        )

    def update_file(self, relative_path: str, content: str) -> FileOperationResult:
        if not relative_path or not relative_path.strip():
            return FileOperationResult(
                success=False,
                operation=FileOperationType.UPDATE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message="INVALID_PATH: Path cannot be empty.",
                error_type="INVALID_PATH",
            )

        # File must exist to be updated
        if not self._workspace.file_exists(relative_path):
            return FileOperationResult(
                success=False,
                operation=FileOperationType.UPDATE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=f"FILE_NOT_FOUND: File '{relative_path}' does not exist in workspace.",
                error_type="FILE_NOT_FOUND",
            )

        meta_res = self.get_file_metadata(relative_path)
        if meta_res.success and meta_res.metadata and meta_res.metadata.is_directory:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.UPDATE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=f"IS_DIRECTORY: Cannot update directory '{relative_path}'.",
                error_type="IS_DIRECTORY",
            )

        res = self._workspace.write_file(relative_path, content, overwrite=True)
        if not res.success:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.UPDATE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=res.error_message,
                error_type=res.error_type or "OPERATION_FAILED",
            )

        updated_meta_res = self.get_file_metadata(res.relative_path or relative_path)
        meta = updated_meta_res.metadata if updated_meta_res.success else None

        return FileOperationResult(
            success=True,
            operation=FileOperationType.UPDATE,
            workspace_id=self._workspace.workspace_id,
            relative_path=res.relative_path or relative_path,
            metadata=meta,
            artifact=res.artifact,
            facts=res.facts,
            evidence=res.evidence,
        )

    def delete_file(self, relative_path: str) -> FileOperationResult:
        if not relative_path or not relative_path.strip():
            return FileOperationResult(
                success=False,
                operation=FileOperationType.DELETE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message="INVALID_PATH: Path cannot be empty.",
                error_type="INVALID_PATH",
            )

        res = self._workspace.delete_file(relative_path)
        if not res.success:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.DELETE,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=res.error_message,
                error_type=res.error_type or "OPERATION_FAILED",
            )

        return FileOperationResult(
            success=True,
            operation=FileOperationType.DELETE,
            workspace_id=self._workspace.workspace_id,
            relative_path=res.relative_path or relative_path,
            facts=res.facts,
        )

    def list_files(self, relative_path: str = "") -> FileOperationResult:
        target_path = relative_path if relative_path is not None else ""
        res = self._workspace.list_files(target_path or ".")
        if not res.success:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.LIST,
                workspace_id=self._workspace.workspace_id,
                relative_path=target_path,
                error_message=res.error_message,
                error_type=res.error_type or "OPERATION_FAILED",
            )

        file_metas: List[FileMetadata] = []
        for info in res.files:
            file_metas.append(
                self._build_metadata(
                    relative_path=info.relative_path,
                    size_bytes=info.size_bytes,
                    is_dir=info.is_directory,
                    mtime=info.modified_at,
                    sha256=info.checksum_sha256,
                )
            )

        return FileOperationResult(
            success=True,
            operation=FileOperationType.LIST,
            workspace_id=self._workspace.workspace_id,
            relative_path=res.relative_path or target_path,
            files=file_metas,
            facts=res.facts,
        )

    def file_exists(self, relative_path: str) -> FileOperationResult:
        if not relative_path or not relative_path.strip():
            return FileOperationResult(
                success=False,
                operation=FileOperationType.EXISTS,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                exists=False,
                error_message="INVALID_PATH: Path cannot be empty.",
                error_type="INVALID_PATH",
            )

        # Validate security via workspace list/read check
        # First attempt list_files to see if path validation raises a security error
        list_res = self._workspace.list_files(relative_path)
        if not list_res.success and list_res.error_type == "SECURITY_PATH_TRAVERSAL":
            return FileOperationResult(
                success=False,
                operation=FileOperationType.EXISTS,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                exists=False,
                error_message=list_res.error_message,
                error_type="SECURITY_PATH_TRAVERSAL",
            )

        exists = self._workspace.file_exists(relative_path)
        return FileOperationResult(
            success=True,
            operation=FileOperationType.EXISTS,
            workspace_id=self._workspace.workspace_id,
            relative_path=relative_path,
            exists=exists,
        )

    def get_file_metadata(self, relative_path: str) -> FileOperationResult:
        if not relative_path or not relative_path.strip():
            return FileOperationResult(
                success=False,
                operation=FileOperationType.METADATA,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message="INVALID_PATH: Path cannot be empty.",
                error_type="INVALID_PATH",
            )

        res = self._workspace.list_files(relative_path)
        if not res.success:
            err_type = "FILE_NOT_FOUND" if res.error_type == "DIRECTORY_NOT_FOUND" else (res.error_type or "OPERATION_FAILED")
            err_msg = f"FILE_NOT_FOUND: File '{relative_path}' does not exist in workspace." if res.error_type == "DIRECTORY_NOT_FOUND" else res.error_message
            return FileOperationResult(
                success=False,
                operation=FileOperationType.METADATA,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=err_msg,
                error_type=err_type,
            )

        # Look for exact relative_path match or first match in list
        target_info = None
        target_rel_norm = relative_path.replace("\\", "/").strip("./")
        for info in res.files:
            info_rel_norm = info.relative_path.replace("\\", "/").strip("./")
            if info_rel_norm == target_rel_norm:
                target_info = info
                break

        if not target_info and res.files:
            target_info = res.files[0]

        if not target_info:
            return FileOperationResult(
                success=False,
                operation=FileOperationType.METADATA,
                workspace_id=self._workspace.workspace_id,
                relative_path=relative_path,
                error_message=f"FILE_NOT_FOUND: File metadata for '{relative_path}' could not be retrieved.",
                error_type="FILE_NOT_FOUND",
            )

        meta = self._build_metadata(
            relative_path=target_info.relative_path,
            size_bytes=target_info.size_bytes,
            is_dir=target_info.is_directory,
            mtime=target_info.modified_at,
            sha256=target_info.checksum_sha256,
        )

        return FileOperationResult(
            success=True,
            operation=FileOperationType.METADATA,
            workspace_id=self._workspace.workspace_id,
            relative_path=target_info.relative_path,
            metadata=meta,
            facts=res.facts,
        )
