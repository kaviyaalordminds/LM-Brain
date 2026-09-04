from typing import Dict, Optional, List
import uuid

from executive_twins.memory.interfaces import (
    IClaudeClient,
    IMemoryKnowledgeAgent,
    IObsidianAdapter,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.knowledge import (
    AcquiredKnowledge,
    ObsidianDocument,
    PersistenceResult,
)


class DevTestObsidianAdapter(IObsidianAdapter):
    """
    DEV_TEST_ONLY_ADAPTER: In-memory simulation of Company Obsidian vault.
    THIS IS NOT THE PRODUCTION OBSIDIAN INTEGRATION.
    Used for local development and testing when external Obsidian vault is not attached.
    """

    def __init__(self) -> None:
        self._vault: Dict[str, ObsidianDocument] = {}
        self._should_fail_write: bool = False
        self._should_fail_read_after_write: bool = False

    def seed_document(self, document: ObsidianDocument) -> None:
        """Seed a pre-existing document into the test vault."""
        self._vault[document.document_id] = document

    def set_fail_write(self, fail: bool) -> None:
        """Simulate persistence failure for test assertions."""
        self._should_fail_write = fail

    def set_fail_read_after_write(self, fail: bool) -> None:
        """Simulate re-retrieval failure post-write for test assertions."""
        self._should_fail_read_after_write = fail

    def search_knowledge(
        self, query: str, company_scope: str = "default"
    ) -> Optional[ObsidianDocument]:
        query_lower = query.lower()
        for doc in self._vault.values():
            if doc.metadata.get("company_scope", "default") != company_scope:
                continue
            if query_lower in doc.title.lower() or query_lower in doc.content.lower():
                return doc
        return None

    def get_document_by_id(self, document_id: str) -> Optional[ObsidianDocument]:
        if self._should_fail_read_after_write:
            return None
        return self._vault.get(document_id)

    def store_document(self, document: ObsidianDocument) -> PersistenceResult:
        if self._should_fail_write:
            return PersistenceResult(
                success=False,
                document_id=document.document_id,
                vault_path=document.vault_path,
                error_message="DEV_TEST_ERROR: Simulated Obsidian vault write failure.",
            )

        self._vault[document.document_id] = document
        return PersistenceResult(
            success=True,
            document_id=document.document_id,
            vault_path=document.vault_path,
        )


class DevTestClaudeClient(IClaudeClient):
    """
    DEV_TEST_ONLY_ADAPTER: Mock adapter for external Claude LLM boundary.
    THIS IS NOT THE REAL CLAUDE INTEGRATION.
    Used for local testing when live Anthropic Claude API is not attached.
    """

    def __init__(self) -> None:
        self._should_fail_acquisition: bool = False
        self._should_return_invalid_facts: bool = False
        self._custom_acquired_knowledge: Optional[AcquiredKnowledge] = None
        self._call_count: int = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def set_fail_acquisition(self, fail: bool) -> None:
        self._should_fail_acquisition = fail

    def set_return_invalid_facts(self, invalid: bool) -> None:
        self._should_return_invalid_facts = invalid

    def set_custom_acquired_knowledge(self, knowledge: AcquiredKnowledge) -> None:
        self._custom_acquired_knowledge = knowledge

    def fetch_external_knowledge(
        self, missing_requirement: str, task_context: str
    ) -> AcquiredKnowledge:
        self._call_count += 1

        if self._should_fail_acquisition:
            return AcquiredKnowledge(
                raw_response="API Connection Error: Unable to reach external Claude model.",
                extracted_facts=[],
                source_model="claude-3-5-sonnet",
                confidence=0.0,
                is_sufficient=False,
                unresolved_questions=[f"Could not resolve requirement: {missing_requirement}"],
            )

        if self._custom_acquired_knowledge is not None:
            return self._custom_acquired_knowledge

        if self._should_return_invalid_facts:
            return AcquiredKnowledge(
                raw_response="Unverified external speculation.",
                extracted_facts=[
                    FactItem(
                        statement="Speculative unverified claim",
                        state=FactState.ASSUMPTION,
                        source="claude_external",
                    ),
                    FactItem(
                        statement="Unknown requirement aspect",
                        state=FactState.UNKNOWN,
                        source="claude_external",
                    ),
                ],
                source_model="claude-3-5-sonnet",
                confidence=0.85,
                is_sufficient=True,
                unresolved_questions=[],
            )

        # Default valid response
        return AcquiredKnowledge(
            raw_response=f"Acquired factual knowledge for requirement '{missing_requirement}' under context '{task_context}'.",
            extracted_facts=[
                FactItem(
                    statement=f"Acquired verified fact for {missing_requirement}",
                    state=FactState.FACT,
                    source="claude_external",
                    evidence_ref=f"claude-acquisition-{uuid.uuid4().hex[:6]}",
                )
            ],
            source_model="claude-3-5-sonnet",
            confidence=0.92,
            is_sufficient=True,
            unresolved_questions=[],
        )


class DevTestMemoryKnowledgeAgent(IMemoryKnowledgeAgent):
    """
    DEV_TEST_ONLY_ADAPTER: Mock Memory/Knowledge Agent for local workflow testing.
    Uses DevTestClaudeClient as external acquisition boundary.
    """

    def __init__(self, claude_client: Optional[IClaudeClient] = None) -> None:
        self.claude_client = claude_client or DevTestClaudeClient()

    def acquire_missing_knowledge(
        self, missing_requirement: str, task_context: str
    ) -> AcquiredKnowledge:
        return self.claude_client.fetch_external_knowledge(missing_requirement, task_context)
