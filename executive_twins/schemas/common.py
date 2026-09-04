from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class FactState(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    ASSUMPTION = "ASSUMPTION"
    UNKNOWN = "UNKNOWN"
    NOT_REGISTERED = "NOT_REGISTERED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    UNVERIFIED = "UNVERIFIED"


class FactItem(BaseModel):
    statement: str
    state: FactState
    source: str = "input"
    evidence_ref: Optional[str] = None


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    FAILED = "FAILED"


class ExecutiveReviewOutcome(str, Enum):
    APPROVED = "APPROVED"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    MORE_EVIDENCE_REQUIRED = "MORE_EVIDENCE_REQUIRED"
    SPECIALIST_FAILURE = "SPECIALIST_FAILURE"
    NO_REGISTERED_SPECIALIST_AVAILABLE = "NO_REGISTERED_SPECIALIST_AVAILABLE"
    SECURITY_AUTHORIZATION_REQUIRED = "SECURITY_AUTHORIZATION_REQUIRED"
    ESCALATE = "ESCALATE"


class FailureState(str, Enum):
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    CRITERIA_FAILED = "CRITERIA_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class SpecialistStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNAUTHORIZED = "UNAUTHORIZED"
    BUSY = "BUSY"


class SecurityContext(BaseModel):
    user_id: str = "system_user"
    clearance_level: str = "standard"
    allowed_roles: List[str] = Field(default_factory=lambda: ["user"])
    is_authenticated: bool = True
