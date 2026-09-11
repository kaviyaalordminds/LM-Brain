from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from executive_twins.content.models import (
    ContentBrief,
    ContentPiece,
    ContentReviewResult,
)


class IContentBuilder(ABC):
    """
    Provider-independent Content Builder interface.
    Enforces fluent, declarative construction of ContentPiece objects.
    """

    @abstractmethod
    def set_brief(self, brief: ContentBrief) -> "IContentBuilder":
        """Configure the builder from a structured ContentBrief."""
        pass

    @abstractmethod
    def set_title(self, title: str) -> "IContentBuilder":
        """Set content asset headline/title."""
        pass

    @abstractmethod
    def set_body(self, body: str) -> "IContentBuilder":
        """Set main content body."""
        pass

    @abstractmethod
    def add_section(self, heading: str, text: str) -> "IContentBuilder":
        """Add a named section/paragraph."""
        pass

    @abstractmethod
    def set_call_to_action(self, cta: str) -> "IContentBuilder":
        """Set call to action string."""
        pass

    @abstractmethod
    def build(self) -> ContentPiece:
        """Validate and return assembled ContentPiece."""
        pass

    @abstractmethod
    def reset(self) -> "IContentBuilder":
        """Reset internal builder state."""
        pass


class IContentRenderer(ABC):
    """
    Provider-independent Content Renderer interface.
    Transforms ContentPiece models into target string representations (Markdown / HTML).
    """

    @abstractmethod
    def render(self, content_piece: ContentPiece) -> str:
        """Render a ContentPiece into target formatted string."""
        pass


class IContentValidator(ABC):
    """
    Provider-independent Content Validator interface.
    Performs structural, tone, audience, and brief alignment checks.
    """

    @abstractmethod
    def validate(
        self,
        content_piece: ContentPiece,
        brief: Optional[ContentBrief] = None,
    ) -> ContentReviewResult:
        """Inspect and validate a ContentPiece against rules and brief."""
        pass


class IContentSpecialist(ABC):
    """
    Content Specialist Worker interface.
    Defines specialist domain contracts for synthesizing, editing, and reviewing content assets.
    """

    @abstractmethod
    def generate_content(self, brief: ContentBrief) -> ContentPiece:
        """Generate a structured content asset from a brief."""
        pass

    @abstractmethod
    def edit_content(
        self,
        content_piece: ContentPiece,
        instructions: str,
        edits: Dict[str, Any],
    ) -> ContentPiece:
        """Apply structured text modifications, refinements, or section edits."""
        pass

    @abstractmethod
    def validate_content(
        self,
        content_piece: ContentPiece,
        brief: Optional[ContentBrief] = None,
    ) -> ContentReviewResult:
        """Perform structural, tone, and brief compliance review."""
        pass
