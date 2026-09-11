from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from executive_twins.documents.models import (
    Document,
    DocumentBlock,
    DocumentMetadata,
    DocumentSection,
)


class IDocumentBuilder(ABC):
    """
    Provider-independent Document Builder interface.
    Enforces fluent, declarative construction of typed Document objects.
    """

    @abstractmethod
    def set_title(self, title: str) -> "IDocumentBuilder":
        """Set the root document title."""
        pass

    @abstractmethod
    def set_metadata(self, metadata: DocumentMetadata) -> "IDocumentBuilder":
        """Set or overwrite document metadata."""
        pass

    @abstractmethod
    def add_heading(self, text: str, level: int = 1) -> "IDocumentBuilder":
        """Add a heading block at current scope."""
        pass

    @abstractmethod
    def add_paragraph(self, text: str) -> "IDocumentBuilder":
        """Add a paragraph block at current scope."""
        pass

    @abstractmethod
    def add_table(
        self,
        headers: List[str],
        rows: List[List[Any]],
        caption: Optional[str] = None,
    ) -> "IDocumentBuilder":
        """Add a tabular block at current scope."""
        pass

    @abstractmethod
    def add_image_ref(
        self,
        uri: str,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> "IDocumentBuilder":
        """Add an image asset reference block at current scope."""
        pass

    @abstractmethod
    def add_block(self, block: DocumentBlock) -> "IDocumentBuilder":
        """Add a generic or custom DocumentBlock at current scope."""
        pass

    @abstractmethod
    def add_section(self, section: DocumentSection) -> "IDocumentBuilder":
        """Add a structured section."""
        pass

    @abstractmethod
    def build(self) -> Document:
        """Validate and return the assembled Document instance."""
        pass

    @abstractmethod
    def reset(self) -> "IDocumentBuilder":
        """Clear internal builder state for reuse."""
        pass


class IDocumentParser(ABC):
    """
    Provider-independent Document Parser interface.
    Converts raw text/data strings into structured Document models.
    """

    @abstractmethod
    def parse(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Parse structured content into a Document instance."""
        pass


class IDocumentRenderer(ABC):
    """
    Provider-independent Document Renderer interface.
    Transforms structured Document models into target string/representation.
    """

    @abstractmethod
    def render(self, document: Document) -> str:
        """Render a Document instance into target text format."""
        pass


class IDocumentSpecialist(ABC):
    """
    Document Specialist Worker interface.
    Defines specialist domain contracts for synthesizing, editing, and validating documents.
    """

    @abstractmethod
    def synthesize_document(
        self,
        title: str,
        topic: str,
        outline: Optional[List[Dict[str, Any]]] = None,
    ) -> Document:
        """Synthesize a structured document from intent/outline."""
        pass

    @abstractmethod
    def edit_document(
        self,
        document: Document,
        instructions: str,
        edits: Dict[str, Any],
    ) -> Document:
        """Apply structured modifications and revisions to an existing document."""
        pass

    @abstractmethod
    def validate_document(
        self,
        document: Document,
    ) -> Dict[str, Any]:
        """Validate structural integrity, hierarchy, and schema compliance of a document."""
        pass

