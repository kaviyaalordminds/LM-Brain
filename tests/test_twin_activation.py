import pytest
from executive_twins.client.agent_adapter import MockSpecialistAgentAdapter
from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.orchestrator.twin_orchestrator import TwinOrchestrator
from executive_twins.twins.ceo import CEOTwin
from executive_twins.twins.cfo import CFOTwin
from executive_twins.twins.cmo import CMOTwin
from executive_twins.twins.coo import COOTwin
from executive_twins.twins.cto import CTOTwin


def test_twin_activation_triggers() -> None:
    ceo = CEOTwin()
    coo = COOTwin()
    cto = CTOTwin()
    cmo = CMOTwin()
    cfo = CFOTwin()

    assert ceo.should_activate("What is our long-term company strategy and major priorities?")
    assert coo.should_activate("Optimize our operational workflows and process bottlenecks.")
    assert cto.should_activate("Define our system architecture and technology strategy.")
    assert cmo.should_activate("Create a marketing app and campaign strategy for our product.")
    assert cfo.should_activate("Conduct financial analysis, budget, and ROI forecasting.")


def test_no_twin_activated_for_non_executive_request() -> None:
    registry = InMemorySpecialistRegistryAdapter()
    adapter = MockSpecialistAgentAdapter()
    orchestrator = TwinOrchestrator(registry, adapter)

    rec = orchestrator.process_request("Calculate 2 + 2")
    assert rec.executive_twin_id == "none"
    assert "NO_EXECUTIVE_TWIN_REQUIRED" in rec.recommendation_text
