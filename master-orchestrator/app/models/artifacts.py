from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class TrustState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    RETRIEVED = "RETRIEVED"

class LineageArtifact(BaseModel):
    artifact_id: str
    execution_id: str
    plan_id: str
    plan_version: int
    step_id: str
    task_id: str
    attempt_id: str
    specialist_id: str
    artifact_type: str
    path: str
    url: str
    content: str
    is_mock: bool
    parent_artifact_ids: List[str]
    source_evidence_refs: List[str]
    trust_state: TrustState
    verification_status: str
    created_at: str
    checksum: Optional[str] = None
