"""
Document Foundation Module.
Provides typed, provider-independent models, schemas, and interfaces for document representation,
composition, templating, and rendering.
"""

from executive_twins.documents.interfaces import (
    IDocumentBuilder,
    IDocumentParser,
    IDocumentRenderer,
    IDocumentSpecialist,
)
from executive_twins.documents.models import (
    BlockType,
    BreakBlock,
    BreakType,
    CodeBlock,
    Document,
    DocumentBlock,
    DocumentFormat,
    DocumentMetadata,
    DocumentSection,
    DocumentTemplate,
    HeadingBlock,
    ImageRefBlock,
    ListBlock,
    ParagraphBlock,
    SectionSpec,
    TableBlock,
    TableCell,
    TableRow,
)
from executive_twins.documents.dev_adapters import (
    DevTestDocumentAdapter,
    DocumentBuilder,
    MarkdownDocumentParser,
    MarkdownDocumentRenderer,
    create_document_specialist,
)
from executive_twins.documents.capability_handlers import (
    DocumentEditingCapabilityHandler,
    DocumentGenerationCapabilityHandler,
    DocumentValidationCapabilityHandler,
)

__all__ = [
    "BlockType",
    "BreakBlock",
    "BreakType",
    "CodeBlock",
    "DevTestDocumentAdapter",
    "Document",
    "DocumentBlock",
    "DocumentBuilder",
    "DocumentEditingCapabilityHandler",
    "DocumentFormat",
    "DocumentGenerationCapabilityHandler",
    "DocumentMetadata",
    "DocumentSection",
    "DocumentTemplate",
    "DocumentValidationCapabilityHandler",
    "HeadingBlock",
    "IDocumentBuilder",
    "IDocumentParser",
    "IDocumentRenderer",
    "IDocumentSpecialist",
    "ImageRefBlock",
    "ListBlock",
    "MarkdownDocumentParser",
    "MarkdownDocumentRenderer",
    "ParagraphBlock",
    "SectionSpec",
    "TableBlock",
    "TableCell",
    "TableRow",
    "create_document_specialist",
]

