from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field, field_validator


class SlideLayout(str, Enum):
    """Supported slide structural layouts."""
    TITLE = "TITLE"
    SECTION_HEADER = "SECTION_HEADER"
    TITLE_AND_CONTENT = "TITLE_AND_CONTENT"
    TWO_COLUMN = "TWO_COLUMN"
    METRIC_CARD = "METRIC_CARD"
    TABLE_SLIDE = "TABLE_SLIDE"
    BLANK = "BLANK"


class ElementType(str, Enum):
    """Types of modular slide elements."""
    TEXT = "TEXT"
    BULLET_LIST = "BULLET_LIST"
    TABLE = "TABLE"
    IMAGE_REF = "IMAGE_REF"
    METRIC = "METRIC"
    CALLOUT = "CALLOUT"
    CODE = "CODE"


class SlideElement(BaseModel):
    """
    Base element for all slide content blocks.
    Enforces deterministic ordering and unique element identification.
    """
    element_id: str = Field(default_factory=lambda: f"el_{uuid.uuid4().hex[:8]}")
    element_type: ElementType
    order_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("element_id")
    @classmethod
    def validate_element_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("element_id cannot be empty.")
        return v.strip()


class SlideTextElement(SlideElement):
    """Text content element on a slide."""
    element_type: ElementType = ElementType.TEXT
    content: str
    font_size: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False


class SlideBulletListElement(SlideElement):
    """Ordered or unordered bullet list element."""
    element_type: ElementType = ElementType.BULLET_LIST
    items: List[str] = Field(default_factory=list)
    is_ordered: bool = False


class SlideTableElement(SlideElement):
    """Structured tabular data element for slides."""
    element_type: ElementType = ElementType.TABLE
    headers: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    caption: Optional[str] = None


class SlideImageElement(SlideElement):
    """
    Pointer / reference to an image asset.
    Does NOT load binary image data into the domain model.
    """
    element_type: ElementType = ElementType.IMAGE_REF
    uri: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Image URI cannot be empty.")
        return v.strip()


class SlideMetricElement(SlideElement):
    """Key metric / KPI callout element."""
    element_type: ElementType = ElementType.METRIC
    label: str
    value: str
    delta: Optional[str] = None
    description: Optional[str] = None

    @field_validator("label", "value")
    @classmethod
    def validate_metric_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Metric label and value cannot be empty.")
        return v.strip()


# Polymorphic element union for deserialization
SlideElementItem = Union[
    SlideTextElement,
    SlideBulletListElement,
    SlideTableElement,
    SlideImageElement,
    SlideMetricElement,
    SlideElement,
]


class Slide(BaseModel):
    """
    Structured Slide model.
    Contains slide identity, layout, ordered elements, and optional speaker notes.
    """
    slide_id: str = Field(default_factory=lambda: f"slide_{uuid.uuid4().hex[:8]}")
    title: str
    layout: SlideLayout = SlideLayout.TITLE_AND_CONTENT
    elements: List[SlideElementItem] = Field(default_factory=list)
    speaker_notes: Optional[str] = None
    order_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("slide_id")
    @classmethod
    def validate_slide_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("slide_id cannot be empty.")
        return v.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Slide title cannot be empty.")
        return v.strip()

    def add_element(self, element: SlideElement) -> "Slide":
        """Append an element with deterministic order index."""
        element.order_index = len(self.elements)
        self.elements.append(element)
        return self


class PresentationDeck(BaseModel):
    """
    Authoritative Presentation Deck model.
    Encapsulates presentation metadata, aspect ratio, theme, and ordered slides.
    """
    presentation_id: str = Field(default_factory=lambda: f"pres_{uuid.uuid4().hex[:8]}")
    title: str
    subtitle: Optional[str] = None
    aspect_ratio: str = "16:9"
    theme: str = "modern_dark"
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    slides: List[Slide] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("presentation_id")
    @classmethod
    def validate_presentation_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("presentation_id cannot be empty.")
        return v.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Presentation title cannot be empty.")
        return v.strip()

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        v_clean = v.strip()
        if v_clean not in ("16:9", "4:3", "16:10"):
            return "16:9"
        return v_clean

    def add_slide(self, slide: Slide) -> "PresentationDeck":
        """Append a slide with deterministic order index."""
        slide.order_index = len(self.slides)
        self.slides.append(slide)
        return self

    def get_all_elements(self) -> List[SlideElement]:
        """Collect all elements across all slides in order."""
        elements: List[SlideElement] = []
        for s in self.slides:
            elements.extend(s.elements)
        return elements


class SlideSpec(BaseModel):
    """Blueprint specification for a slide in a presentation template."""
    title_template: str
    layout: SlideLayout = SlideLayout.TITLE_AND_CONTENT
    default_elements: List[SlideElementItem] = Field(default_factory=list)
    speaker_notes_template: Optional[str] = None
    description: Optional[str] = None


class PresentationTemplate(BaseModel):
    """
    Reusable Presentation blueprint / template.
    Enforces required template variables and safe deterministic instantiation.
    """
    template_id: str = Field(default_factory=lambda: f"ptmpl_{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    aspect_ratio: str = "16:9"
    theme: str = "modern_dark"
    required_variables: List[str] = Field(default_factory=list)
    slide_specs: List[SlideSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty.")
        return v.strip()

    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Return list of missing required variable names."""
        return [v for v in self.required_variables if v not in variables]

    def instantiate(
        self,
        title: str,
        subtitle: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> PresentationDeck:
        """Instantiate a structured PresentationDeck from this template."""
        vars_map = variables or {}
        missing = self.validate_variables(vars_map)
        if missing:
            raise ValueError(f"Missing required template variables: {', '.join(missing)}")

        deck = PresentationDeck(
            title=title,
            subtitle=subtitle,
            aspect_ratio=self.aspect_ratio,
            theme=self.theme,
            metadata=dict(self.metadata),
        )

        for idx, spec in enumerate(self.slide_specs):
            rendered_title = spec.title_template
            for k, val in vars_map.items():
                rendered_title = rendered_title.replace(f"{{{k}}}", str(val))

            rendered_notes: Optional[str] = None
            if spec.speaker_notes_template:
                rendered_notes = spec.speaker_notes_template
                for k, val in vars_map.items():
                    rendered_notes = rendered_notes.replace(f"{{{k}}}", str(val))

            elements: List[SlideElement] = []
            for el in spec.default_elements:
                el_copy = el.model_copy(deep=True)
                if isinstance(el_copy, SlideTextElement):
                    for k, val in vars_map.items():
                        el_copy.content = el_copy.content.replace(f"{{{k}}}", str(val))
                elements.append(el_copy)

            slide = Slide(
                title=rendered_title,
                layout=spec.layout,
                elements=elements,
                speaker_notes=rendered_notes,
                order_index=idx,
            )
            deck.add_slide(slide)

        return deck
