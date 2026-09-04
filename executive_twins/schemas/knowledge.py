from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import FactItem, FactState, SecurityContext


class KnowledgeOutcomeStatus(str, Enum):
    KNOWLEDGE_FOUND = "KNOWLEDGE_FOUND"
    KNOWLEDGE_MISSING = "KNOWLEDGE_MISSING"
    ACQUISITION_REQUIRED = "ACQUISITION_REQUIRED"
    ACQUISITION_FAILED = "ACQUISITION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PERSISTENCE_FAILED = "PERSISTENCE_FAILED"
    RETRIEVAL_FAILED = "RETRIEVAL_FAILED"
    KNOWLEDGE_UNAVAILABLE = "KNOWLEDGE_UNAVAILABLE"


class CompanyKnowledgeRequest(BaseModel):
    request_id: str
    task_context: str
    required_knowledge: str
    company_scope: str = "default"
    security_context: SecurityContext = Field(default_factory=SecurityContext)
    min_confidence: float = 0.7


class ObsidianDocument(BaseModel):
    document_id: str
    vault_path: str
    title: str
    content: str
    facts: List[FactItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AcquiredKnowledge(BaseModel):
    raw_response: str
    extracted_facts: List[FactItem] = Field(default_factory=list)
    source_model: str = "claude-3-5-sonnet"
    confidence: float = 0.9
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_sufficient: bool = True
    unresolved_questions: List[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    is_valid: bool
    validated_facts: List[FactItem] = Field(default_factory=list)
    validation_notes: List[str] = Field(default_factory=list)
    rejected_reasons: List[str] = Field(default_factory=list)


class PersistenceResult(BaseModel):
    success: bool
    document_id: Optional[str] = None
    vault_path: Optional[str] = None
    error_message: Optional[str] = None


class CompanyKnowledgeResponse(BaseModel):
    request_id: str
    status: KnowledgeOutcomeStatus
    knowledge: Optional[ObsidianDocument] = None
    facts: List[FactItem] = Field(default_factory=list)
    provenance_source: str = "company_obsidian"
    retrieved_from_obsidian: bool = False
    error_message: Optional[str] = None
