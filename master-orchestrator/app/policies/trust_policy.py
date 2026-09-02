from app.models.artifacts import TrustState

class TrustPolicy:
    @staticmethod
    def can_use_as_context(trust_state: TrustState) -> bool:
        return trust_state in {TrustState.VALIDATED, TrustState.APPROVED, TrustState.RETRIEVED}

    @staticmethod
    def can_persist_to_memory(trust_state: TrustState) -> bool:
        return trust_state == TrustState.APPROVED

    @staticmethod
    def blocks_production_artifact(trust_state: TrustState) -> bool:
        return trust_state == TrustState.UNVERIFIED
