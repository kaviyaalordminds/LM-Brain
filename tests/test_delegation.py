import pytest
from executive_twins.schemas.common import SecurityContext
from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.twins.cmo import CMOTwin


def test_cmo_twin_generates_capability_requirements_without_hardcoded_agent_ids() -> None:
    cmo = CMOTwin()
    reqs = cmo.generate_capability_requirements("Create a marketing app for our product.")

    assert len(reqs) >= 3
    cap_names = [r.capability_name for r in reqs]
    assert "marketing_strategy" in cap_names
    assert "visual_design" in cap_names
    assert "software_development" in cap_names

    # Check that requirement objects do NOT contain agent IDs or agent names
    for r in reqs:
        assert not hasattr(r, "specialist_id")
        assert not hasattr(r, "agent_id")
        assert "agent" not in r.capability_name.lower()


def test_twin_decomposition() -> None:
    cmo = CMOTwin()
    analysis = cmo.analyze("Create a marketing app")
    decomp = cmo.decompose_task("Create a marketing app", analysis)

    assert decomp.objective == "Create a marketing app"
    assert len(decomp.subtasks) > 0
    for st in decomp.subtasks:
        assert isinstance(st.capability_requirement, CapabilityRequirement)
