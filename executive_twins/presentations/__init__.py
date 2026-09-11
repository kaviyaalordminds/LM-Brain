"""
Presentation Specialist Module (Member 2 Day 2).
Provides typed presentation deck models, modular slide elements, templates,
HTML/Markdown offline renderers, builder interfaces, and registered capability handlers.
"""

from executive_twins.presentations.capability_handlers import (
    PresentationGenerationCapabilityHandler,
    PresentationValidationCapabilityHandler,
    SlideCreationCapabilityHandler,
)
from executive_twins.presentations.dev_adapters import (
    DevTestPresentationAdapter,
    PresentationBuilder,
    PresentationHTMLRenderer,
    PresentationMarkdownRenderer,
    create_presentation_specialist,
)
from executive_twins.presentations.interfaces import (
    IPresentationBuilder,
    IPresentationRenderer,
    IPresentationSpecialist,
)
from executive_twins.presentations.models import (
    ElementType,
    PresentationDeck,
    PresentationTemplate,
    Slide,
    SlideBulletListElement,
    SlideElement,
    SlideImageElement,
    SlideLayout,
    SlideMetricElement,
    SlideSpec,
    SlideTableElement,
    SlideTextElement,
)

__all__ = [
    "DevTestPresentationAdapter",
    "ElementType",
    "IPresentationBuilder",
    "IPresentationRenderer",
    "IPresentationSpecialist",
    "PresentationBuilder",
    "PresentationDeck",
    "PresentationGenerationCapabilityHandler",
    "PresentationHTMLRenderer",
    "PresentationMarkdownRenderer",
    "PresentationTemplate",
    "PresentationValidationCapabilityHandler",
    "Slide",
    "SlideBulletListElement",
    "SlideCreationCapabilityHandler",
    "SlideElement",
    "SlideImageElement",
    "SlideLayout",
    "SlideMetricElement",
    "SlideSpec",
    "SlideTableElement",
    "SlideTextElement",
    "create_presentation_specialist",
]
