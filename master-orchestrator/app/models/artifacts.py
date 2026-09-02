import hashlib
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TrustState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETRIEVED = "RETRIEVED"
    PENDING = "PENDING"

class LineageArtifact(BaseModel):
    artifact_id: str
    execution_id: str
    plan_id: str
    plan_version: int = 1
    step_id: str
    task_id: str = ""
    attempt_id: str = ""
    specialist_id: str
    artifact_type: str
    path: str = ""
    url: str = ""
    content: str = ""
    is_mock: bool = False
    parent_artifact_ids: List[str] = Field(default_factory=list)
    source_evidence_refs: List[str] = Field(default_factory=list)
    trust_state: TrustState = TrustState.UNVERIFIED
    verification_status: str = "PENDING"
    created_at: str
    checksum: Optional[str] = None

    @staticmethod
    def calculate_checksum(data: str) -> str:
        """Compute deterministic SHA-256 checksum of artifact content."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

