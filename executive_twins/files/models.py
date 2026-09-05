"""
Data models and schemas for Controlled Files API operations.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import FactItem
from executive_twins.schemas.evidence import ArtifactEvidence
from executive_twins.workspace.models import WorkspaceArtifact, WorkspaceFileInfo


class FileOperationType(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LIST = "LIST"
    EXISTS = "EXISTS"
    METADATA = "METADATA"


class FileMetadata(BaseModel):
    relative_path: str
    file_name: str
    size_bytes: int
    is_directory: bool
    modified_at: datetime
    checksum_sha256: Optional[str] = None
    workspace_id: str


class FileOperationRequest(BaseModel):
    operation: FileOperationType
    workspace_id: str
    relative_path: str
    content: Optional[str] = None
    overwrite: bool = False


class FileOperationResult(BaseModel):
    success: bool
    operation: FileOperationType
    workspace_id: str
    relative_path: Optional[str] = None
    content: Optional[str] = None
    exists: Optional[bool] = None
    metadata: Optional[FileMetadata] = None
    files: List[FileMetadata] = Field(default_factory=list)
    artifact: Optional[WorkspaceArtifact] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    facts: List[FactItem] = Field(default_factory=list)
    evidence: List[ArtifactEvidence] = Field(default_factory=list)
