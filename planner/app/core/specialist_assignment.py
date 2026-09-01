"""
Planner — Specialist Assignment

Maps detected capabilities to the 10 known specialist IDs.
Assignment is fully deterministic — no random selection.

Priority rules (when multiple capabilities map to the same specialist):
  - The specialist is included once.
  - Capabilities are listed under the assigned specialist.

Unknown capabilities produce a 'research' specialist as a fallback,
NOT an invented specialist.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.plan import KNOWN_SPECIALISTS


# ---------------------------------------------------------------------------
# Capability → Specialist mapping
# Ordered from most specific to least specific within each specialist.
# ---------------------------------------------------------------------------

CAPABILITY_TO_SPECIALIST: dict[str, str] = {
    # Web / Frontend
    "frontend": "web_development",
    # Backend
    "backend": "backend",
    "authentication": "security",       # Auth is primarily a security concern
    "authorization": "security",
    # Database
    "database": "database",
    # API Integration (third-party)
    "api_integration": "api_integration",
    # Security
    "security": "security",
    # Testing
    "testing": "testing",
    # DevOps
    "deployment": "devops",
    "docker": "devops",
    "cicd": "devops",
    "cloud": "devops",
    # AI / ML
    "ai_ml": "ai_ml",
    "rag": "ai_ml",
    "vector_database": "ai_ml",
    # Research / Documentation
    "research": "research",
    "external_docs": "research",
    # Image generation
    "image_generation": "image_generation",
    # Memory signals — not directly a specialist; Orchestrator resolves at runtime
    # research specialist handles knowledge discovery
    "memory": "research",
}


@dataclass
class SpecialistAssignment:
    """Result of assigning a set of capabilities to a specialist."""
    specialist_id: str
    capabilities: list[str] = field(default_factory=list)
    is_known: bool = True


def assign_specialists(capabilities: list[str]) -> list[SpecialistAssignment]:
    """
    Deterministically assign capabilities to specialists.

    Rules:
    1. Map each known capability to its specialist via CAPABILITY_TO_SPECIALIST.
    2. Group capabilities by specialist (a specialist may cover multiple capabilities).
    3. Unknown capabilities fall back to 'research'.
    4. Return one SpecialistAssignment per specialist, deduplicated.

    Returns assignments in a deterministic order (alphabetical by specialist_id).
    """
    specialist_capability_map: dict[str, list[str]] = {}

    for cap in capabilities:
        specialist_id = CAPABILITY_TO_SPECIALIST.get(cap)
        if specialist_id is None:
            # Unknown capability — controlled fallback, not an invented specialist
            specialist_id = "research"
        specialist_capability_map.setdefault(specialist_id, []).append(cap)

    # Return sorted by specialist_id for determinism
    assignments: list[SpecialistAssignment] = []
    for specialist_id in sorted(specialist_capability_map.keys()):
        assignments.append(
            SpecialistAssignment(
                specialist_id=specialist_id,
                capabilities=sorted(specialist_capability_map[specialist_id]),
                is_known=specialist_id in KNOWN_SPECIALISTS,
            )
        )

    return assignments


def is_valid_specialist(specialist_id: str) -> bool:
    """Return True iff the specialist_id is in the known catalog."""
    return specialist_id in KNOWN_SPECIALISTS
