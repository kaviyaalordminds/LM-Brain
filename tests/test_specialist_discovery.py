import pytest
from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.schemas.common import SecurityContext, SpecialistStatus
from executive_twins.schemas.specialist import (
    Capability,
    CapabilityRequirement,
    RegistryProvenance,
    SpecialistMetadata,
)


def test_specialist_discovery_matching() -> None:
    registry = InMemorySpecialistRegistryAdapter()

    spec = SpecialistMetadata(
        specialist_id="spec_strat_01",
        name="Strategy Specialist",
        capabilities=[
            Capability(name="marketing_strategy", description="Marketing campaign strategy")
        ],
        status=SpecialistStatus.ACTIVE,
        provenance=RegistryProvenance(registry_id="test-registry-01", snapshot_id="snap-v1"),
    )
    registry.register_specialist(spec)

    reqs = [CapabilityRequirement(capability_name="marketing_strategy", description="Needs marketing strategy")]
    context = SecurityContext()

    results = registry.discover_specialists(reqs, context)
    assert len(results) == 1
    assert results[0].status == "MATCHED"
    assert results[0].selected_specialist.specialist_id == "spec_strat_01"
    assert results[0].selected_specialist.provenance.snapshot_id == "snap-v1"


def test_specialist_discovery_missing_capability() -> None:
    registry = InMemorySpecialistRegistryAdapter()
    reqs = [CapabilityRequirement(capability_name="quantum_computing", description="Quantum algorithm")]
    context = SecurityContext()

    results = registry.discover_specialists(reqs, context)
    assert len(results) == 1
    assert results[0].status == "NO_REGISTERED_SPECIALIST_AVAILABLE"
    assert results[0].selected_specialist is None


def test_specialist_discovery_inactive_and_security_filtering() -> None:
    registry = InMemorySpecialistRegistryAdapter()

    inactive_spec = SpecialistMetadata(
        specialist_id="spec_inactive_01",
        name="Inactive Specialist",
        capabilities=[Capability(name="marketing_strategy", description="Strategy")],
        status=SpecialistStatus.INACTIVE,
    )
    restricted_spec = SpecialistMetadata(
        specialist_id="spec_restricted_01",
        name="Restricted Specialist",
        capabilities=[Capability(name="visual_design", description="Design")],
        status=SpecialistStatus.ACTIVE,
        security_level="restricted",
    )
    registry.register_specialist(inactive_spec)
    registry.register_specialist(restricted_spec)

    # Standard security context cannot access restricted or inactive specialists
    reqs = [
        CapabilityRequirement(capability_name="marketing_strategy", description="Strategy"),
        CapabilityRequirement(capability_name="visual_design", description="Design"),
    ]
    standard_context = SecurityContext(clearance_level="standard")

    results = registry.discover_specialists(reqs, standard_context)
    assert results[0].status == "NO_REGISTERED_SPECIALIST_AVAILABLE"
    assert results[1].status == "NO_REGISTERED_SPECIALIST_AVAILABLE"
