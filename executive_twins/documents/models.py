from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, field_validator


class DocumentFormat(str, Enum):
    """Supported logical document formats."""
    MARKDOWN = "MARKDOWN"
    PLAIN_TEXT = "PLAIN_TEXT"
    HTML = "HTML"
    REPORT = "REPORT"
    SPECIFICATION = "SPECIFICATION"
    MEMO = "MEMO"
    STRUCTURED_DATA = "STRUCTURED_DATA"
    GENERIC = "GENERIC"


class BlockType(str, Enum):
    """Types of modular document blocks."""
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    TABLE = "TABLE"
    IMAGE_REF = "IMAGE_REF"
    BREAK = "BREAK"
    CODE = "CODE"
    LIST = "LIST"


class BreakType(str, Enum):
    """Types of document breaks."""
    PAGE_BREAK = "PAGE_BREAK"
    SECTION_BREAK = "SECTION_BREAK"
    LINE_BREAK = "LINE_BREAK"


class DocumentMetadata(BaseModel):
    """
    Extensible metadata container for document instances.
    Provides provenance, versioning, formatting tags, and custom attributes.
    """
    document_format: DocumentFormat = DocumentFormat.MARKDOWN
    author: Optional[str] = None
    source: Optional[str] = None
    version: str = "1.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)


class DocumentBlock(BaseModel):
    """
    Abstract base block for all structured document elements.
    Maintains deterministic ordering and unique block identification.
    """
    block_id: str = Field(default_factory=lambda: f"blk_{uuid.uuid4().hex[:8]}")
    block_type: BlockType
    order_index: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("block_id")
    @classmethod
    def validate_block_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("block_id cannot be empty.")
        return v.strip()


class HeadingBlock(DocumentBlock):
    """Structured heading block with explicit hierarchy level (1-6)."""
    block_type: BlockType = BlockType.HEADING
    text: str
    level: int = Field(default=1, ge=1, le=6)

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Heading text cannot be empty.")
        return v.strip()


class ParagraphBlock(DocumentBlock):
    """Standard paragraph text block."""
    block_type: BlockType = BlockType.PARAGRAPH
    text: str = ""


class TableCell(BaseModel):
    """Individual table cell with alignment and header flags."""
    content: str = ""
    align: str = "left"  # left, center, right
    is_header: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("align")
    @classmethod
    def validate_align(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in ("left", "center", "right"):
            return "left"
        return v_clean


class TableRow(BaseModel):
    """Ordered row of table cells."""
    cells: List[TableCell] = Field(default_factory=list)

    @classmethod
    def from_values(cls, values: List[Any], is_header: bool = False) -> "TableRow":
        """Convenience constructor from raw scalar values."""
        cells = [
            TableCell(content=str(v), is_header=is_header) for v in values
        ]
        return cls(cells=cells)


class TableBlock(DocumentBlock):
    """
    Structured tabular data block with headers and row data.
    """
    block_type: BlockType = BlockType.TABLE
    headers: List[str] = Field(default_factory=list)
    rows: List[TableRow] = Field(default_factory=list)
    caption: Optional[str] = None

    @classmethod
    def create(
        cls,
        headers: List[str],
        rows_data: List[List[Any]],
        caption: Optional[str] = None,
        block_id: Optional[str] = None,
        order_index: int = 0,
    ) -> "TableBlock":
        """Factory method creating a TableBlock from 2D arrays."""
        table_rows: List[TableRow] = []
        for r in rows_data:
            if isinstance(r, TableRow):
                table_rows.append(r)
            elif isinstance(r, list):
                table_rows.append(TableRow.from_values(r))
        kwargs: Dict[str, Any] = {
            "headers": [str(h) for h in headers],
            "rows": table_rows,
            "caption": caption,
            "order_index": order_index,
        }
        if block_id:
            kwargs["block_id"] = block_id
        return cls(**kwargs)


class ImageRefBlock(DocumentBlock):
    """
    Reference/pointer to an image asset.
    Does NOT load or mutate binary image data directly.
    """
    block_type: BlockType = BlockType.IMAGE_REF
    uri: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ImageRefBlock URI cannot be empty.")
        return v.strip()


class BreakBlock(DocumentBlock):
    """Structural page or section break."""
    block_type: BlockType = BlockType.BREAK
    break_type: BreakType = BreakType.SECTION_BREAK


class CodeBlock(DocumentBlock):
    """Source code snippet or formatted programmatic block."""
    block_type: BlockType = BlockType.CODE
    code: str
    language: Optional[str] = None


class ListBlock(DocumentBlock):
    """Ordered or unordered bullet list block."""
    block_type: BlockType = BlockType.LIST
    items: List[str] = Field(default_factory=list)
    is_ordered: bool = False


class DocumentSection(BaseModel):
    """
    Hierarchical section organizing child blocks and optional subsections.
    """
    section_id: str = Field(default_factory=lambda: f"sec_{uuid.uuid4().hex[:8]}")
    title: str
    level: int = Field(default=1, ge=1, le=6)
    order_index: int = 0
    blocks: List[DocumentBlock] = Field(default_factory=list)
    subsections: List["DocumentSection"] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("section_id")
    @classmethod
    def validate_section_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("section_id cannot be empty.")
        return v.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Section title cannot be empty.")
        return v.strip()

    def add_block(self, block: DocumentBlock) -> "DocumentSection":
        """Add block preserving relative order index."""
        block.order_index = len(self.blocks)
        self.blocks.append(block)
        return self

    def add_subsection(self, subsection: "DocumentSection") -> "DocumentSection":
        """Add nested subsection."""
        subsection.order_index = len(self.subsections)
        subsection.level = self.level + 1
        self.subsections.append(subsection)
        return self


class Document(BaseModel):
    """
    Authoritative Root Document model.
    Pure provider-independent representation of a structured document.
    """
    document_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    title: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    blocks: List[DocumentBlock] = Field(default_factory=list)
    sections: List[DocumentSection] = Field(default_factory=list)

    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("document_id cannot be empty.")
        return v.strip()

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Document title cannot be empty.")
        return v.strip()

    def add_block(self, block: DocumentBlock) -> "Document":
        """Append top-level block with assigned order index."""
        block.order_index = len(self.blocks)
        self.blocks.append(block)
        return self

    def add_section(self, section: DocumentSection) -> "Document":
        """Append section with assigned order index."""
        section.order_index = len(self.sections)
        self.sections.append(section)
        return self

    def get_all_blocks(self) -> List[DocumentBlock]:
        """Recursively collect all blocks across document root and sections."""
        all_blocks: List[DocumentBlock] = list(self.blocks)

        def _collect_from_section(sec: DocumentSection) -> None:
            all_blocks.extend(sec.blocks)
            for sub in sec.subsections:
                _collect_from_section(sub)

        for s in self.sections:
            _collect_from_section(s)

        return all_blocks


class SectionSpec(BaseModel):
    """Specification schema for a template section."""
    title_template: str
    required: bool = True
    default_blocks: List[DocumentBlock] = Field(default_factory=list)
    description: Optional[str] = None


class DocumentTemplate(BaseModel):
    """
    Reusable document specification/template.
    Defines blueprint structures, default metadata, and required template variables.
    """
    template_id: str = Field(default_factory=lambda: f"tmpl_{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    target_format: DocumentFormat = DocumentFormat.MARKDOWN
    default_metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    section_specs: List[SectionSpec] = Field(default_factory=list)
    required_variables: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty.")
        return v.strip()

    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Return list of missing required variable names."""
        missing = [v for v in self.required_variables if v not in variables]
        return missing

    def instantiate(self, title: str, variables: Optional[Dict[str, Any]] = None) -> Document:
        """Instantiate a structured Document instance from this template."""
        vars_map = variables or {}
        missing = self.validate_variables(vars_map)
        if missing:
            raise ValueError(f"Missing required template variables: {', '.join(missing)}")

        doc = Document(
            title=title,
            metadata=self.default_metadata.model_copy(deep=True),
        )
        for idx, spec in enumerate(self.section_specs):
            # Format title template with provided variables if formatted
            rendered_title = spec.title_template
            for k, val in vars_map.items():
                rendered_title = rendered_title.replace(f"{{{k}}}", str(val))

            sec = DocumentSection(
                title=rendered_title,
                order_index=idx,
                blocks=[b.model_copy(deep=True) for b in spec.default_blocks],
            )
            doc.add_section(sec)

        return doc
