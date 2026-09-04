from datetime import datetime, timezone
from enum import Enum
from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class EvidenceCategory(str, Enum):
    ARTIFACT = "ARTIFACT"
    EXECUTION_LOG = "EXECUTION_LOG"
    TEST = "TEST"
    DATA = "DATA"
    SOURCE = "SOURCE"
    API_RESPONSE = "API_RESPONSE"
    VERIFICATION = "VERIFICATION"


class BaseEvidence(BaseModel):
    evidence_id: str
    category: EvidenceCategory
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    system_generated: bool = True
    description: str = ""


class ArtifactEvidence(BaseEvidence):
    category: Literal[EvidenceCategory.ARTIFACT] = EvidenceCategory.ARTIFACT
    artifact_uri: str
    mime_type: str = "text/plain"
    checksum_sha256: Optional[str] = None


class ExecutionLogEvidence(BaseEvidence):
    category: Literal[EvidenceCategory.EXECUTION_LOG] = EvidenceCategory.EXECUTION_LOG
    execution_id: str
    log_snippet: str
    exit_code: int = 0


class TestEvidence(BaseEvidence):
    category: Literal[EvidenceCategory.TEST] = EvidenceCategory.TEST
    suite_name: str
    tests_passed: int
    tests_failed: int
    report_uri: Optional[str] = None


class DataEvidence(BaseEvidence):
    category: Literal[EvidenceCategory.DATA] = EvidenceCategory.DATA
    record_count: int
    schema_name: str
    data_summary: str


class SourceEvidence(BaseEvidence):
    category: Literal[EvidenceCategory.SOURCE] = EvidenceCategory.SOURCE
    source_system: str
    query_signature: str


class APIResponseEvidence(BaseEvidence):
    category: Literal[EvidenceCategory.API_RESPONSE] = EvidenceCategory.API_RESPONSE
    endpoint: str
    status_code: int
    response_hash: str


class VerificationEvidence(BaseEvidence):
    category: Literal[EvidenceCategory.VERIFICATION] = EvidenceCategory.VERIFICATION
    verifier_id: str
    verified_status: str
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


TypedEvidence = Union[
    ArtifactEvidence,
    ExecutionLogEvidence,
    TestEvidence,
    DataEvidence,
    SourceEvidence,
    APIResponseEvidence,
    VerificationEvidence,
]


class EvidenceSet(BaseModel):
    items: List[TypedEvidence] = Field(default_factory=list)

    def contains_category(self, category: EvidenceCategory) -> bool:
        return any(item.category == category for item in self.items)

    def get_by_category(self, category: EvidenceCategory) -> List[TypedEvidence]:
        return [item for item in self.items if item.category == category]
