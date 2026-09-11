import re
from typing import Any, Dict, List, Optional
import uuid

from executive_twins.documents.interfaces import (
    IDocumentBuilder,
    IDocumentParser,
    IDocumentRenderer,
)
from executive_twins.documents.models import (
    BlockType,
    BreakBlock,
    CodeBlock,
    Document,
    DocumentBlock,
    DocumentFormat,
    DocumentMetadata,
    DocumentSection,
    HeadingBlock,
    ImageRefBlock,
    ListBlock,
    ParagraphBlock,
    TableBlock,
    TableRow,
)
from executive_twins.schemas.common import SpecialistStatus
from executive_twins.schemas.specialist import Capability, RegistryProvenance, SpecialistMetadata



class DocumentBuilder(IDocumentBuilder):

    """
    Standard in-memory implementation of IDocumentBuilder.
    Provides fluent construction of structured Document objects.
    """

    def __init__(self, title: Optional[str] = None) -> None:
        self._title: str = title or ""
        self._metadata: DocumentMetadata = DocumentMetadata()
        self._blocks: List[DocumentBlock] = []
        self._sections: List[DocumentSection] = []

    def set_title(self, title: str) -> "DocumentBuilder":
        if not title or not title.strip():
            raise ValueError("Document title cannot be empty.")
        self._title = title.strip()
        return self

    def set_metadata(self, metadata: DocumentMetadata) -> "DocumentBuilder":
        self._metadata = metadata
        return self

    def add_heading(self, text: str, level: int = 1) -> "DocumentBuilder":
        heading = HeadingBlock(
            text=text,
            level=level,
            order_index=len(self._blocks),
        )
        self._blocks.append(heading)
        return self

    def add_paragraph(self, text: str) -> "DocumentBuilder":
        paragraph = ParagraphBlock(
            text=text,
            order_index=len(self._blocks),
        )
        self._blocks.append(paragraph)
        return self

    def add_table(
        self,
        headers: List[str],
        rows: List[List[Any]],
        caption: Optional[str] = None,
    ) -> "DocumentBuilder":
        table = TableBlock.create(
            headers=headers,
            rows_data=rows,
            caption=caption,
            order_index=len(self._blocks),
        )
        self._blocks.append(table)
        return self

    def add_image_ref(
        self,
        uri: str,
        alt_text: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> "DocumentBuilder":
        img = ImageRefBlock(
            uri=uri,
            alt_text=alt_text,
            caption=caption,
            order_index=len(self._blocks),
        )
        self._blocks.append(img)
        return self

    def add_block(self, block: DocumentBlock) -> "DocumentBuilder":
        block.order_index = len(self._blocks)
        self._blocks.append(block)
        return self

    def add_section(self, section: DocumentSection) -> "DocumentBuilder":
        section.order_index = len(self._sections)
        self._sections.append(section)
        return self

    def build(self) -> Document:
        if not self._title or not self._title.strip():
            raise ValueError("Cannot build Document: title is required and cannot be empty.")

        doc = Document(
            title=self._title,
            metadata=self._metadata,
            blocks=list(self._blocks),
            sections=list(self._sections),
        )
        return doc

    def reset(self) -> "DocumentBuilder":
        self._title = ""
        self._metadata = DocumentMetadata()
        self._blocks = []
        self._sections = []
        return self


class MarkdownDocumentRenderer(IDocumentRenderer):
    """
    Pure Python deterministic renderer that converts Document models into Markdown text.
    Does NOT depend on external markdown rendering engines.
    """

    def render(self, document: Document) -> str:
        lines: List[str] = []

        # 1. Document Title
        lines.append(f"# {document.title}\n")

        # 2. Render Root Blocks
        for b in document.blocks:
            lines.append(self._render_block(b))

        # 3. Render Sections
        for s in document.sections:
            lines.append(self._render_section(s))

        return "\n".join(lines).strip() + "\n"

    def _render_section(self, section: DocumentSection) -> str:
        lines: List[str] = []
        prefix = "#" * max(1, min(6, section.level))
        lines.append(f"{prefix} {section.title}\n")

        for b in section.blocks:
            lines.append(self._render_block(b))

        for sub in section.subsections:
            lines.append(self._render_section(sub))

        return "\n".join(lines)

    def _render_block(self, block: DocumentBlock) -> str:
        if isinstance(block, HeadingBlock):
            prefix = "#" * block.level
            return f"{prefix} {block.text}\n"

        elif isinstance(block, ParagraphBlock):
            return f"{block.text}\n"

        elif isinstance(block, CodeBlock):
            lang = block.language or ""
            return f"```{lang}\n{block.code}\n```\n"

        elif isinstance(block, ListBlock):
            items_str = []
            for idx, itm in enumerate(block.items, 1):
                if block.is_ordered:
                    items_str.append(f"{idx}. {itm}")
                else:
                    items_str.append(f"- {itm}")
            return "\n".join(items_str) + "\n"

        elif isinstance(block, ImageRefBlock):
            alt = block.alt_text or "image"
            caption_str = f"\n*{block.caption}*" if block.caption else ""
            return f"![{alt}]({block.uri}){caption_str}\n"

        elif isinstance(block, BreakBlock):
            return "\n---\n"

        elif isinstance(block, TableBlock):
            t_lines: List[str] = []
            if block.caption:
                t_lines.append(f"*{block.caption}*\n")
            if block.headers:
                t_lines.append("| " + " | ".join(block.headers) + " |")
                t_lines.append("| " + " | ".join(["---"] * len(block.headers)) + " |")
            for row in block.rows:
                cell_vals = [c.content for c in row.cells]
                t_lines.append("| " + " | ".join(cell_vals) + " |")
            return "\n".join(t_lines) + "\n"

        return ""


class MarkdownDocumentParser(IDocumentParser):
    """
    Standard lightweight parser converting Markdown text into typed Document models.
    """

    def parse(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        lines = content.splitlines()
        title = "Untitled Document"
        meta = DocumentMetadata(
            document_format=DocumentFormat.MARKDOWN,
            custom_attributes=metadata or {},
        )

        doc = Document(title=title, metadata=meta)
        current_section: Optional[DocumentSection] = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Heading 1 -> Root Document Title if title not yet discovered
            if stripped.startswith("# ") and doc.title == "Untitled Document":
                doc.title = stripped[2:].strip()
                continue

            # Headings -> Section or Heading block
            if stripped.startswith("## "):
                sec_title = stripped[3:].strip()
                current_section = DocumentSection(title=sec_title, level=2)
                doc.add_section(current_section)
                continue
            elif stripped.startswith("### "):
                sec_title = stripped[4:].strip()
                if current_section:
                    sub = DocumentSection(title=sec_title, level=3)
                    current_section.add_subsection(sub)
                else:
                    sec = DocumentSection(title=sec_title, level=3)
                    doc.add_section(sec)
                continue

            # Image reference ![alt](uri)
            img_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", stripped)
            if img_match:
                img_block = ImageRefBlock(
                    alt_text=img_match.group(1),
                    uri=img_match.group(2),
                )
                if current_section:
                    current_section.add_block(img_block)
                else:
                    doc.add_block(img_block)
                continue

            # Standard Paragraph
            p_block = ParagraphBlock(text=stripped)
            if current_section:
                current_section.add_block(p_block)
            else:
                doc.add_block(p_block)

        return doc


class DevTestDocumentAdapter:
    """
    DEV_TEST_ONLY_ADAPTER: Convenience adapter grouping DocumentBuilder, Renderer, and Parser.
    """

    def __init__(self) -> None:
        self.builder = DocumentBuilder()
        self.renderer = MarkdownDocumentRenderer()
        self.parser = MarkdownDocumentParser()

    def create_simple_document(self, title: str, paragraph: str) -> Document:
        return (
            DocumentBuilder()
            .set_title(title)
            .add_paragraph(paragraph)
            .build()
        )


def create_document_specialist(
    specialist_id: str = "spec_document_01",
    name: str = "Document Specialist",
    status: SpecialistStatus = SpecialistStatus.ACTIVE,
    security_level: str = "standard",
) -> SpecialistMetadata:
    """
    Factory creating authoritative SpecialistMetadata for the Document Specialist.
    Declares all supported document capabilities and authorized tools into the registry.
    """
    capabilities = [
        Capability(
            name="document_generation",
            description="Controlled synthesis of structured documents and offline visual artifacts",
            required_tools=["file_service"],
        ),
        Capability(
            name="document_editing",
            description="Controlled structured document modification and section editing",
            required_tools=["file_service"],
        ),
        Capability(
            name="document_validation",
            description="Controlled structural, hierarchy, and schema validation for documents",
            required_tools=["document_validator"],
        ),
    ]

    return SpecialistMetadata(
        specialist_id=specialist_id,
        name=name,
        capabilities=capabilities,
        status=status,
        authorized_tools=["file_service", "document_builder", "document_parser", "document_validator"],
        security_level=security_level,
        provenance=RegistryProvenance(
            registry_id="local_dev_registry",
            snapshot_id="snap_document_v1",
        ),
    )

