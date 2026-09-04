import pytest
from executive_twins.client.agent_adapter import MockSpecialistAgentAdapter
from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.orchestrator.twin_orchestrator import TwinOrchestrator
from executive_twins.schemas.common import ExecutiveReviewOutcome, SpecialistStatus
from executive_twins.schemas.specialist import (
    Capability,
    RegistryProvenance,
    SpecialistMetadata,
)
from executive_twins.utils.audit_logger import AuditLogger


def test_end_to_end_cmo_marketing_app_workflow() -> None:
    AuditLogger.clear_events()

    # Step 1: Set up authoritative test registry client with registered specialists
    registry = InMemorySpecialistRegistryAdapter()

    spec_strat = SpecialistMetadata(
        specialist_id="spec_mkt_strat_01",
        name="Strategy Specialist",
        capabilities=[Capability(name="marketing_strategy", description="Digital marketing strategy")],
        status=SpecialistStatus.ACTIVE,
        provenance=RegistryProvenance(registry_id="prod-reg-01", snapshot_id="snap-2026-v1"),
    )
    spec_design = SpecialistMetadata(
        specialist_id="spec_visual_design_01",
        name="Design Specialist",
        capabilities=[Capability(name="visual_design", description="UI design & branding")],
        status=SpecialistStatus.ACTIVE,
        provenance=RegistryProvenance(registry_id="prod-reg-01", snapshot_id="snap-2026-v1"),
    )
    spec_dev = SpecialistMetadata(
        specialist_id="spec_app_dev_01",
        name="App Dev Specialist",
        capabilities=[Capability(name="software_development", description="Frontend & backend dev")],
        status=SpecialistStatus.ACTIVE,
        provenance=RegistryProvenance(registry_id="prod-reg-01", snapshot_id="snap-2026-v1"),
    )

    registry.register_specialist(spec_strat)
    registry.register_specialist(spec_design)
    registry.register_specialist(spec_dev)

    # Step 2: Set up specialist execution adapter
    agent_adapter = MockSpecialistAgentAdapter()

    # Step 3: Initialize TwinOrchestrator
    orchestrator = TwinOrchestrator(registry_client=registry, agent_adapter=agent_adapter)

    # Step 4: Process User Request
    user_request = "Create a complete marketing app for our product."
    recommendation = orchestrator.process_request(user_request)

    # Step 5: Assertions & Verification
    assert recommendation.role == "CMO Twin"
    assert recommendation.final_status == ExecutiveReviewOutcome.APPROVED
    assert recommendation.confidence >= 0.90
    assert len(recommendation.delegation_results) == 3

    # Check delegation results contain empirical evidence
    for del_res in recommendation.delegation_results:
        assert del_res.status == "SUCCESS"
        assert len(del_res.evidence.items) > 0
        assert del_res.evidence.contains_category(
            del_res.evidence.items[0].category
        )

    # Check audit events were recorded
    events = AuditLogger.get_events()
    event_types = [e.event_type for e in events]
    assert "twin.resolution.started" in event_types
    assert "twin.resolved" in event_types
    assert "twin.activated" in event_types
    assert "specialist.discovery.started" in event_types
    assert "specialist.selected" in event_types
    assert "delegation.created" in event_types
    assert "evidence.received" in event_types
    assert "recommendation.created" in event_types
