"""
Data models and schemas for Software Development Workspace operations.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import FactItem
from executive_twins.schemas.evidence import ArtifactEvidence


class WorkspaceOperationType(str, Enum):
    CREATE_WORKSPACE = "CREATE_WORKSPACE"
    READ_FILE = "READ_FILE"
    WRITE_FILE = "WRITE_FILE"
    DELETE_FILE = "DELETE_FILE"
    LIST_FILES = "LIST_FILES"
    FILE_EXISTS = "FILE_EXISTS"
    RECORD_ARTIFACT = "RECORD_ARTIFACT"
    CLOSE_WORKSPACE = "CLOSE_WORKSPACE"
    REGISTERED_CAPABILITY_EXECUTION = "REGISTERED_CAPABILITY_EXECUTION"


class WorkspaceFileInfo(BaseModel):
    relative_path: str
    size_bytes: int
    is_directory: bool
    modified_at: datetime
    checksum_sha256: Optional[str] = None


class WorkspaceArtifact(BaseModel):
    artifact_id: str
    workspace_id: str
    relative_path: str
    artifact_uri: str
    checksum_sha256: str
    size_bytes: int
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkspaceOperationResult(BaseModel):
    success: bool
    operation: WorkspaceOperationType
    workspace_id: str
    relative_path: Optional[str] = None
    content: Optional[str] = None
    files: List[WorkspaceFileInfo] = Field(default_factory=list)
    artifact: Optional[WorkspaceArtifact] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    facts: List[FactItem] = Field(default_factory=list)
    evidence: List[ArtifactEvidence] = Field(default_factory=list)


class WorkspaceMetadata(BaseModel):
    workspace_id: str
    root_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    recorded_artifacts: List[WorkspaceArtifact] = Field(default_factory=list)
