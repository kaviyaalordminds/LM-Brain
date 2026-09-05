"""
Local deterministic implementation of Software Development Workspace.
Enforces strict path isolation and sandbox security boundaries.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePath
import shutil
from typing import List, Optional, Union
import uuid

from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.evidence import ArtifactEvidence, EvidenceCategory
from executive_twins.workspace.interfaces import ISoftwareWorkspace
from executive_twins.workspace.models import (
    WorkspaceArtifact,
    WorkspaceFileInfo,
    WorkspaceMetadata,
    WorkspaceOperationResult,
    WorkspaceOperationType,
)


class PathSecurityException(Exception):
    """Exception raised when path traversal or outside-workspace access is attempted."""
    pass


class LocalSoftwareWorkspace(ISoftwareWorkspace):
    """
    Deterministic Local Implementation of Software Development Workspace.
    Enforces strict path isolation against workspace root and rejects traversal,
    outside absolute paths, and symlinks escaping the workspace root.
    """

    def __init__(self, workspace_id: str, root_path: Union[str, Path]) -> None:
        self._workspace_id = workspace_id
        self._raw_root_path = str(root_path)
        self._root_path = Path(root_path).resolve()
        self._is_active = True
        self._metadata = WorkspaceMetadata(
            workspace_id=workspace_id,
            root_path=str(self._root_path),
            is_active=True,
        )

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    @property
    def root_path(self) -> str:
        return str(self._root_path)

    @property
    def is_active(self) -> bool:
        return self._is_active

    def _is_subpath(self, target: Path, base: Path) -> bool:
        """Check if target path is equal to or inside base path."""
        try:
            target.relative_to(base)
            return True
        except ValueError:
            return False

    def _validate_and_resolve_path(self, relative_path: str) -> Path:
        """
        Enforce strict path isolation boundaries.
        Path must resolve under canonical workspace root.
        Rejects traversal (..), outside absolute paths, and escaping symlinks.
        """
        if not relative_path or not relative_path.strip():
            raise PathSecurityException("PATH_TRAVERSAL_REJECTED: Path cannot be empty.")

        path_obj = Path(relative_path)

        # 1. Reject explicit parent traversal components in raw path
        for part in path_obj.parts:
            if part == "..":
                raise PathSecurityException(
                    f"PATH_TRAVERSAL_REJECTED: Explicit parent traversal '..' detected in '{relative_path}'."
                )

        # 2. Handle absolute vs relative paths
        if path_obj.is_absolute():
            try:
                resolved_path = path_obj.resolve()
            except Exception as e:
                raise PathSecurityException(f"PATH_TRAVERSAL_REJECTED: Invalid path '{relative_path}': {e}")

            if not self._is_subpath(resolved_path, self._root_path):
                raise PathSecurityException(
                    f"PATH_OUTSIDE_WORKSPACE_REJECTED: Absolute path '{relative_path}' resolves outside workspace root."
                )
            target_path = resolved_path
        else:
            full_path = self._root_path / path_obj
            if full_path.exists() or full_path.is_symlink():
                try:
                    resolved_path = full_path.resolve()
                except Exception as e:
                    raise PathSecurityException(f"PATH_TRAVERSAL_REJECTED: Invalid path '{relative_path}': {e}")
            else:
                parent = full_path.parent
                try:
                    resolved_parent = parent.resolve()
                except Exception as e:
                    raise PathSecurityException(
                        f"PATH_TRAVERSAL_REJECTED: Invalid parent path for '{relative_path}': {e}"
                    )
                resolved_path = resolved_parent / full_path.name

            if not self._is_subpath(resolved_path, self._root_path):
                raise PathSecurityException(
                    f"PATH_OUTSIDE_WORKSPACE_REJECTED: Path '{relative_path}' resolves outside workspace root."
                )
            target_path = resolved_path

        return target_path

    def _get_relative_path_string(self, target: Path) -> str:
        """Return normalized relative path string from workspace root."""
        if target == self._root_path:
            return "."
        return str(target.relative_to(self._root_path)).replace("\\", "/")

    def create_workspace(self) -> WorkspaceOperationResult:
        if not self._is_active:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.CREATE_WORKSPACE,
                workspace_id=self._workspace_id,
                error_message="WORKSPACE_CLOSED: Cannot initialize a closed workspace.",
                error_type="WORKSPACE_CLOSED",
            )
        try:
            self._root_path.mkdir(parents=True, exist_ok=True)
            fact = FactItem(
                statement=f"Initialized workspace '{self._workspace_id}' at '{self._root_path}'.",
                state=FactState.FACT,
                source="local_workspace",
            )
            return WorkspaceOperationResult(
                success=True,
                operation=WorkspaceOperationType.CREATE_WORKSPACE,
                workspace_id=self._workspace_id,
                facts=[fact],
            )
        except Exception as e:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.CREATE_WORKSPACE,
                workspace_id=self._workspace_id,
                error_message=f"WORKSPACE_CREATION_FAILED: {str(e)}",
                error_type="CREATION_FAILED",
            )

    def workspace_exists(self) -> bool:
        return self._is_active and self._root_path.exists() and self._root_path.is_dir()

    def read_file(self, relative_path: str) -> WorkspaceOperationResult:
        if not self.workspace_exists():
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.READ_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message="WORKSPACE_NOT_FOUND: Workspace directory does not exist or is inactive.",
                error_type="WORKSPACE_NOT_FOUND",
            )
        try:
            target_path = self._validate_and_resolve_path(relative_path)
        except PathSecurityException as se:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.READ_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=str(se),
                error_type="SECURITY_PATH_TRAVERSAL",
            )

        if not target_path.exists() or not target_path.is_file():
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.READ_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"FILE_NOT_FOUND: File '{relative_path}' does not exist in workspace.",
                error_type="FILE_NOT_FOUND",
            )

        try:
            content = target_path.read_text(encoding="utf-8")
            rel_str = self._get_relative_path_string(target_path)
            fact = FactItem(
                statement=f"Read workspace file '{rel_str}'.",
                state=FactState.FACT,
                source="local_workspace",
            )
            return WorkspaceOperationResult(
                success=True,
                operation=WorkspaceOperationType.READ_FILE,
                workspace_id=self._workspace_id,
                relative_path=rel_str,
                content=content,
                facts=[fact],
            )
        except Exception as e:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.READ_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"READ_ERROR: Failed to read file: {str(e)}",
                error_type="READ_ERROR",
            )

    def write_file(
        self, relative_path: str, content: str, overwrite: bool = True
    ) -> WorkspaceOperationResult:
        if not self.workspace_exists():
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.WRITE_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message="WORKSPACE_NOT_FOUND: Workspace directory does not exist or is inactive.",
                error_type="WORKSPACE_NOT_FOUND",
            )
        try:
            target_path = self._validate_and_resolve_path(relative_path)
        except PathSecurityException as se:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.WRITE_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=str(se),
                error_type="SECURITY_PATH_TRAVERSAL",
            )

        if target_path.exists() and not overwrite:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.WRITE_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"FILE_ALREADY_EXISTS: File '{relative_path}' exists and overwrite=False.",
                error_type="FILE_ALREADY_EXISTS",
            )

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if not self._is_subpath(target_path.parent.resolve(), self._root_path):
                raise PathSecurityException("PATH_OUTSIDE_WORKSPACE_REJECTED: Parent directory resolves outside workspace.")

            target_path.write_text(content, encoding="utf-8")
            rel_str = self._get_relative_path_string(target_path)

            sha256_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            size_bytes = len(content.encode("utf-8"))

            artifact_id = f"art-{uuid.uuid4().hex[:8]}"
            artifact_uri = f"workspace://{self._workspace_id}/{rel_str}"

            artifact = WorkspaceArtifact(
                artifact_id=artifact_id,
                workspace_id=self._workspace_id,
                relative_path=rel_str,
                artifact_uri=artifact_uri,
                checksum_sha256=sha256_hash,
                size_bytes=size_bytes,
                description=f"Project file written at '{rel_str}'",
            )
            self._metadata.recorded_artifacts.append(artifact)

            evidence = ArtifactEvidence(
                evidence_id=f"ev-{artifact_id}",
                category=EvidenceCategory.ARTIFACT,
                artifact_uri=artifact_uri,
                checksum_sha256=sha256_hash,
                description=f"File write recorded for '{rel_str}'",
            )

            fact = FactItem(
                statement=f"Wrote {size_bytes} bytes to workspace file '{rel_str}' (SHA256: {sha256_hash[:8]}...).",
                state=FactState.FACT,
                source="local_workspace",
            )

            return WorkspaceOperationResult(
                success=True,
                operation=WorkspaceOperationType.WRITE_FILE,
                workspace_id=self._workspace_id,
                relative_path=rel_str,
                artifact=artifact,
                facts=[fact],
                evidence=[evidence],
            )
        except Exception as e:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.WRITE_FILE,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"WRITE_ERROR: Failed to write file: {str(e)}",
                error_type="WRITE_ERROR",
            )

    def list_files(self, relative_path: str = ".") -> WorkspaceOperationResult:
        if not self.workspace_exists():
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.LIST_FILES,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message="WORKSPACE_NOT_FOUND: Workspace directory does not exist or is inactive.",
                error_type="WORKSPACE_NOT_FOUND",
            )
        try:
            target_path = self._validate_and_resolve_path(relative_path)
        except PathSecurityException as se:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.LIST_FILES,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=str(se),
                error_type="SECURITY_PATH_TRAVERSAL",
            )

        if not target_path.exists():
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.LIST_FILES,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"DIRECTORY_NOT_FOUND: Path '{relative_path}' does not exist.",
                error_type="DIRECTORY_NOT_FOUND",
            )

        try:
            files_info: List[WorkspaceFileInfo] = []
            if target_path.is_file():
                entries = [target_path]
            else:
                entries = list(target_path.rglob("*"))

            for entry in entries:
                try:
                    resolved_entry = entry.resolve()
                    if not self._is_subpath(resolved_entry, self._root_path):
                        continue
                except Exception:
                    continue

                rel_str = self._get_relative_path_string(resolved_entry)
                is_dir = resolved_entry.is_dir()
                size_bytes = 0
                sha256 = None
                mtime = datetime.fromtimestamp(resolved_entry.stat().st_mtime, tz=timezone.utc)

                if not is_dir:
                    try:
                        content = resolved_entry.read_bytes()
                        size_bytes = len(content)
                        sha256 = hashlib.sha256(content).hexdigest()
                    except Exception:
                        pass

                files_info.append(
                    WorkspaceFileInfo(
                        relative_path=rel_str,
                        size_bytes=size_bytes,
                        is_directory=is_dir,
                        modified_at=mtime,
                        checksum_sha256=sha256,
                    )
                )

            rel_target_str = self._get_relative_path_string(target_path)
            fact = FactItem(
                statement=f"Listed {len(files_info)} items in workspace directory '{rel_target_str}'.",
                state=FactState.FACT,
                source="local_workspace",
            )
            return WorkspaceOperationResult(
                success=True,
                operation=WorkspaceOperationType.LIST_FILES,
                workspace_id=self._workspace_id,
                relative_path=rel_target_str,
                files=files_info,
                facts=[fact],
            )
        except Exception as e:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.LIST_FILES,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"LIST_ERROR: Failed to list files: {str(e)}",
                error_type="LIST_ERROR",
            )

    def file_exists(self, relative_path: str) -> bool:
        if not self.workspace_exists():
            return False
        try:
            target_path = self._validate_and_resolve_path(relative_path)
            return target_path.exists()
        except PathSecurityException:
            return False

    def record_artifact(
        self, relative_path: str, description: str = ""
    ) -> WorkspaceOperationResult:
        if not self.workspace_exists():
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.RECORD_ARTIFACT,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message="WORKSPACE_NOT_FOUND: Workspace directory does not exist or is inactive.",
                error_type="WORKSPACE_NOT_FOUND",
            )
        try:
            target_path = self._validate_and_resolve_path(relative_path)
        except PathSecurityException as se:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.RECORD_ARTIFACT,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=str(se),
                error_type="SECURITY_PATH_TRAVERSAL",
            )

        if not target_path.exists() or not target_path.is_file():
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.RECORD_ARTIFACT,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"FILE_NOT_FOUND: Cannot record artifact for non-existent file '{relative_path}'.",
                error_type="FILE_NOT_FOUND",
            )

        try:
            content_bytes = target_path.read_bytes()
            sha256_hash = hashlib.sha256(content_bytes).hexdigest()
            size_bytes = len(content_bytes)
            rel_str = self._get_relative_path_string(target_path)
            artifact_id = f"art-{uuid.uuid4().hex[:8]}"
            artifact_uri = f"workspace://{self._workspace_id}/{rel_str}"

            artifact = WorkspaceArtifact(
                artifact_id=artifact_id,
                workspace_id=self._workspace_id,
                relative_path=rel_str,
                artifact_uri=artifact_uri,
                checksum_sha256=sha256_hash,
                size_bytes=size_bytes,
                description=description or f"Recorded artifact at '{rel_str}'",
            )
            self._metadata.recorded_artifacts.append(artifact)

            evidence = ArtifactEvidence(
                evidence_id=f"ev-{artifact_id}",
                category=EvidenceCategory.ARTIFACT,
                artifact_uri=artifact_uri,
                checksum_sha256=sha256_hash,
                description=description or f"Artifact recorded for '{rel_str}'",
            )

            fact = FactItem(
                statement=f"Recorded workspace artifact '{rel_str}' (SHA256: {sha256_hash}).",
                state=FactState.FACT,
                source="local_workspace",
            )

            return WorkspaceOperationResult(
                success=True,
                operation=WorkspaceOperationType.RECORD_ARTIFACT,
                workspace_id=self._workspace_id,
                relative_path=rel_str,
                artifact=artifact,
                facts=[fact],
                evidence=[evidence],
            )
        except Exception as e:
            return WorkspaceOperationResult(
                success=False,
                operation=WorkspaceOperationType.RECORD_ARTIFACT,
                workspace_id=self._workspace_id,
                relative_path=relative_path,
                error_message=f"ARTIFACT_RECORDING_FAILED: {str(e)}",
                error_type="RECORDING_FAILED",
            )

    def close_workspace(self, cleanup: bool = False) -> WorkspaceOperationResult:
        self._is_active = False
        self._metadata.is_active = False

        if cleanup and self._root_path.exists():
            try:
                shutil.rmtree(self._root_path)
                fact = FactItem(
                    statement=f"Closed and cleaned up workspace directory '{self._root_path}'.",
                    state=FactState.FACT,
                    source="local_workspace",
                )
            except Exception as e:
                return WorkspaceOperationResult(
                    success=False,
                    operation=WorkspaceOperationType.CLOSE_WORKSPACE,
                    workspace_id=self._workspace_id,
                    error_message=f"CLEANUP_FAILED: Failed to remove workspace directory: {str(e)}",
                    error_type="CLEANUP_FAILED",
                )
        else:
            fact = FactItem(
                statement=f"Closed workspace '{self._workspace_id}'.",
                state=FactState.FACT,
                source="local_workspace",
            )

        return WorkspaceOperationResult(
            success=True,
            operation=WorkspaceOperationType.CLOSE_WORKSPACE,
            workspace_id=self._workspace_id,
            facts=[fact],
        )
