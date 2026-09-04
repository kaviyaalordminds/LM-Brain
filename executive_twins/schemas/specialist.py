from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from executive_twins.schemas.common import SpecialistStatus


class RegistryProvenance(BaseModel):
    registry_id: str = "default-specialist-registry"
    snapshot_id: str = "snap-initial"
    metadata_version: str = "1.0.0"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_authoritative: bool = True


class Capability(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    required_tools: List[str] = Field(default_factory=list)


class SpecialistMetadata(BaseModel):
    specialist_id: str
    name: str
    capabilities: List[Capability]
    status: SpecialistStatus = SpecialistStatus.ACTIVE
    authorized_tools: List[str] = Field(default_factory=list)
    security_level: str = "standard"
    provenance: RegistryProvenance = Field(default_factory=RegistryProvenance)


class CapabilityRequirement(BaseModel):
    capability_name: str
    description: str
    min_security_level: str = "standard"
    constraints: List[str] = Field(default_factory=list)


class SpecialistSelectionResult(BaseModel):
    selected_specialist: Optional[SpecialistMetadata] = None
    matched_capabilities: List[str] = Field(default_factory=list)
    selection_reason: str
    confidence: float = 1.0
    status: str = "MATCHED"  # "MATCHED" or "NO_REGISTERED_SPECIALIST_AVAILABLE"
