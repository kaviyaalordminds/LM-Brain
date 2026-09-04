from abc import ABC, abstractmethod
from typing import Optional

from executive_twins.schemas.knowledge import (
    AcquiredKnowledge,
    CompanyKnowledgeRequest,
    CompanyKnowledgeResponse,
    ObsidianDocument,
    PersistenceResult,
)


class IObsidianAdapter(ABC):
    """
    Authoritative abstraction for Company Obsidian vault storage and retrieval.
    All persistent company knowledge operations MUST pass through this interface.
    """

    @abstractmethod
    def search_knowledge(
        self, query: str, company_scope: str = "default"
    ) -> Optional[ObsidianDocument]:
        """Search Company Obsidian for existing verified document matching query."""
        pass

    @abstractmethod
    def get_document_by_id(self, document_id: str) -> Optional[ObsidianDocument]:
        """Retrieve a specific document from Company Obsidian by ID."""
        pass

    @abstractmethod
    def store_document(self, document: ObsidianDocument) -> PersistenceResult:
        """Persist a validated document into Company Obsidian vault."""
        pass


class IClaudeClient(ABC):
    """
    External Claude knowledge acquisition interface.
    Integration Boundary: Claude is ONLY used to fetch missing information when Obsidian search fails.
    Claude is NOT a persistent company knowledge source.
    """

    @abstractmethod
    def fetch_external_knowledge(
        self, missing_requirement: str, task_context: str
    ) -> AcquiredKnowledge:
        """Fetch raw external knowledge candidate from Claude model boundary."""
        pass


class IMemoryKnowledgeAgent(ABC):
    """
    Memory/Knowledge Agent interface responsible for acquiring missing information
    via external sources (Claude) when Company Obsidian lacks sufficient information.
    """

    @abstractmethod
    def acquire_missing_knowledge(
        self, missing_requirement: str, task_context: str
    ) -> AcquiredKnowledge:
        """Acquire candidate knowledge for missing information requirements."""
        pass


class IKnowledgeMemoryLayer(ABC):
    """
    Main Company Knowledge / Memory Abstraction Layer interface exposed to requesting agents.
    Requesting agents MUST interact only with this interface and MUST NOT directly access
    Obsidian or Claude implementations.
    """

    @abstractmethod
    def request_company_knowledge(
        self, request: CompanyKnowledgeRequest
    ) -> CompanyKnowledgeResponse:
        """
        Request verified company knowledge for a task context.
        Enforces Obsidian-first retrieval, missing-knowledge acquisition via Memory Agent & Claude,
        validation, persistence into Obsidian, and re-retrieval from Obsidian.
        """
        pass
