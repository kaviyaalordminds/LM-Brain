"""
Productivity Integration Domain Models.
Provides typed models and schemas for storage providers, export formats,
export requests, export results, and synchronization statuses.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class StorageProvider(str, Enum):
    """Supported storage provider identities."""
    LOCAL = "LOCAL"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    ONEDRIVE = "ONEDRIVE"
    OBSIDIAN = "OBSIDIAN"


class ExportFormat(str, Enum):
    """Supported export and representation formats."""
    ORIGINAL = "ORIGINAL"
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"
    CSV = "CSV"
    TSV = "TSV"
    TEXT = "TEXT"


class SyncStatus(str, Enum):
    """Bounded lifecycle states for artifact storage and export operations."""
    NOT_STARTED = "NOT_STARTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


def _validate_safe_relative_path(v: str) -> str:
    """Validate that path is relative, safe, and does not perform traversal."""
    if not v or not v.strip():
        raise ValueError("Path cannot be empty.")
    v = v.strip().replace("\\", "/")
    if v.startswith("/") or re.match(r"^[a-zA-Z]:", v):
        raise ValueError(f"Absolute paths are forbidden: '{v}'. Must be a workspace-relative path.")
    parts = v.split("/")
    if ".." in parts:
        raise ValueError(f"Path traversal ('..') is forbidden: '{v}'.")
    return v


class ExportRequest(BaseModel):
    """
    Request specification for exporting an existing workspace artifact to a target format/provider.
    """
    source_workspace: str = "default"
    source_relative_path: str = Field(..., description="Relative path of source artifact in workspace")
    destination_workspace: Optional[str] = None
    destination_relative_path: Optional[str] = None
    provider: StorageProvider = StorageProvider.LOCAL
    requested_format: ExportFormat = ExportFormat.ORIGINAL
    overwrite: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    @field_validator("source_relative_path")
    @classmethod
    def validate_src_path(cls, v: str) -> str:
        return _validate_safe_relative_path(v)

    @field_validator("destination_relative_path")
    @classmethod
    def validate_dest_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_safe_relative_path(v)
        return v


class ExportResult(BaseModel):
    """
    Outcome of an artifact export operation.
    """
    status: SyncStatus = SyncStatus.SUCCESS
    source_artifact: str
    destination_artifact: Optional[str] = None
    provider: StorageProvider = StorageProvider.LOCAL
    format: ExportFormat = ExportFormat.ORIGINAL
    checksum_sha256: Optional[str] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StorageRequest(BaseModel):
    """
    Request specification for copying or storing an artifact in a target logical destination.
    """
    source_workspace: str = "default"
    source_relative_path: str = Field(..., description="Relative path of source artifact in workspace")
    destination_workspace: Optional[str] = None
    destination_relative_path: Optional[str] = None
    provider: StorageProvider = StorageProvider.LOCAL
    overwrite: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    @field_validator("source_relative_path")
    @classmethod
    def validate_src_path(cls, v: str) -> str:
        return _validate_safe_relative_path(v)

    @field_validator("destination_relative_path")
    @classmethod
    def validate_dest_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_safe_relative_path(v)
        return v


class StorageResult(BaseModel):
    """
    Outcome of an artifact storage/movement operation.
    """
    status: SyncStatus = SyncStatus.SUCCESS
    source_artifact: str
    destination_artifact: Optional[str] = None
    provider: StorageProvider = StorageProvider.LOCAL
    checksum_sha256: Optional[str] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
