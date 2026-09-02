"""
Tests for TrustPolicy — trust state semantics, production artifact blocking, memory persistence gate.

Critical: RETRIEVED is provenance (access tag), NOT a trust promotion.
Trust chain: UNVERIFIED → (Memory Agent validates) → VALIDATED → (Memory Agent approves) → APPROVED
"""
from __future__ import annotations

import pytest

from app.models.artifacts import TrustState
from app.policies.trust_policy import TrustPolicy


class TestContextUsability:
    def test_validated_can_be_used_as_context(self):
        assert TrustPolicy.can_use_as_context(TrustState.VALIDATED) is True

    def test_approved_can_be_used_as_context(self):
        assert TrustPolicy.can_use_as_context(TrustState.APPROVED) is True

    def test_retrieved_can_be_used_as_context(self):
        """RETRIEVED = provenance tag, safe to use as context."""
        assert TrustPolicy.can_use_as_context(TrustState.RETRIEVED) is True

    def test_unverified_cannot_be_used_as_context(self):
        """Unverified external research must not be trusted as context."""
        assert TrustPolicy.can_use_as_context(TrustState.UNVERIFIED) is False


class TestMemoryPersistence:
    def test_approved_can_persist_to_memory(self):
        assert TrustPolicy.can_persist_to_memory(TrustState.APPROVED) is True

    def test_validated_cannot_persist_to_memory(self):
        """Validated but not approved cannot be persisted."""
        assert TrustPolicy.can_persist_to_memory(TrustState.VALIDATED) is False

    def test_unverified_cannot_persist_to_memory(self):
        assert TrustPolicy.can_persist_to_memory(TrustState.UNVERIFIED) is False

    def test_retrieved_cannot_persist_to_memory(self):
        """RETRIEVED is a read provenance tag, not an approval for write."""
        assert TrustPolicy.can_persist_to_memory(TrustState.RETRIEVED) is False


class TestProductionArtifactBlocking:
    def test_unverified_blocks_production_artifact(self):
        """External research evidence starts UNVERIFIED and must block artifact creation."""
        assert TrustPolicy.blocks_production_artifact(TrustState.UNVERIFIED) is True

    def test_validated_does_not_block(self):
        assert TrustPolicy.blocks_production_artifact(TrustState.VALIDATED) is False

    def test_approved_does_not_block(self):
        assert TrustPolicy.blocks_production_artifact(TrustState.APPROVED) is False

    def test_retrieved_does_not_block(self):
        """RETRIEVED memory context is safe to use in artifacts."""
        assert TrustPolicy.blocks_production_artifact(TrustState.RETRIEVED) is False


class TestTrustStateSemantics:
    def test_retrieved_is_not_higher_than_approved(self):
        """
        RETRIEVED must NOT be treated as a higher trust level than APPROVED.
        It is a provenance/access tag indicating data was read from Memory Agent.
        """
        # Both RETRIEVED and APPROVED are usable as context
        assert TrustPolicy.can_use_as_context(TrustState.RETRIEVED) is True
        assert TrustPolicy.can_use_as_context(TrustState.APPROVED) is True
        # But RETRIEVED cannot persist to memory (only APPROVED can)
        assert TrustPolicy.can_persist_to_memory(TrustState.RETRIEVED) is False
        assert TrustPolicy.can_persist_to_memory(TrustState.APPROVED) is True

    def test_unverified_cannot_bypass_validation(self):
        """
        UNVERIFIED data cannot be used as context, persisted, or create production artifacts.
        Only the Memory Agent's validation/write contract can change trust state.
        """
        assert TrustPolicy.can_use_as_context(TrustState.UNVERIFIED) is False
        assert TrustPolicy.can_persist_to_memory(TrustState.UNVERIFIED) is False
        assert TrustPolicy.blocks_production_artifact(TrustState.UNVERIFIED) is True
