"""
Unit tests for Presentation Specialist (Member 2 Day 2).
Verifies presentation domain models, slide layouts, elements, templates, builders,
renderers, capability handlers, specialist metadata, evidence creation, and security isolation.
"""

from datetime import datetime, timezone
import json
import pytest
from pydantic import ValidationError

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionEngine,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.presentations import (
    DevTestPresentationAdapter,
    ElementType,
    IPresentationBuilder,
    IPresentationRenderer,
    IPresentationSpecialist,
    PresentationBuilder,
    PresentationDeck,
    PresentationGenerationCapabilityHandler,
    PresentationHTMLRenderer,
    PresentationMarkdownRenderer,
    PresentationTemplate,
    PresentationValidationCapabilityHandler,
    Slide,
    SlideBulletListElement,
    SlideCreationCapabilityHandler,
    SlideElement,
    SlideImageElement,
    SlideLayout,
    SlideMetricElement,
    SlideSpec,
    SlideTableElement,
    SlideTextElement,
    create_presentation_specialist,
)
from executive_twins.schemas.common import FactState, SecurityContext, SpecialistStatus
from executive_twins.schemas.delegation import DelegationRequest
from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


def make_delegation_request(
    delegation_id: str,
    capability_name: str,
    inputs: dict,
    specialist_id: str = "spec_presentation_01",
    task: str = "Presentation task",
    objective: str = "Execute presentation operation",
    expected_output: str = "Presentation output",
) -> DelegationRequest:
    """Helper creating a fully populated DelegationRequest."""
    return DelegationRequest(
        delegation_id=delegation_id,
        parent_task_id=f"parent_{delegation_id}",
        executive_twin_id="twin_cmo",
        specialist_id=specialist_id,
        objective=objective,
        task=task,
        required_capabilities=[capability_name],
        inputs=inputs,
        expected_output=expected_output,
    )


class TestPresentationSpecialist:
    """Comprehensive test suite for Presentation Specialist module."""

    # -------------------------------------------------------------------------
    # 1-2. Deck Creation & Title Validation
    # -------------------------------------------------------------------------

    def test_presentation_deck_creation(self):
        """1. Valid PresentationDeck creation with default metadata and aspect ratio."""
        deck = PresentationDeck(title="Autonomous Workforce Q3 Overview")
        assert deck.title == "Autonomous Workforce Q3 Overview"
        assert deck.presentation_id.startswith("pres_")
        assert deck.aspect_ratio == "16:9"
        assert deck.theme == "modern_dark"
        assert len(deck.slides) == 0

    def test_required_title_validation(self):
        """2. Presentation title is mandatory and non-empty."""
        with pytest.raises(ValidationError):
            PresentationDeck(title="")

        with pytest.raises(ValidationError):
            PresentationDeck(title="Valid", presentation_id="")

    # -------------------------------------------------------------------------
    # 3-6. Slide Creation, Layouts & Ordering
    # -------------------------------------------------------------------------

    def test_slide_creation_and_defaults(self):
        """3. Slide creation with layout and title."""
        slide = Slide(title="Architecture Roadmap", layout=SlideLayout.SECTION_HEADER)
        assert slide.title == "Architecture Roadmap"
        assert slide.layout == SlideLayout.SECTION_HEADER
        assert slide.slide_id.startswith("slide_")
        assert len(slide.elements) == 0

    def test_slide_layout_validation(self):
        """4. SlideLayout enum values supported."""
        for layout in SlideLayout:
            s = Slide(title=f"Slide for {layout.value}", layout=layout)
            assert s.layout == layout

    def test_deterministic_slide_ordering(self):
        """5. Slides preserve sequential order indices in deck."""
        deck = PresentationDeck(title="Multi-Slide Deck")
        s1 = Slide(title="Intro")
        s2 = Slide(title="Architecture")
        s3 = Slide(title="Results")

        deck.add_slide(s1)
        deck.add_slide(s2)
        deck.add_slide(s3)

        assert len(deck.slides) == 3
        assert deck.slides[0].order_index == 0
        assert deck.slides[1].order_index == 1
        assert deck.slides[2].order_index == 2
        assert [s.title for s in deck.slides] == ["Intro", "Architecture", "Results"]

    def test_slide_element_ordering(self):
        """6. Slide elements maintain deterministic order."""
        slide = Slide(title="Components")
        t1 = SlideTextElement(content="Header description")
        b1 = SlideBulletListElement(items=["Worker 1", "Worker 2"])
        m1 = SlideMetricElement(label="Throughput", value="100 req/s")

        slide.add_element(t1)
        slide.add_element(b1)
        slide.add_element(m1)

        assert len(slide.elements) == 3
        assert slide.elements[0].order_index == 0
        assert slide.elements[1].order_index == 1
        assert slide.elements[2].order_index == 2

    # -------------------------------------------------------------------------
    # 7-12. Granular Slide Elements & Speaker Notes
    # -------------------------------------------------------------------------

    def test_text_element(self):
        """7. SlideTextElement creation and styling attributes."""
        el = SlideTextElement(content="Executive alignment is mandatory", is_bold=True, font_size="large")
        assert el.element_type == ElementType.TEXT
        assert el.content == "Executive alignment is mandatory"
        assert el.is_bold is True

    def test_bullet_list_element(self):
        """8. SlideBulletListElement ordered and unordered modes."""
        ul = SlideBulletListElement(items=["Item A", "Item B"], is_ordered=False)
        assert ul.element_type == ElementType.BULLET_LIST
        assert len(ul.items) == 2
        assert ul.is_ordered is False

        ol = SlideBulletListElement(items=["Step 1", "Step 2"], is_ordered=True)
        assert ol.is_ordered is True

    def test_table_element(self):
        """9. SlideTableElement with headers, rows, and caption."""
        headers = ["Agent", "Clearance", "Status"]
        rows = [
            ["spec_software_dev_01", "standard", "ACTIVE"],
            ["spec_presentation_01", "standard", "ACTIVE"],
        ]
        tbl = SlideTableElement(headers=headers, rows=rows, caption="Active Workforce Agents")
        assert tbl.element_type == ElementType.TABLE
        assert len(tbl.headers) == 3
        assert len(tbl.rows) == 2
        assert tbl.caption == "Active Workforce Agents"

    def test_image_reference_element(self):
        """10. SlideImageElement validates URI without loading binary files."""
        img = SlideImageElement(
            uri="workspace://diagrams/pipeline.png",
            alt_text="Pipeline Flowchart",
            caption="Figure 1: 10-Stage Pipeline",
        )
        assert img.element_type == ElementType.IMAGE_REF
        assert img.uri == "workspace://diagrams/pipeline.png"

        # Empty URI must fail validation
        with pytest.raises(ValidationError):
            SlideImageElement(uri="")

    def test_metric_element(self):
        """11. SlideMetricElement validates label and value."""
        m = SlideMetricElement(
            label="Inference Latency",
            value="450ms",
            delta="-32% vs v1",
            description="Average response time over local relay",
        )
        assert m.element_type == ElementType.METRIC
        assert m.label == "Inference Latency"
        assert m.value == "450ms"
        assert m.delta == "-32% vs v1"

        with pytest.raises(ValidationError):
            SlideMetricElement(label="", value="10")

    def test_speaker_notes(self):
        """12. Slide speaker notes field preservation."""
        slide = Slide(
            title="Strategic Overview",
            speaker_notes="Emphasize governance boundaries and lack of direct tool execution.",
        )
        assert "governance boundaries" in slide.speaker_notes

    # -------------------------------------------------------------------------
    # 13-15. Presentation Templates
    # -------------------------------------------------------------------------

    def test_presentation_template_creation(self):
        """13. PresentationTemplate creation and metadata."""
        tmpl = PresentationTemplate(
            name="Quarterly Business Review",
            description="Standardized QBR presentation deck template",
            required_variables=["quarter", "year", "presenter"],
            slide_specs=[
                SlideSpec(
                    title_template="QBR - {quarter} {year}",
                    layout=SlideLayout.TITLE,
                    default_elements=[SlideTextElement(content="Presented by: {presenter}")],
                ),
                SlideSpec(
                    title_template="Key Achievements",
                    layout=SlideLayout.TITLE_AND_CONTENT,
                    default_elements=[
                        SlideMetricElement(label="Features Delivered", value="24"),
                        SlideBulletListElement(items=["Item 1", "Item 2"]),
                    ],
                    speaker_notes_template="Highlight on-time delivery metrics for {quarter}.",
                ),
            ],
        )
        assert tmpl.name == "Quarterly Business Review"
        assert len(tmpl.slide_specs) == 2

    def test_template_required_variable_validation(self):
        """14. Template variable validation detects missing fields."""
        tmpl = PresentationTemplate(
            name="Test Template",
            required_variables=["client_name", "product"],
        )
        missing = tmpl.validate_variables({"client_name": "Acme Corp"})
        assert missing == ["product"]

    def test_template_instantiation(self):
        """15. Template instantiates complete deck with variable interpolation."""
        tmpl = PresentationTemplate(
            name="Project Proposal",
            required_variables=["project_name", "client"],
            slide_specs=[
                SlideSpec(
                    title_template="{project_name} for {client}",
                    layout=SlideLayout.TITLE,
                    default_elements=[SlideTextElement(content="Confidential Proposal for {client}")],
                )
            ],
        )
        deck = tmpl.instantiate(
            title="NovaPulse Proposal",
            variables={"project_name": "Autonomous Brain", "client": "Apex Logistics"},
        )
        assert deck.title == "NovaPulse Proposal"
        assert len(deck.slides) == 1
        assert deck.slides[0].title == "Autonomous Brain for Apex Logistics"
        assert deck.slides[0].elements[0].content == "Confidential Proposal for Apex Logistics"

    # -------------------------------------------------------------------------
    # 16-18. Builder & Renderers (Markdown and HTML)
    # -------------------------------------------------------------------------

    def test_builder_fluent_construction(self):
        """16. PresentationBuilder fluent assembly."""
        builder = PresentationBuilder()
        deck = (
            builder.set_title("Autonomous AI Workforce")
            .set_subtitle("CEO Proposal & Implementation Plan")
            .set_aspect_ratio("16:9")
            .set_theme("modern_dark")
            .create_slide("1. Executive Summary", layout=SlideLayout.TITLE_AND_CONTENT, speaker_notes="Introductory slide")
            .add_text("Autonomous execution behind security guard.")
            .add_bullet_list(["Master Orchestrator", "Specialist Workers", "Audit Trail"])
            .add_metric("Pass Rate", "100%", delta="+0%")
            .create_slide("2. Performance Matrix", layout=SlideLayout.TABLE_SLIDE)
            .add_table(headers=["Task", "Duration"], rows=[["Planning", "1.2s"], ["Execution", "3.4s"]])
            .build()
        )

        assert isinstance(builder, IPresentationBuilder)
        assert deck.title == "Autonomous AI Workforce"
        assert len(deck.slides) == 2
        assert len(deck.slides[0].elements) == 3
        assert len(deck.slides[1].elements) == 1

    def test_markdown_rendering(self):
        """17. PresentationMarkdownRenderer formats deck into structured Markdown."""
        renderer = PresentationMarkdownRenderer()
        assert isinstance(renderer, IPresentationRenderer)

        deck = (
            PresentationBuilder(title="Deck for Markdown Render")
            .create_slide(title="Slide One", layout=SlideLayout.TITLE_AND_CONTENT, speaker_notes="Notes here")
            .add_bullet_list(["Point 1", "Point 2"])
            .build()
        )

        md = renderer.render(deck)
        assert "marp: true" in md
        assert "# Deck for Markdown Render" in md
        assert "## Slide One" in md
        assert "- Point 1" in md
        assert "<!-- Speaker Notes:\nNotes here\n-->" in md

    def test_html_rendering_self_contained(self):
        """18. PresentationHTMLRenderer generates self-contained interactive HTML without external assets."""
        renderer = PresentationHTMLRenderer()
        deck = (
            PresentationBuilder(title="Interactive Slide Deck")
            .set_subtitle("Self Contained Demo")
            .create_slide(title="KPI Overview", layout=SlideLayout.METRIC_CARD, speaker_notes="Speaker notes for KPI")
            .add_metric("Reliability", "99.9%", delta="+0.4%")
            .add_text("System operates autonomously.")
            .build()
        )

        html_out = renderer.render(deck)
        assert "<!DOCTYPE html>" in html_out
        assert "Interactive Slide Deck" in html_out
        assert "KPI Overview" in html_out
        assert "Reliability" in html_out
        assert "99.9%" in html_out
        assert "Speaker Notes" in html_out
        assert "http://" not in html_out  # No external CDNs or unapproved network links
        assert "https://" not in html_out

    # -------------------------------------------------------------------------
    # 19-20. Presentation Validation Handler
    # -------------------------------------------------------------------------

    def test_presentation_validation_success(self):
        """19. PresentationValidationCapabilityHandler accepts valid decks."""
        handler = PresentationValidationCapabilityHandler()
        deck = (
            PresentationBuilder(title="Valid Deck")
            .create_slide("Slide 1", speaker_notes="Notes")
            .add_text("Content")
            .build()
        )

        meta = create_presentation_specialist()
        req = make_delegation_request(
            delegation_id="del_val_01",
            capability_name="presentation_validation",
            inputs={"presentation": deck.model_dump()},
        )

        out = handler.execute(req, meta)
        assert out.success is True
        assert "successfully verified" in out.output_text
        assert len(out.additional_evidence) == 1

    def test_presentation_validation_failure(self):
        """20. PresentationValidationCapabilityHandler detects empty titles and slide bounds."""
        handler = PresentationValidationCapabilityHandler()
        meta = create_presentation_specialist()

        # Deck with 0 slides when min_slides=1
        invalid_deck = {"title": "Empty Deck", "slides": []}
        req = make_delegation_request(
            delegation_id="del_val_02",
            capability_name="presentation_validation",
            inputs={"presentation": invalid_deck, "min_slides": 1},
        )

        out = handler.execute(req, meta)
        assert out.success is False
        assert any("below minimum required" in err for err in out.errors)

    # -------------------------------------------------------------------------
    # 21-25. Specialist Registration, Execution Boundary, Evidence & Isolation
    # -------------------------------------------------------------------------

    def test_specialist_metadata_creation(self):
        """21. create_presentation_specialist factory exports authoritative metadata."""
        meta = create_presentation_specialist()
        assert meta.specialist_id == "spec_presentation_01"
        assert meta.name == "Presentation Specialist"
        assert meta.status == SpecialistStatus.ACTIVE

        cap_names = [c.name for c in meta.capabilities]
        assert "presentation_generation" in cap_names
        assert "slide_creation" in cap_names
        assert "presentation_validation" in cap_names

    def test_capability_handler_parameter_validation(self):
        """22. Capability handler rejects missing required parameters."""
        gen_handler = PresentationGenerationCapabilityHandler()
        err = gen_handler.validate_parameters({})
        assert "Missing required parameter 'title'" in err

        slide_handler = SlideCreationCapabilityHandler()
        err2 = slide_handler.validate_parameters({"title": "Slide 1"})
        assert "Missing required parameter 'layout'" in err2

    def test_presentation_generation_through_execution_engine(self):
        """23. Full presentation generation executed through SpecialistExecutionEngine boundary."""
        registry = InMemorySpecialistRegistryAdapter()
        meta = create_presentation_specialist()
        registry.register_specialist(meta)

        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)

        engine = SpecialistExecutionEngine(registry_client=registry)
        engine.register_handler(PresentationGenerationCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(SlideCreationCapabilityHandler())
        engine.register_handler(PresentationValidationCapabilityHandler())

        req = make_delegation_request(
            delegation_id="del_pres_01",
            capability_name="presentation_generation",
            task="Generate Q3 review presentation",
            inputs={
                "title": "Q3 Engineering Review",
                "subtitle": "Autonomous Workforce Milestone",
                "workspace_id": "default",
                "relative_path": "presentations/q3_review.html",
                "slides": [
                    {
                        "title": "Milestone Highlights",
                        "layout": "TITLE_AND_CONTENT",
                        "elements": [
                            {"type": "METRIC", "label": "Pipeline Tests", "value": "566+", "delta": "+100%"},
                            {"type": "BULLET_LIST", "items": ["Reasoning Engine", "Document Foundation", "PPT Specialist"]},
                        ],
                        "speaker_notes": "Walk through the key deliverables for Q3.",
                    }
                ],
            },
        )

        result = engine.execute_delegation(req)
        assert result.status == "SUCCESS"
        assert "Successfully generated presentation" in result.output
        assert len(result.artifacts) > 0

        # Verify file persisted inside workspace boundary
        file_service = file_adapter.get_file_service("default")
        read_res = file_service.read_file("presentations/q3_review.html")
        assert read_res.success is True
        assert "<!DOCTYPE html>" in read_res.content
        assert "Q3 Engineering Review" in read_res.content
        assert "566+" in read_res.content

    def test_artifact_and_evidence_creation(self):
        """24. Evidence items and artifact URIs correctly generated."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        gen_handler = PresentationGenerationCapabilityHandler(file_adapter=file_adapter)
        meta = create_presentation_specialist()

        req = make_delegation_request(
            delegation_id="del_pres_ev_01",
            capability_name="presentation_generation",
            inputs={"title": "Evidence Verification Deck", "relative_path": "deck.html"},
        )

        out = gen_handler.execute(req, meta)
        assert out.success is True
        assert len(out.artifacts) > 0
        assert out.artifacts[0].startswith("workspace://")
        assert len(out.additional_evidence) > 0

    def test_no_direct_filesystem_access_from_domain_models(self):
        """25. Domain models are pure data structures without filesystem coupling."""
        deck = PresentationDeck(title="Pure Domain Deck")
        slide = Slide(title="Pure Slide")
        slide.add_element(SlideTextElement(content="In-memory only"))
        deck.add_slide(slide)

        # Domain models must serialize cleanly without disk interaction
        dumped = deck.model_dump()
        assert dumped["title"] == "Pure Domain Deck"
        assert len(dumped["slides"]) == 1

        reconstructed = PresentationDeck.model_validate(dumped)
        assert reconstructed.title == deck.title
        assert isinstance(reconstructed.slides[0].elements[0], SlideTextElement)
        assert reconstructed.slides[0].elements[0].content == "In-memory only"
