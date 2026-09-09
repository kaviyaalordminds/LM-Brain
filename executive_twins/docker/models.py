"""
Data models and schemas for Controlled Docker Execution Layer.
Provides typed Docker operations, requests, inspection models, and structured execution results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from executive_twins.schemas.common import FactItem
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    DataEvidence,
    ExecutionLogEvidence,
    TestEvidence,
    VerificationEvidence,
)


class DockerOperationType(str, Enum):
    """
    Exclusively supported, explicitly modeled Docker operations.
    Arbitrary CLI commands, exec, shell, or daemon controls are strictly forbidden.
    """
    CHECK_AVAILABILITY = "CHECK_AVAILABILITY"
    BUILD_IMAGE = "BUILD_IMAGE"
    RUN_CONTAINER = "RUN_CONTAINER"
    STOP_CONTAINER = "STOP_CONTAINER"
    REMOVE_CONTAINER = "REMOVE_CONTAINER"
    INSPECT_CONTAINER = "INSPECT_CONTAINER"


class DockerStatus(str, Enum):
    """Execution outcome status for controlled Docker operations."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    REJECTED = "REJECTED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    INVALID_INPUT = "INVALID_INPUT"
    DOCKER_UNAVAILABLE = "DOCKER_UNAVAILABLE"
    IMAGE_BUILD_FAILED = "IMAGE_BUILD_FAILED"
    CONTAINER_FAILED = "CONTAINER_FAILED"
    CONTAINER_NOT_FOUND = "CONTAINER_NOT_FOUND"
    CONTAINER_STOPPED = "CONTAINER_STOPPED"
    CONTAINER_REMOVED = "CONTAINER_REMOVED"


class ContainerInspectionResult(BaseModel):
    """Structured result of inspecting a controlled container."""
    container_id: str
    container_name: str
    image: str
    status: str
    running: bool
    exit_code: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class DockerRequest(BaseModel):
    """
    Structured request for controlled Docker operations within a Software Development Workspace.
    Raw command strings, arbitrary Docker CLI flags, host path mounts, and daemon controls are strictly forbidden.
    """
    model_config = ConfigDict(extra="forbid")

    operation: DockerOperationType
    workspace_id: Optional[str] = None
    image_name: Optional[str] = None
    dockerfile_path: Optional[str] = None
    build_context: Optional[str] = None
    container_name: Optional[str] = None
    environment: Dict[str, str] = Field(default_factory=dict)
    command: Optional[List[str]] = None
    timeout_seconds: Optional[float] = None
    memory_limit: Optional[str] = None
    cpu_limit: Optional[float] = None
    force: Optional[bool] = False


class DockerResult(BaseModel):
    """
    Structured outcome of a controlled Docker operation.
    Contains explicit typed fields for container/image identifiers, logs, execution metrics,
    bounded stdout/stderr, facts, and empirical verification evidence.
    """
    success: bool
    operation: DockerOperationType
    status: DockerStatus
    message: Optional[str] = None
    image_id: Optional[str] = None
    image_name: Optional[str] = None
    container_id: Optional[str] = None
    container_name: Optional[str] = None
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    timed_out: bool = False
    output_truncated: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    inspection: Optional[ContainerInspectionResult] = None
    facts: List[FactItem] = Field(default_factory=list)
    evidence: List[Union[ExecutionLogEvidence, ArtifactEvidence, DataEvidence, TestEvidence, VerificationEvidence]] = Field(
        default_factory=list
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
