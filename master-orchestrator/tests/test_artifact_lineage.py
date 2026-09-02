"""
Tests for LineageArtifact — artifact creation, trust states, provenance references.
"""
from __future__ import annotations

import pytest
from app.models.artifacts import LineageArtifact, TrustState

def test_lineage_artifact_properties():
    art = LineageArtifact(
        artifact_id="art-001",
        execution_id="exec-001",
        plan_id="plan-001",
        plan_version=1,
        step_id="step-001",
        task_id="task-001",
        attempt_id="att-001",
        specialist_id="backend",
        artifact_type="code",
        path="src/api.py",
        url="",
        content="print('hello')",
        is_mock=False,
        parent_artifact_ids=["art-parent"],
        source_evidence_refs=["evidence-ref-1"],
        trust_state=TrustState.APPROVED,
        verification_status="PASSED",
        created_at="2026-09-02T10:00:00Z"
    )
    
    assert art.artifact_id == "art-001"
    assert art.trust_state == TrustState.APPROVED
    assert art.is_mock is False
    assert art.parent_artifact_ids == ["art-parent"]
    assert art.source_evidence_refs == ["evidence-ref-1"]
    
    dumped = art.model_dump(mode="json")
    assert dumped["artifact_id"] == "art-001"
    assert dumped["trust_state"] == "APPROVED"

