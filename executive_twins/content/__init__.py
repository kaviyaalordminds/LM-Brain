"""
Content Foundation and Specialist Module.
Provides typed, provider-independent models, schemas, and interfaces for marketing copy,
blog posts, social snippets, PR announcements, renderers, validators, and specialist capability handlers.
"""

from executive_twins.content.capability_handlers import (
    ContentEditingCapabilityHandler,
    ContentGenerationCapabilityHandler,
    ContentValidationCapabilityHandler,
)
from executive_twins.content.dev_adapters import (
    ContentBuilder,
    DeterministicContentValidator,
    DevTestContentAdapter,
    HTMLContentRenderer,
    MarkdownContentRenderer,
    create_content_specialist,
)
from executive_twins.content.interfaces import (
    IContentBuilder,
    IContentRenderer,
    IContentSpecialist,
    IContentValidator,
)
from executive_twins.content.models import (
    Channel,
    ContentBrief,
    ContentMetadata,
    ContentPiece,
    ContentReviewResult,
    ContentType,
    Tone,
)

__all__ = [
    "Channel",
    "ContentBrief",
    "ContentBuilder",
    "ContentEditingCapabilityHandler",
    "ContentGenerationCapabilityHandler",
    "ContentMetadata",
    "ContentPiece",
    "ContentReviewResult",
    "ContentType",
    "ContentValidationCapabilityHandler",
    "DeterministicContentValidator",
    "DevTestContentAdapter",
    "HTMLContentRenderer",
    "IContentBuilder",
    "IContentRenderer",
    "IContentSpecialist",
    "IContentValidator",
    "MarkdownContentRenderer",
    "Tone",
    "create_content_specialist",
]
