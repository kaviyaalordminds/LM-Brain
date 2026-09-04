import pytest
from datetime import datetime, timezone

from executive_twins.memory.dev_adapters import (
    DevTestClaudeClient,
    DevTestMemoryKnowledgeAgent,
    DevTestObsidianAdapter,
)
from executive_twins.memory.knowledge_layer import CompanyKnowledgeService
from executive_twins.schemas.common import FactItem, FactState, SecurityContext
from executive_twins.schemas.knowledge import (
    AcquiredKnowledge,
    CompanyKnowledgeRequest,
    KnowledgeOutcomeStatus,
    ObsidianDocument,
)


@pytest.fixture
def memory_components():
    obsidian_adapter = DevTestObsidianAdapter()
    claude_client = DevTestClaudeClient()
    memory_agent = DevTestMemoryKnowledgeAgent(claude_client=claude_client)
    service = CompanyKnowledgeService(
        obsidian_adapter=obsidian_adapter,
        memory_agent=memory_agent,
    )
    return service, obsidian_adapter, claude_client, memory_agent


def test_1_knowledge_exists_in_obsidian(memory_components):
    """
    TEST 1: Knowledge exists in Obsidian.
    Expected:
    - Obsidian is searched.
    - Knowledge is found.
    - Claude is NOT called.
    - Knowledge is returned from Obsidian.
    """
    service, obsidian_adapter, claude_client, _ = memory_components

    # Seed Obsidian with existing verified knowledge
    seeded_doc = ObsidianDocument(
        document_id="doc-existing-100",
        vault_path="company_knowledge/default/pricing_policy.md",
        title="Verified Knowledge: pricing policy",
        content="Enterprise tier pricing is $5,000/month.",
        facts=[
            FactItem(
                statement="Enterprise tier pricing is $5,000/month",
                state=FactState.FACT,
                source="obsidian_vault",
            )
        ],
        confidence=0.98,
    )
    obsidian_adapter.seed_document(seeded_doc)

    request = CompanyKnowledgeRequest(
        request_id="req-test-1",
        task_context="CFO financial planning",
        required_knowledge="pricing policy",
        min_confidence=0.8,
    )

    response = service.request_company_knowledge(request)

    assert response.status == KnowledgeOutcomeStatus.KNOWLEDGE_FOUND
    assert response.retrieved_from_obsidian is True
    assert response.knowledge is not None
    assert response.knowledge.document_id == "doc-existing-100"
    assert response.knowledge.content == "Enterprise tier pricing is $5,000/month."
    assert claude_client.call_count == 0  # Claude NOT called


def test_2_knowledge_missing_acquisition_flow(memory_components):
    """
    TEST 2: Knowledge is missing.
    Expected:
    - Obsidian search occurs first.
    - Missing information is identified.
    - Memory/Knowledge Agent is invoked.
    - Claude boundary is invoked through the correct abstraction.
    - Acquired information is validated.
    - Information is stored in Obsidian.
    - Information is retrieved AGAIN from Obsidian.
    - The final response comes from the Obsidian retrieval.
    """
    service, obsidian_adapter, claude_client, _ = memory_components

    request = CompanyKnowledgeRequest(
        request_id="req-test-2",
        task_context="CTO architecture review",
        required_knowledge="disaster recovery SLA",
        min_confidence=0.8,
    )

    response = service.request_company_knowledge(request)

    assert response.status == KnowledgeOutcomeStatus.KNOWLEDGE_FOUND
    assert response.retrieved_from_obsidian is True
    assert response.knowledge is not None
    assert claude_client.call_count == 1  # External acquisition triggered
    assert "disaster recovery SLA" in response.knowledge.title

    # Verify that the document now exists in Obsidian vault and matches final response
    obsidian_doc = obsidian_adapter.get_document_by_id(response.knowledge.document_id)
    assert obsidian_doc is not None
    assert obsidian_doc.document_id == response.knowledge.document_id


def test_3_claude_acquisition_fails(memory_components):
    """
    TEST 3: Claude/knowledge acquisition fails.
    Expected:
    - No fake knowledge is returned.
    - Failure is explicit (ACQUISITION_FAILED).
    """
    service, obsidian_adapter, claude_client, _ = memory_components
    claude_client.set_fail_acquisition(True)

    request = CompanyKnowledgeRequest(
        request_id="req-test-3",
        task_context="CMO campaign strategy",
        required_knowledge="unknown market trend",
    )

    response = service.request_company_knowledge(request)

    assert response.status == KnowledgeOutcomeStatus.ACQUISITION_FAILED
    assert response.knowledge is None
    assert response.retrieved_from_obsidian is False
    assert "failed" in response.error_message.lower()


def test_4_validation_fails(memory_components):
    """
    TEST 4: Validation fails.
    Expected:
    - Invalid information is not stored.
    - Failure is explicit (VALIDATION_FAILED).
    """
    service, obsidian_adapter, claude_client, _ = memory_components
    claude_client.set_return_invalid_facts(True)

    request = CompanyKnowledgeRequest(
        request_id="req-test-4",
        task_context="Legal audit",
        required_knowledge="unsubstantiated rumor",
    )

    response = service.request_company_knowledge(request)

    assert response.status == KnowledgeOutcomeStatus.VALIDATION_FAILED
    assert response.knowledge is None
    assert response.retrieved_from_obsidian is False
    # Ensure nothing was stored in Obsidian
    assert obsidian_adapter.search_knowledge("unsubstantiated rumor") is None


def test_5_obsidian_write_fails(memory_components):
    """
    TEST 5: Obsidian write fails.
    Expected:
    - System does not claim persistence.
    - Knowledge is not returned as persisted company knowledge (PERSISTENCE_FAILED).
    """
    service, obsidian_adapter, claude_client, _ = memory_components
    obsidian_adapter.set_fail_write(True)

    request = CompanyKnowledgeRequest(
        request_id="req-test-5",
        task_context="COO operations check",
        required_knowledge="warehouse address",
    )

    response = service.request_company_knowledge(request)

    assert response.status == KnowledgeOutcomeStatus.PERSISTENCE_FAILED
    assert response.knowledge is None
    assert response.retrieved_from_obsidian is False
    assert "Persistence into Obsidian failed" in response.error_message


def test_6_obsidian_retrieval_after_successful_write_fails(memory_components):
    """
    TEST 6: Obsidian retrieval after successful write fails.
    Expected:
    - System does not directly return the Claude response.
    - Retrieval failure is explicit (RETRIEVAL_FAILED).
    """
    service, obsidian_adapter, claude_client, _ = memory_components
    obsidian_adapter.set_fail_read_after_write(True)

    request = CompanyKnowledgeRequest(
        request_id="req-test-6",
        task_context="Executive inquiry",
        required_knowledge="compliance framework",
    )

    response = service.request_company_knowledge(request)

    assert response.status == KnowledgeOutcomeStatus.RETRIEVAL_FAILED
    assert response.knowledge is None
    assert response.retrieved_from_obsidian is False
    assert "Re-retrieval from Obsidian failed" in response.error_message


def test_7_attempt_to_bypass_obsidian(memory_components):
    """
    TEST 7: Attempt to bypass Obsidian.
    Expected:
    - Architecture/test prevents direct external knowledge from being returned as final company knowledge.
    - Any successful response MUST have retrieved_from_obsidian=True and provenance_source='company_obsidian'.
    """
    service, obsidian_adapter, claude_client, _ = memory_components

    request = CompanyKnowledgeRequest(
        request_id="req-test-7",
        task_context="Bypass test",
        required_knowledge="security key policy",
    )

    response = service.request_company_knowledge(request)

    # Verification: Response MUST be retrieved from Obsidian
    assert response.status == KnowledgeOutcomeStatus.KNOWLEDGE_FOUND
    assert response.retrieved_from_obsidian is True
    assert response.provenance_source == "company_obsidian"
    assert response.knowledge is not None


def test_8_existing_obsidian_knowledge_is_sufficient(memory_components):
    """
    TEST 8: Existing Obsidian knowledge is sufficient.
    Expected:
    - No unnecessary external knowledge acquisition.
    - Claude client call_count is zero.
    """
    service, obsidian_adapter, claude_client, _ = memory_components

    doc = ObsidianDocument(
        document_id="doc-sufficient-1",
        vault_path="company_knowledge/default/datacenter_location.md",
        title="Verified Knowledge: datacenter location",
        content="Primary datacenter is located in us-east-1.",
        facts=[
            FactItem(
                statement="Primary datacenter is in us-east-1",
                state=FactState.FACT,
                source="obsidian_vault",
            )
        ],
        confidence=0.95,
    )
    obsidian_adapter.seed_document(doc)

    request = CompanyKnowledgeRequest(
        request_id="req-test-8",
        task_context="Infrastructure audit",
        required_knowledge="datacenter location",
        min_confidence=0.8,
    )

    response = service.request_company_knowledge(request)

    assert response.status == KnowledgeOutcomeStatus.KNOWLEDGE_FOUND
    assert response.retrieved_from_obsidian is True
    assert response.knowledge.document_id == "doc-sufficient-1"
    assert claude_client.call_count == 0  # No external acquisition calls
