"""
Unit tests for Document Foundation (Member 2 Day 1 Item 2).
Verifies typed document structures, blocks, sections, templates, builder, renderer, parser, and serialization.
"""

from datetime import datetime, timezone
import json
import pytest
from pydantic import ValidationError

from executive_twins.documents import (
    BlockType,
    BreakBlock,
    BreakType,
    CodeBlock,
    DevTestDocumentAdapter,
    Document,
    DocumentBlock,
    DocumentBuilder,
    DocumentFormat,
    DocumentMetadata,
    DocumentSection,
    DocumentTemplate,
    HeadingBlock,
    IDocumentBuilder,
    IDocumentParser,
    IDocumentRenderer,
    ImageRefBlock,
    ListBlock,
    MarkdownDocumentParser,
    MarkdownDocumentRenderer,
    ParagraphBlock,
    SectionSpec,
    TableBlock,
    TableCell,
    TableRow,
)


class TestDocumentFoundation:
    """Test suite for Document Foundation domain models and adapters."""

    def test_valid_document_creation(self):
        """1. Valid document creation with title and default metadata."""
        doc = Document(title="Quarterly Engineering Report")
        assert doc.title == "Quarterly Engineering Report"
        assert doc.document_id.startswith("doc_")
        assert doc.metadata.document_format == DocumentFormat.MARKDOWN
        assert len(doc.blocks) == 0
        assert len(doc.sections) == 0

    def test_metadata_handling(self):
        """2. Document metadata custom attributes and tags."""
        meta = DocumentMetadata(
            document_format=DocumentFormat.REPORT,
            author="Executive Architect",
            source="governance_review",
            version="2.1",
            tags=["architecture", "q3", "confidential"],
            custom_attributes={"department": "Robotics", "approval_level": 3},
        )
        doc = Document(title="Architecture Spec", metadata=meta)
        assert doc.metadata.author == "Executive Architect"
        assert doc.metadata.version == "2.1"
        assert "q3" in doc.metadata.tags
        assert doc.metadata.custom_attributes["approval_level"] == 3

    def test_ordered_sections_and_blocks(self):
        """3. Ordered sections and nested block hierarchy."""
        doc = Document(title="System Architecture Document")

        # Top-level paragraph
        doc.add_block(ParagraphBlock(text="Executive Overview"))

        # Section 1 with blocks
        sec1 = DocumentSection(title="Core Architecture", level=1)
        sec1.add_block(HeadingBlock(text="Module Breakdown", level=2))
        sec1.add_block(ParagraphBlock(text="Detailing autonomous control loop components."))

        # Subsection
        sub_sec = DocumentSection(title="Security Layer")
        sub_sec.add_block(ParagraphBlock(text="Sandboxed boundary checks."))
        sec1.add_subsection(sub_sec)

        doc.add_section(sec1)

        assert len(doc.blocks) == 1
        assert doc.blocks[0].order_index == 0
        assert len(doc.sections) == 1
        assert doc.sections[0].title == "Core Architecture"
        assert len(doc.sections[0].blocks) == 2
        assert len(doc.sections[0].subsections) == 1
        assert doc.sections[0].subsections[0].title == "Security Layer"

        all_blocks = doc.get_all_blocks()
        assert len(all_blocks) == 4

    def test_heading_creation_and_bounds(self):
        """4. Heading creation with level validation (1-6)."""
        h1 = HeadingBlock(text="Top Level Heading", level=1)
        assert h1.level == 1
        assert h1.block_type == BlockType.HEADING

        h6 = HeadingBlock(text="Sub Sub Sub Heading", level=6)
        assert h6.level == 6

        # Level 0 or 7 must raise validation error
        with pytest.raises(ValidationError):
            HeadingBlock(text="Invalid Level", level=0)
        with pytest.raises(ValidationError):
            HeadingBlock(text="Invalid Level", level=7)

        # Empty text must raise validation error
        with pytest.raises(ValidationError):
            HeadingBlock(text="", level=1)

    def test_paragraph_creation(self):
        """5. Paragraph creation with arbitrary text."""
        p = ParagraphBlock(text="Autonomous workforce processes run with bounded iterations.")
        assert p.block_type == BlockType.PARAGRAPH
        assert "Autonomous" in p.text

    def test_table_creation(self):
        """6. Table block creation with headers and structured cells."""
        headers = ["Capability", "Specialist", "Status"]
        rows = [
            ["code_generation", "spec_software_dev_01", "ACTIVE"],
            ["static_analysis", "spec_software_dev_01", "ACTIVE"],
        ]
        table = TableBlock.create(headers=headers, rows_data=rows, caption="Active Workforce Capabilities")
        assert table.block_type == BlockType.TABLE
        assert len(table.headers) == 3
        assert len(table.rows) == 2
        assert table.rows[0].cells[0].content == "code_generation"
        assert table.caption == "Active Workforce Capabilities"

    def test_image_reference_creation(self):
        """7. Image reference block creation without binary file loading."""
        img = ImageRefBlock(
            uri="workspace://diagrams/architecture_flow.png",
            alt_text="Architecture Diagram",
            caption="Figure 1: Control Loop DAG",
        )
        assert img.block_type == BlockType.IMAGE_REF
        assert img.uri == "workspace://diagrams/architecture_flow.png"
        assert img.alt_text == "Architecture Diagram"

        # Empty URI must fail validation
        with pytest.raises(ValidationError):
            ImageRefBlock(uri="")

    def test_template_creation_and_instantiation(self):
        """8. Reusable document template creation and instantiation."""
        tmpl = DocumentTemplate(
            name="Sprint Plan Template",
            description="Standardized engineering sprint document blueprint",
            target_format=DocumentFormat.MARKDOWN,
            required_variables=["sprint_num", "team_name"],
            section_specs=[
                SectionSpec(
                    title_template="Sprint {sprint_num} Goals - {team_name}",
                    default_blocks=[ParagraphBlock(text="Primary objectives and milestones for this sprint.")],
                ),
                SectionSpec(
                    title_template="Deliverables",
                    default_blocks=[
                        TableBlock.create(
                            headers=["Item", "Owner", "Estimate"],
                            rows_data=[["Feature A", "Engineer 1", "3d"]],
                        )
                    ],
                ),
            ],
        )
        assert tmpl.name == "Sprint Plan Template"

        # Instantiation with variables
        doc = tmpl.instantiate(
            title="Sprint 14 Plan",
            variables={"sprint_num": 14, "team_name": "Core Brain"},
        )
        assert doc.title == "Sprint 14 Plan"
        assert len(doc.sections) == 2
        assert doc.sections[0].title == "Sprint 14 Goals - Core Brain"
        assert doc.sections[1].title == "Deliverables"

        # Missing required variable raises error
        with pytest.raises(ValueError, match="Missing required template variables"):
            tmpl.instantiate(title="Invalid Sprint", variables={"sprint_num": 15})

    def test_invalid_document_structures_rejected(self):
        """9. Invalid document structures (empty IDs, empty titles) rejected."""
        with pytest.raises(ValidationError):
            Document(title="")

        with pytest.raises(ValidationError):
            Document(title="Valid Title", document_id="")

        with pytest.raises(ValidationError):
            DocumentSection(title="")

        with pytest.raises(ValidationError):
            DocumentSection(title="Valid", section_id="")

    def test_builder_interface_and_fluent_assembly(self):
        """10. DocumentBuilder interface creates verified document."""
        builder = DocumentBuilder()
        doc = (
            builder.set_title("Autonomous AI Workforce Whitepaper")
            .set_metadata(DocumentMetadata(author="LM-Brain Team"))
            .add_heading("1. Executive Summary", level=1)
            .add_paragraph("LM-Brain introduces verifiable multi-agent orchestration.")
            .add_table(
                headers=["Layer", "Role"],
                rows=[["Executive Twins", "Governance"], ["Control Loop", "Orchestration"]],
            )
            .add_image_ref("workspace://charts/kpi.svg", alt_text="KPI Chart")
            .add_block(CodeBlock(code="def run(): pass", language="python"))
            .add_block(ListBlock(items=["Milestone 1", "Milestone 2"], is_ordered=True))
            .add_block(BreakBlock(break_type=BreakType.SECTION_BREAK))
            .build()
        )

        assert isinstance(builder, IDocumentBuilder)
        assert doc.title == "Autonomous AI Workforce Whitepaper"
        assert len(doc.blocks) == 7
        assert doc.metadata.author == "LM-Brain Team"

    def test_builder_requires_title(self):
        """11. Builder raises ValueError when building without title."""
        builder = DocumentBuilder()
        builder.add_paragraph("Some text")
        with pytest.raises(ValueError, match="title is required"):
            builder.build()

    def test_renderer_and_parser_roundtrip(self):
        """12. Markdown renderer and parser interfaces integration."""
        renderer = MarkdownDocumentRenderer()
        parser = MarkdownDocumentParser()

        assert isinstance(renderer, IDocumentRenderer)
        assert isinstance(parser, IDocumentParser)

        # Build doc
        doc = (
            DocumentBuilder()
            .set_title("Product Requirements")
            .add_paragraph("Overview of requested features.")
            .build()
        )
        sec = DocumentSection(title="Functional Requirements", level=2)
        sec.add_block(ParagraphBlock(text="The system must support deterministic reasoning."))
        doc.add_section(sec)

        rendered_md = renderer.render(doc)
        assert "# Product Requirements" in rendered_md
        assert "## Functional Requirements" in rendered_md
        assert "deterministic reasoning" in rendered_md

        # Parse back
        parsed_doc = parser.parse(rendered_md)
        assert parsed_doc.title == "Product Requirements"
        assert len(parsed_doc.sections) == 1
        assert parsed_doc.sections[0].title == "Functional Requirements"

    def test_pydantic_serialization_and_deserialization(self):
        """13. Serialization and deserialization preservation."""
        doc = (
            DocumentBuilder()
            .set_title("Serialization Test Document")
            .set_metadata(DocumentMetadata(tags=["test", "serialization"]))
            .add_heading("Section 1", level=1)
            .add_paragraph("Test paragraph content.")
            .add_table(headers=["A", "B"], rows=[["1", "2"]])
            .build()
        )

        # JSON dump and load
        json_str = doc.model_dump_json()
        data = json.loads(json_str)
        assert data["title"] == "Serialization Test Document"
        assert len(data["blocks"]) == 3

        # Reconstruct from JSON
        doc_reconstructed = Document.model_validate_json(json_str)
        assert doc_reconstructed.title == doc.title
        assert len(doc_reconstructed.blocks) == len(doc.blocks)
        assert doc_reconstructed.metadata.tags == ["test", "serialization"]

    def test_dev_test_adapter(self):
        """14. DevTestDocumentAdapter convenience helper."""
        adapter = DevTestDocumentAdapter()
        doc = adapter.create_simple_document(
            title="Quick Note",
            paragraph="Automated test note content.",
        )
        assert doc.title == "Quick Note"
        assert len(doc.blocks) == 1
        rendered = adapter.renderer.render(doc)
        assert "# Quick Note" in rendered
