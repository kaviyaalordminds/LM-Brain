from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from executive_twins.presentations.models import (
    PresentationDeck,
    Slide,
    SlideElement,
    SlideLayout,
)


class IPresentationBuilder(ABC):
    """
    Provider-independent Presentation Builder interface.
    Provides fluent, declarative construction of typed PresentationDeck models.
    """

    @abstractmethod
    def set_title(self, title: str) -> "IPresentationBuilder":
        """Set presentation root title."""
        pass

    @abstractmethod
    def set_subtitle(self, subtitle: str) -> "IPresentationBuilder":
        """Set presentation subtitle."""
        pass

    @abstractmethod
    def set_aspect_ratio(self, aspect_ratio: str) -> "IPresentationBuilder":
        """Set deck aspect ratio (e.g. '16:9', '4:3')."""
        pass

    @abstractmethod
    def set_theme(self, theme: str) -> "IPresentationBuilder":
        """Set visual styling theme."""
        pass

    @abstractmethod
    def add_slide(self, slide: Slide) -> "IPresentationBuilder":
        """Append pre-constructed Slide object."""
        pass

    @abstractmethod
    def create_slide(
        self,
        title: str,
        layout: SlideLayout = SlideLayout.TITLE_AND_CONTENT,
        speaker_notes: Optional[str] = None,
    ) -> "IPresentationBuilder":
        """Start a new slide scope."""
        pass

    @abstractmethod
    def add_text(
        self,
        content: str,
        font_size: Optional[str] = None,
        is_bold: bool = False,
    ) -> "IPresentationBuilder":
        """Add text element to current active slide."""
        pass

    @abstractmethod
    def add_bullet_list(
        self,
        items: List[str],
        is_ordered: bool = False,
    ) -> "IPresentationBuilder":
        """Add bullet list to current active slide."""
        pass

    @abstractmethod
    def add_table(
        self,
        headers: List[str],
        rows: List[List[Any]],
        caption: Optional[str] = None,
    ) -> "IPresentationBuilder":
        """Add table element to current active slide."""
        pass

    @abstractmethod
    def add_image(
        self,
        uri: str,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> "IPresentationBuilder":
        """Add image reference to current active slide."""
        pass

    @abstractmethod
    def add_metric(
        self,
        label: str,
        value: str,
        delta: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "IPresentationBuilder":
        """Add metric card element to current active slide."""
        pass

    @abstractmethod
    def build(self) -> PresentationDeck:
        """Validate and return assembled PresentationDeck."""
        pass

    @abstractmethod
    def reset(self) -> "IPresentationBuilder":
        """Reset internal builder state."""
        pass


class IPresentationRenderer(ABC):
    """
    Provider-independent Presentation Renderer interface.
    Transforms PresentationDeck models into inspectable string representations (HTML / Markdown).
    """

    @abstractmethod
    def render(self, deck: PresentationDeck) -> str:
        """Render presentation deck into target string format."""
        pass


class IPresentationSpecialist(ABC):
    """
    Presentation Specialist Worker interface.
    Defines specialist domain contracts for synthesizing and validating slide decks.
    """

    @abstractmethod
    def synthesize_presentation(
        self,
        title: str,
        topic: str,
        outline: Optional[List[Dict[str, Any]]] = None,
    ) -> PresentationDeck:
        """Synthesize a complete presentation deck from intent/outline."""
        pass

    @abstractmethod
    def validate_presentation(
        self,
        deck: PresentationDeck,
    ) -> Dict[str, Any]:
        """Validate structural integrity, ordering, and readability of presentation deck."""
        pass
