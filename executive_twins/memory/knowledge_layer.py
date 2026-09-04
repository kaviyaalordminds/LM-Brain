from typing import Optional, List
import uuid

from executive_twins.memory.interfaces import (
    IClaudeClient,
    IKnowledgeMemoryLayer,
    IMemoryKnowledgeAgent,
    IObsidianAdapter,
)
from executive_twins.schemas.common import FactItem, FactState
from executive_twins.schemas.knowledge import (
    AcquiredKnowledge,
    CompanyKnowledgeRequest,
    CompanyKnowledgeResponse,
    KnowledgeOutcomeStatus,
    ObsidianDocument,
    ValidationResult,
)
from executive_twins.utils.audit_logger import AuditLogger


class CompanyKnowledgeService(IKnowledgeMemoryLayer):
    """
    Authoritative implementation of Company Knowledge / Memory Abstraction Layer.
    
    PRIMARY DESIGN PRINCIPLE:
    Requesting agents interact ONLY with this service abstraction.
    Obsidian is the ONLY permanent company knowledge source.
    Claude is an external acquisition source used ONLY when required information is missing from Obsidian.
    
    AUTHORITATIVE FLOW:
    Request -> Search Obsidian FIRST ->
      If found & sufficient: return Obsidian knowledge
      If missing:
        Memory/Knowledge Agent (Claude boundary) ->
        validate acquired knowledge ->
        store validated knowledge in Obsidian ->
        re-retrieve from Obsidian ->
        return ONLY re-retrieved Obsidian knowledge.
    """

    def __init__(
        self,
        obsidian_adapter: IObsidianAdapter,
        memory_agent: IMemoryKnowledgeAgent,
    ) -> None:
        self.obsidian_adapter = obsidian_adapter
        self.memory_agent = memory_agent

    def validate_acquired_knowledge(
        self, acquired: AcquiredKnowledge, request: CompanyKnowledgeRequest
    ) -> ValidationResult:
        """
        Validate acquired candidate knowledge before persistence into Obsidian.
        Rules:
        1. Response must be marked sufficient by acquisition source.
        2. Extracted facts must not be empty.
        3. Facts must include at least one verified FACT (assumptions/inferences are not silently converted to facts).
        4. Overall confidence must meet or exceed request.min_confidence.
        """
        if not acquired.is_sufficient or acquired.confidence < request.min_confidence:
            return ValidationResult(
                is_valid=False,
                validated_facts=[],
                validation_notes=["Insufficient confidence or acquired knowledge marked incomplete."],
                rejected_reasons=[f"Confidence {acquired.confidence} below required threshold {request.min_confidence}"],
            )

        valid_facts: List[FactItem] = []
        rejected_reasons: List[str] = []

        for fact in acquired.extracted_facts:
            # Explicitly check FactState - do not convert ASSUMPTION or UNKNOWN into FACT
            if fact.state == FactState.FACT:
                valid_facts.append(fact)
            elif fact.state in (FactState.ASSUMPTION, FactState.INFERENCE, FactState.UNKNOWN):
                rejected_reasons.append(
                    f"Fact statement '{fact.statement}' rejected from core fact registry due to non-factual state '{fact.state}'."
                )

        if not valid_facts:
            return ValidationResult(
                is_valid=False,
                validated_facts=[],
                validation_notes=["No verified FACT entries found in acquired payload."],
                rejected_reasons=rejected_reasons or ["Acquired knowledge contains zero verified facts."],
            )

        return ValidationResult(
            is_valid=True,
            validated_facts=valid_facts,
            validation_notes=[f"Validated {len(valid_facts)} fact(s) for Obsidian persistence."],
            rejected_reasons=rejected_reasons,
        )

    def request_company_knowledge(
        self, request: CompanyKnowledgeRequest
    ) -> CompanyKnowledgeResponse:
        AuditLogger.log_event(
            "knowledge.request.received",
            {"request_id": request.request_id, "required_knowledge": request.required_knowledge},
        )

        # STEP 1: Search Company Obsidian FIRST
        existing_doc = self.obsidian_adapter.search_knowledge(
            query=request.required_knowledge, company_scope=request.company_scope
        )

        # STEP 2: Evaluate retrieved knowledge sufficiency
        if existing_doc and existing_doc.confidence >= request.min_confidence:
            AuditLogger.log_event(
                "knowledge.obsidian.hit",
                {"request_id": request.request_id, "document_id": existing_doc.document_id},
            )
            return CompanyKnowledgeResponse(
                request_id=request.request_id,
                status=KnowledgeOutcomeStatus.KNOWLEDGE_FOUND,
                knowledge=existing_doc,
                facts=existing_doc.facts,
                provenance_source="company_obsidian",
                retrieved_from_obsidian=True,
            )

        AuditLogger.log_event(
            "knowledge.obsidian.miss",
            {"request_id": request.request_id, "required_knowledge": request.required_knowledge},
        )

        # STEP 3: Knowledge missing -> Invoke Memory/Knowledge Agent (Claude boundary)
        acquired = self.memory_agent.acquire_missing_knowledge(
            missing_requirement=request.required_knowledge,
            task_context=request.task_context,
        )

        if not acquired.is_sufficient or acquired.confidence == 0.0:
            AuditLogger.log_event(
                "knowledge.acquisition.failed",
                {"request_id": request.request_id},
            )
            return CompanyKnowledgeResponse(
                request_id=request.request_id,
                status=KnowledgeOutcomeStatus.ACQUISITION_FAILED,
                knowledge=None,
                facts=[],
                provenance_source="external_acquisition",
                retrieved_from_obsidian=False,
                error_message="External knowledge acquisition failed via Memory Agent.",
            )

        # STEP 4: Validate acquired knowledge before persistence
        val_result = self.validate_acquired_knowledge(acquired, request)
        if not val_result.is_valid:
            AuditLogger.log_event(
                "knowledge.validation.failed",
                {"request_id": request.request_id, "reasons": val_result.rejected_reasons},
            )
            return CompanyKnowledgeResponse(
                request_id=request.request_id,
                status=KnowledgeOutcomeStatus.VALIDATION_FAILED,
                knowledge=None,
                facts=[],
                provenance_source="external_acquisition",
                retrieved_from_obsidian=False,
                error_message=f"Acquired knowledge validation failed: {'; '.join(val_result.rejected_reasons)}",
            )

        # STEP 5: Store validated knowledge in Company Obsidian
        doc_id = f"doc-obs-{uuid.uuid4().hex[:8]}"
        slug = request.required_knowledge.lower().replace(" ", "_")
        vault_path = f"company_knowledge/{request.company_scope}/{slug}.md"

        new_doc = ObsidianDocument(
            document_id=doc_id,
            vault_path=vault_path,
            title=f"Verified Knowledge: {request.required_knowledge}",
            content=acquired.raw_response,
            facts=val_result.validated_facts,
            metadata={
                "company_scope": request.company_scope,
                "acquired_from": acquired.source_model,
                "acquired_context": request.task_context,
            },
            confidence=acquired.confidence,
        )

        store_result = self.obsidian_adapter.store_document(new_doc)
        if not store_result.success or not store_result.document_id:
            AuditLogger.log_event(
                "knowledge.persistence.failed",
                {"request_id": request.request_id, "error": store_result.error_message},
            )
            return CompanyKnowledgeResponse(
                request_id=request.request_id,
                status=KnowledgeOutcomeStatus.PERSISTENCE_FAILED,
                knowledge=None,
                facts=[],
                provenance_source="company_obsidian",
                retrieved_from_obsidian=False,
                error_message=f"Persistence into Obsidian failed: {store_result.error_message}",
            )

        # STEP 6: CRITICAL REQUIREMENT — RE-RETRIEVE FROM OBSIDIAN
        # Do NOT return raw Claude/acquired object directly to agent.
        re_retrieved_doc = self.obsidian_adapter.get_document_by_id(store_result.document_id)

        if re_retrieved_doc is None:
            AuditLogger.log_event(
                "knowledge.re_retrieval.failed",
                {"request_id": request.request_id, "document_id": store_result.document_id},
            )
            return CompanyKnowledgeResponse(
                request_id=request.request_id,
                status=KnowledgeOutcomeStatus.RETRIEVAL_FAILED,
                knowledge=None,
                facts=[],
                provenance_source="company_obsidian",
                retrieved_from_obsidian=False,
                error_message="Re-retrieval from Obsidian failed post-write.",
            )

        AuditLogger.log_event(
            "knowledge.re_retrieved.success",
            {"request_id": request.request_id, "document_id": re_retrieved_doc.document_id},
        )

        # STEP 7: Return re-retrieved document from Obsidian
        return CompanyKnowledgeResponse(
            request_id=request.request_id,
            status=KnowledgeOutcomeStatus.KNOWLEDGE_FOUND,
            knowledge=re_retrieved_doc,
            facts=re_retrieved_doc.facts,
            provenance_source="company_obsidian",
            retrieved_from_obsidian=True,
        )
