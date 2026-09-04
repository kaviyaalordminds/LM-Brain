from typing import List, Optional

from executive_twins.schemas.common import SecurityContext, SpecialistStatus
from executive_twins.schemas.specialist import (
    CapabilityRequirement,
    SpecialistMetadata,
    SpecialistSelectionResult,
)


class CapabilityMatcher:
    """
    Capability-first selection engine.
    Matches required capabilities against authoritative registry metadata.
    Does NOT invent specialists or assume unverified capabilities exist.
    """

    @staticmethod
    def match_capability(
        requirement: CapabilityRequirement,
        candidates: List[SpecialistMetadata],
        security_context: SecurityContext,
    ) -> SpecialistSelectionResult:
        qualified: List[SpecialistMetadata] = []

        for candidate in candidates:
            # 1. Filter: Must be ACTIVE
            if candidate.status != SpecialistStatus.ACTIVE:
                continue

            # 2. Filter: Security clearance compatibility
            if candidate.security_level == "restricted" and security_context.clearance_level != "restricted":
                continue

            # 3. Filter: Check capability name match
            has_cap = any(
                cap.name.lower() == requirement.capability_name.lower() for cap in candidate.capabilities
            )
            if has_cap:
                qualified.append(candidate)

        if not qualified:
            return SpecialistSelectionResult(
                selected_specialist=None,
                matched_capabilities=[],
                selection_reason=f"NO_REGISTERED_SPECIALIST_AVAILABLE: No active, authorized specialist in registry has capability '{requirement.capability_name}'.",
                confidence=0.0,
                status="NO_REGISTERED_SPECIALIST_AVAILABLE",
            )

        # Rank candidates based on authoritative provenance and total matching capabilities
        def ranking_score(spec: SpecialistMetadata) -> float:
            score = 1.0
            if spec.provenance.is_authoritative:
                score += 1.0
            score += len(spec.capabilities) * 0.1
            return score

        ranked = sorted(qualified, key=ranking_score, reverse=True)
        selected = ranked[0]

        matched_names = [
            cap.name for cap in selected.capabilities if cap.name.lower() == requirement.capability_name.lower()
        ]

        return SpecialistSelectionResult(
            selected_specialist=selected,
            matched_capabilities=matched_names,
            selection_reason=f"Selected '{selected.name}' ({selected.specialist_id}) from authoritative registry snapshot '{selected.provenance.snapshot_id}'.",
            confidence=0.95,
            status="MATCHED",
        )
