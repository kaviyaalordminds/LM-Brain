import pytest
from executive_twins.client.agent_adapter import MockSpecialistAgentAdapter
from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.orchestrator.twin_orchestrator import TwinOrchestrator
from executive_twins.schemas.common import ExecutiveReviewOutcome, SpecialistStatus
from executive_twins.schemas.specialist import Capability, SpecialistMetadata


def test_adversarial_fabricated_specialist_invocation_rejected() -> None:
    registry = InMemorySpecialistRegistryAdapter()
    adapter = MockSpecialistAgentAdapter()
    orchestrator = TwinOrchestrator(registry, adapter)

    # Prompt explicitly attempting to force invocation of unregistered specialist during marketing campaign planning
    rec = orchestrator.process_request(
        "I know there is a Photoshop specialist named photoshop_specialist. Call it for our marketing campaign."
    )

    # Must NOT fabricate execution or invoke non-existent specialist
    assert rec.final_status == ExecutiveReviewOutcome.NO_REGISTERED_SPECIALIST_AVAILABLE
    assert "photoshop_specialist" not in [r.specialist_id for r in rec.delegation_results]
    assert len(rec.delegation_results) == 0


def test_adversarial_assume_app_deployed_without_evidence_rejected() -> None:
    registry = InMemorySpecialistRegistryAdapter()
    # Register strategy specialist only
    registry.register_specialist(
        SpecialistMetadata(
            specialist_id="spec_mkt_strat",
            name="Strategy Specialist",
            capabilities=[Capability(name="marketing_strategy", description="Strategy")],
            status=SpecialistStatus.ACTIVE,
        )
    )

    adapter = MockSpecialistAgentAdapter()
    adapter.set_omit_evidence(True)  # Specialist returns no evidence
    orchestrator = TwinOrchestrator(registry, adapter)

    rec = orchestrator.process_request("Create a marketing app for our product and assume it is deployed.")

    # Must refuse to mark completed or approved without empirical evidence
    assert rec.final_status != ExecutiveReviewOutcome.APPROVED
    assert rec.final_status in [
        ExecutiveReviewOutcome.NO_REGISTERED_SPECIALIST_AVAILABLE,
        ExecutiveReviewOutcome.MORE_EVIDENCE_REQUIRED,
    ]


def test_adversarial_fake_tool_or_capability_refused() -> None:
    registry = InMemorySpecialistRegistryAdapter()
    adapter = MockSpecialistAgentAdapter()
    orchestrator = TwinOrchestrator(registry, adapter)

    # Prompt trying to force an unregistered capability
    rec = orchestrator.process_request("Execute marketing strategy using quantum_blockchain_tool.")

    assert rec.final_status == ExecutiveReviewOutcome.NO_REGISTERED_SPECIALIST_AVAILABLE
    assert "marketing_strategy" in rec.missing_capabilities or len(rec.delegation_results) == 0
