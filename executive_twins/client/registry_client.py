from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from executive_twins.schemas.common import SecurityContext, SpecialistStatus
from executive_twins.schemas.specialist import (
    CapabilityRequirement,
    SpecialistMetadata,
    SpecialistSelectionResult,
)


class ISpecialistRegistryClient(ABC):
    """
    Authoritative client interface for discovering and retrieving Specialist Agent metadata.
    Executive Twins MUST NOT own or fabricate the Specialist Registry.
    """

    @abstractmethod
    def discover_specialists(
        self,
        requirements: List[CapabilityRequirement],
        security_context: SecurityContext,
    ) -> List[SpecialistSelectionResult]:
        """Discover specialists matching capability requirements."""
        pass

    @abstractmethod
    def get_specialist_by_id(self, specialist_id: str) -> Optional[SpecialistMetadata]:
        """Retrieve specialist metadata by exact ID."""
        pass

    @abstractmethod
    def list_all_specialists(self) -> List[SpecialistMetadata]:
        """List all specialists registered in the authoritative source."""
        pass


class InMemorySpecialistRegistryAdapter(ISpecialistRegistryClient):
    """
    DEV_TEST_ONLY_ADAPTER: Development and testing in-memory implementation.
    THIS IS NOT THE PRODUCTION SOURCE OF TRUTH.
    Consumed as an adapter for local testing when external production registry is not attached.
    """

    def __init__(self) -> None:
        self._specialists: Dict[str, SpecialistMetadata] = {}

    def register_specialist(self, specialist: SpecialistMetadata) -> None:
        """Register a specialist metadata entry into the test adapter."""
        self._specialists[specialist.specialist_id] = specialist

    def get_specialist_by_id(self, specialist_id: str) -> Optional[SpecialistMetadata]:
        return self._specialists.get(specialist_id)

    def list_all_specialists(self) -> List[SpecialistMetadata]:
        return list(self._specialists.values())

    def discover_specialists(
        self,
        requirements: List[CapabilityRequirement],
        security_context: SecurityContext,
    ) -> List[SpecialistSelectionResult]:
        results: List[SpecialistSelectionResult] = []

        for req in requirements:
            matched_specialist: Optional[SpecialistMetadata] = None
            matched_caps: List[str] = []

            for spec in self._specialists.values():
                # Filter: Must be ACTIVE
                if spec.status != SpecialistStatus.ACTIVE:
                    continue

                # Filter: Security clearance compatibility
                # (Simple check: standard context can't access restricted specialists unless authorized)
                if spec.security_level == "restricted" and security_context.clearance_level != "restricted":
                    continue

                # Capability compatibility check
                for cap in spec.capabilities:
                    if cap.name.lower() == req.capability_name.lower():
                        matched_specialist = spec
                        matched_caps.append(cap.name)
                        break

                if matched_specialist:
                    break

            if matched_specialist:
                results.append(
                    SpecialistSelectionResult(
                        selected_specialist=matched_specialist,
                        matched_capabilities=matched_caps,
                        selection_reason=f"Matched capability requirement '{req.capability_name}' from registry snapshot '{matched_specialist.provenance.snapshot_id}'.",
                        confidence=1.0,
                        status="MATCHED",
                    )
                )
            else:
                results.append(
                    SpecialistSelectionResult(
                        selected_specialist=None,
                        matched_capabilities=[],
                        selection_reason=f"NO_REGISTERED_SPECIALIST_AVAILABLE: No active, authorized specialist registered for capability '{req.capability_name}'.",
                        confidence=0.0,
                        status="NO_REGISTERED_SPECIALIST_AVAILABLE",
                    )
                )

        return results
