"""
Unit tests for Content Foundation & Specialist (Member 2 Day 3).
Verifies Content models, builders, renderers, validators, adapters, capability handlers,
specialist metadata, FileService persistence, and SpecialistExecutionEngine integration.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import pytest
from pydantic import ValidationError

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.content import (
    Channel,
    ContentBrief,
    ContentBuilder,
    ContentEditingCapabilityHandler,
    ContentGenerationCapabilityHandler,
    ContentMetadata,
    ContentPiece,
    ContentReviewResult,
    ContentType,
    ContentValidationCapabilityHandler,
    DeterministicContentValidator,
    DevTestContentAdapter,
    HTMLContentRenderer,
    IContentBuilder,
    IContentRenderer,
    IContentSpecialist,
    IContentValidator,
    MarkdownContentRenderer,
    Tone,
    create_content_specialist,
)
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionEngine,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.schemas.common import FactState, SecurityContext, SpecialistStatus
from executive_twins.schemas.delegation import DelegationRequest, DelegationResult
from executive_twins.schemas.evidence import (
    ArtifactEvidence,
    EvidenceCategory,
    VerificationEvidence,
)
from executive_twins.schemas.specialist import CapabilityRequirement
from executive_twins.workspace.dev_adapters import DevTestWorkspaceAdapter


def make_delegation_request(
    delegation_id: str,
    capability_name: str,
    inputs: dict,
    specialist_id: str = "spec_content_01",
    task: str = "Content task",
    objective: str = "Execute content operation",
    expected_output: str = "Content asset output",
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


# ==============================================================================
# 1. Models and Enums Tests
# ==============================================================================


class TestContentModels:
    def test_enums(self):
        assert ContentType.BLOG_POST.value == "BLOG_POST"
        assert ContentType.SOCIAL_POST.value == "SOCIAL_POST"
        assert ContentType.AD_COPY.value == "AD_COPY"
        assert ContentType.PRESS_RELEASE.value == "PRESS_RELEASE"
        assert ContentType.EMAIL.value == "EMAIL"

        assert Tone.PROFESSIONAL.value == "PROFESSIONAL"
        assert Tone.FRIENDLY.value == "FRIENDLY"
        assert Tone.FORMAL.value == "FORMAL"
        assert Tone.CONVERSATIONAL.value == "CONVERSATIONAL"
        assert Tone.PERSUASIVE.value == "PERSUASIVE"
        assert Tone.INFORMATIVE.value == "INFORMATIVE"

        assert Channel.BLOG.value == "BLOG"
        assert Channel.LINKEDIN.value == "LINKEDIN"
        assert Channel.INSTAGRAM.value == "INSTAGRAM"
        assert Channel.EMAIL.value == "EMAIL"
        assert Channel.WEBSITE.value == "WEBSITE"
        assert Channel.PRESS.value == "PRESS"

    def test_content_metadata(self):
        meta = ContentMetadata(
            title="Q3 Strategy Announcement",
            content_type=ContentType.PRESS_RELEASE,
            channel=Channel.PRESS,
            tone=Tone.FORMAL,
            target_audience="Enterprise Executives",
            tags=["Q3", "Strategy", "AI"],
            custom_attributes={"embargo": "2026-10-01"},
        )
        assert meta.title == "Q3 Strategy Announcement"
        assert meta.content_type == ContentType.PRESS_RELEASE
        assert meta.tags == ["Q3", "Strategy", "AI"]
        assert meta.custom_attributes["embargo"] == "2026-10-01"

    def test_content_brief(self):
        brief = ContentBrief(
            purpose="Launch Autonomous Workforce v2.0",
            content_type=ContentType.BLOG_POST,
            channel=Channel.BLOG,
            tone=Tone.PERSUASIVE,
            target_audience="Engineering Leaders & CTOs",
            key_points=["Deterministic security", "Executive Twin architecture", "Zero hallucination"],
            call_to_action="Read the whitepaper and start deployment",
        )
        assert brief.purpose == "Launch Autonomous Workforce v2.0"
        assert len(brief.key_points) == 3
        assert brief.call_to_action is not None

        # Serialization
        dumped = brief.model_dump()
        restored = ContentBrief.model_validate(dumped)
        assert restored.purpose == brief.purpose
        assert restored.content_type == ContentType.BLOG_POST

    def test_content_piece(self):
        meta = ContentMetadata(content_type=ContentType.BLOG_POST, channel=Channel.WEBSITE)
        piece = ContentPiece(
            metadata=meta,
            title="Overview of Controlled Execution",
            body="Specialists execute capabilities within strict sandboxes.",
            sections={"Architecture": "Engine verifies tools and provenance.", "Outcome": "Deterministic operations."},
            call_to_action="Contact us for enterprise deployment.",
        )
        assert piece.title == "Overview of Controlled Execution"
        assert len(piece.sections) == 2
        assert piece.call_to_action == "Contact us for enterprise deployment."

        dumped = piece.model_dump()
        restored = ContentPiece.model_validate(dumped)
        assert restored.title == piece.title
        assert restored.sections["Architecture"] == "Engine verifies tools and provenance."

    def test_content_review_result(self):
        res = ContentReviewResult(
            valid=True,
            issues=[],
            warnings=["Slightly short introduction"],
            suggestions=["Consider adding metrics"],
            checks_performed=["check_body_non_empty", "check_minimum_length"],
        )
        assert res.valid is True
        assert len(res.warnings) == 1
        assert len(res.checks_performed) == 2


# ==============================================================================
# 2. Builder and Renderers Tests
# ==============================================================================


class TestContentBuilderAndRenderers:
    def test_builder_from_brief(self):
        brief = ContentBrief(
            purpose="Introduce Member 2 Content Specialist",
            content_type=ContentType.SOCIAL_POST,
            channel=Channel.LINKEDIN,
            tone=Tone.PROFESSIONAL,
            target_audience="Dev Team",
            key_points=["Deterministic synthesis", "Offline verification"],
            call_to_action="Check the test results.",
        )
        builder = ContentBuilder(brief=brief)
        piece = builder.build()

        assert piece.title == "Social Post: Introduce Member 2 Content Specialist"
        assert "Deterministic synthesis" in piece.body
        assert "#AutonomousWorkforce" in piece.body
        assert piece.call_to_action == "Check the test results."

    def test_builder_manual_configuration(self):
        builder = (
            ContentBuilder()
            .set_title("Executive Memo")
            .set_body("All specialists have been audited and verified.")
            .add_section("Key Findings", "100% test coverage with zero regressions.")
            .set_call_to_action("Approve next phase.")
        )
        piece = builder.build()

        assert piece.title == "Executive Memo"
        assert piece.body == "All specialists have been audited and verified."
        assert piece.sections["Key Findings"] == "100% test coverage with zero regressions."
        assert piece.call_to_action == "Approve next phase."

    def test_markdown_renderer(self):
        meta = ContentMetadata(
            content_type=ContentType.BLOG_POST,
            channel=Channel.BLOG,
            tone=Tone.PROFESSIONAL,
            target_audience="General Tech Audience",
        )
        piece = ContentPiece(
            metadata=meta,
            title="Building Autonomous Workforce",
            body="LM-Brain represents the next stage in agentic engineering.",
            sections={"Component Design": "Each specialist isolates domain expertise."},
            call_to_action="Join the platform.",
        )
        renderer = MarkdownContentRenderer()
        md_text = renderer.render(piece)

        assert "# Building Autonomous Workforce" in md_text
        assert "**Type**: `BLOG_POST`" in md_text
        assert "**Channel**: `BLOG`" in md_text
        assert "LM-Brain represents the next stage" in md_text
        assert "## Component Design" in md_text
        assert "**Call to Action**: Join the platform." in md_text

    def test_html_renderer(self):
        meta = ContentMetadata(
            content_type=ContentType.PRESS_RELEASE,
            channel=Channel.PRESS,
            tone=Tone.FORMAL,
            target_audience="Media & Analysts",
        )
        piece = ContentPiece(
            metadata=meta,
            title="Press Release <Special & Safe>",
            body="Important announcement.\nSecond paragraph.",
            sections={"Details": "Full breakdown of capabilities."},
            call_to_action="Visit press center.",
        )
        renderer = HTMLContentRenderer()
        html_text = renderer.render(piece)

        assert "<!DOCTYPE html>" in html_text
        assert "&lt;Special &amp; Safe&gt;" in html_text
        assert "<br/>Second paragraph." in html_text
        assert "<h3>Details</h3>" in html_text
        assert "Visit press center." in html_text


# ==============================================================================
# 3. Validator and Dev Adapter Tests
# ==============================================================================


class TestContentValidatorAndAdapter:
    def test_validator_success(self):
        brief = ContentBrief(
            purpose="Explain architecture",
            content_type=ContentType.BLOG_POST,
            channel=Channel.WEBSITE,
            key_points=["Controlled execution", "Sandbox isolation"],
            call_to_action="Explore docs",
        )
        piece = ContentPiece(
            metadata=ContentMetadata(),
            title="Architecture Guide",
            body="This article explains controlled execution and sandbox isolation principles.",
            call_to_action="Explore docs",
        )
        validator = DeterministicContentValidator()
        result = validator.validate(piece, brief=brief)

        assert result.valid is True
        assert len(result.issues) == 0

    def test_validator_failure_empty_body(self):
        with pytest.raises(ValidationError):
            ContentPiece(
                metadata=ContentMetadata(),
                title="Empty Asset",
                body="   ",
            )

    def test_validator_failure_missing_cta(self):
        brief = ContentBrief(
            purpose="Sign up promo",
            call_to_action="Click here to register now",
        )
        piece = ContentPiece(
            metadata=ContentMetadata(),
            title="Promo Post",
            body="Great offers are available today for everyone.",
            call_to_action=None,
        )
        validator = DeterministicContentValidator()
        result = validator.validate(piece, brief=brief)

        assert result.valid is False
        assert any("call to action" in issue.lower() for issue in result.issues)

    def test_dev_test_content_adapter(self):
        adapter = DevTestContentAdapter()
        brief = ContentBrief(
            purpose="Product Launch",
            content_type=ContentType.AD_COPY,
            channel=Channel.EMAIL,
            call_to_action="Sign up today",
        )
        piece = adapter.generate_content(brief)
        assert piece.metadata.content_type == ContentType.AD_COPY

        # Edit content
        edited_piece = adapter.edit_content(
            piece,
            instructions="Update CTA and append guarantee",
            edits={
                "action": "append_content",
                "content": "30-day money-back guarantee.",
            },
        )
        assert "30-day money-back guarantee." in edited_piece.body

        # Validate content
        review = adapter.validate_content(edited_piece, brief)
        assert review.valid is True


# ==============================================================================
# 4. Capability Handlers Unit Tests
# ==============================================================================


class TestContentCapabilityHandlers:
    @pytest.fixture
    def workspace_setup(self):
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("default")
        return ws_adapter, file_adapter

    def test_generation_handler_markdown(self, workspace_setup):
        _, file_adapter = workspace_setup
        handler = ContentGenerationCapabilityHandler(file_adapter=file_adapter)
        specialist = create_content_specialist()

        req = make_delegation_request(
            delegation_id="del_gen_01",
            capability_name="content_generation",
            inputs={
                "purpose": "Product launch announcement",
                "content_type": "blog_post",
                "channel": "blog",
                "tone": "persuasive",
                "target_audience": "Enterprise Customers",
                "key_points": ["Fast deployment", "Secure by design"],
                "call_to_action": "Schedule a demo",
                "relative_path": "articles/launch.md",
                "workspace_id": "default",
            },
        )

        out = handler.execute(req, specialist)
        assert out.success is True
        assert len(out.artifacts) == 1
        assert out.artifacts[0] == "workspace://default/articles/launch.md"
        assert len(out.additional_evidence) == 1
        art_ev = out.additional_evidence[0]
        assert isinstance(art_ev, ArtifactEvidence)
        assert art_ev.mime_type == "text/markdown"

        # Verify file persisted
        fs = file_adapter.get_file_service("default")
        file_res = fs.read_file("articles/launch.md")
        assert file_res.success is True
        assert "# Blog Post: Product launch announcement" in file_res.content
        assert "**Call to Action**: Schedule a demo" in file_res.content

    def test_generation_handler_html(self, workspace_setup):
        _, file_adapter = workspace_setup
        handler = ContentGenerationCapabilityHandler(file_adapter=file_adapter)
        specialist = create_content_specialist()

        req = make_delegation_request(
            delegation_id="del_gen_02",
            capability_name="content_generation",
            inputs={
                "title": "Quarterly Highlights",
                "purpose": "Review Q2 accomplishments",
                "output_format": "html",
                "relative_path": "reports/q2_highlights.html",
                "workspace_id": "default",
            },
        )

        out = handler.execute(req, specialist)
        assert out.success is True
        assert len(out.additional_evidence) == 1
        assert out.additional_evidence[0].mime_type == "text/html"

        fs = file_adapter.get_file_service("default")
        file_res = fs.read_file("reports/q2_highlights.html")
        assert file_res.success is True
        assert "<!DOCTYPE html>" in file_res.content
        assert "Quarterly Highlights" in file_res.content

    def test_editing_handler_replace_and_append(self, workspace_setup):
        _, file_adapter = workspace_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file(
            "posts/blog.md",
            "# Old Title\n\nInitial draft paragraph.\n\n**Call to Action**: Old CTA\n",
        )

        handler = ContentEditingCapabilityHandler(file_adapter=file_adapter)
        specialist = create_content_specialist()

        req = make_delegation_request(
            delegation_id="del_edit_01",
            capability_name="content_editing",
            inputs={
                "relative_path": "posts/blog.md",
                "workspace_id": "default",
                "edits": [
                    {"action": "update_title", "title": "New Awesome Title"},
                    {"action": "replace_text", "target_text": "Initial draft paragraph.", "replacement_text": "Refined executive summary."},
                    {"action": "append_content", "content": "Additional closing remarks."},
                    {"action": "update_cta", "call_to_action": "Contact Sales Today"},
                ],
            },
        )

        out = handler.execute(req, specialist)
        assert out.success is True
        assert len(out.additional_evidence) == 1
        assert isinstance(out.additional_evidence[0], ArtifactEvidence)

        file_res = fs.read_file("posts/blog.md")
        assert file_res.success is True
        assert "# New Awesome Title" in file_res.content
        assert "Refined executive summary." in file_res.content
        assert "Additional closing remarks." in file_res.content
        assert "**Call to Action**: Contact Sales Today" in file_res.content

    def test_editing_handler_file_not_found(self, workspace_setup):
        _, file_adapter = workspace_setup
        handler = ContentEditingCapabilityHandler(file_adapter=file_adapter)
        specialist = create_content_specialist()

        req = make_delegation_request(
            delegation_id="del_edit_02",
            capability_name="content_editing",
            inputs={
                "relative_path": "non_existent.md",
                "workspace_id": "default",
                "action": "replace_text",
                "target_text": "a",
                "replacement_text": "b",
            },
        )

        out = handler.execute(req, specialist)
        assert out.success is False
        assert "CONTENT_NOT_FOUND" in out.output_text

    def test_validation_handler_direct(self):
        handler = ContentValidationCapabilityHandler()
        specialist = create_content_specialist()

        # Success case
        piece = ContentPiece(
            metadata=ContentMetadata(),
            title="Strategic Vision",
            body="Detailed overview of our multi-agent architecture and safety guarantees.",
            call_to_action="Read full report",
        )
        req = make_delegation_request(
            delegation_id="del_val_01",
            capability_name="content_validation",
            inputs={
                "content_piece": piece,
                "required_keywords": ["architecture", "safety"],
                "require_cta": True,
            },
        )
        out = handler.execute(req, specialist)
        assert out.success is True
        assert len(out.additional_evidence) == 1
        verif_ev = out.additional_evidence[0]
        assert isinstance(verif_ev, VerificationEvidence)
        assert verif_ev.verified_status == "VERIFIED"

        # Failure case (missing keyword)
        req_fail = make_delegation_request(
            delegation_id="del_val_02",
            capability_name="content_validation",
            inputs={
                "content_piece": piece,
                "required_keywords": ["quantum_computing_breakthrough"],
            },
        )
        out_fail = handler.execute(req_fail, specialist)
        assert out_fail.success is False
        assert any("quantum_computing_breakthrough" in err for err in out_fail.errors)


# ==============================================================================
# 5. Specialist Metadata & Registry Tests
# ==============================================================================


class TestContentSpecialistRegistry:
    def test_create_content_specialist_metadata(self):
        spec = create_content_specialist()
        assert spec.specialist_id == "spec_content_01"
        assert spec.name == "Content Specialist"
        assert spec.status == SpecialistStatus.ACTIVE
        assert "file_service" in spec.authorized_tools
        assert "content_validator" in spec.authorized_tools

        cap_names = [c.name for c in spec.capabilities]
        assert "content_generation" in cap_names
        assert "content_editing" in cap_names
        assert "content_validation" in cap_names

    def test_registry_registration_and_lookup(self):
        registry = InMemorySpecialistRegistryAdapter()
        spec = create_content_specialist()
        registry.register_specialist(spec)

        retrieved = registry.get_specialist_by_id("spec_content_01")
        assert retrieved is not None
        assert retrieved.specialist_id == "spec_content_01"

        sec_ctx = SecurityContext(actor_id="test_actor", session_id="test_session")
        reqs = [CapabilityRequirement(capability_name="content_generation", description="Generate content")]
        matching = registry.discover_specialists(reqs, sec_ctx)
        assert len(matching) == 1
        assert matching[0].selected_specialist.specialist_id == "spec_content_01"

        reqs_edit = [CapabilityRequirement(capability_name="content_editing", description="Edit content")]
        matching_edit = registry.discover_specialists(reqs_edit, sec_ctx)
        assert len(matching_edit) == 1
        assert matching_edit[0].selected_specialist.specialist_id == "spec_content_01"

        reqs_val = [CapabilityRequirement(capability_name="content_validation", description="Validate content")]
        matching_val = registry.discover_specialists(reqs_val, sec_ctx)
        assert len(matching_val) == 1
        assert matching_val[0].selected_specialist.specialist_id == "spec_content_01"


# ==============================================================================
# 6. SpecialistExecutionEngine Integration Tests
# ==============================================================================


class TestContentSpecialistExecutionEngineIntegration:
    @pytest.fixture
    def engine_setup(self):
        registry = InMemorySpecialistRegistryAdapter()
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("default")

        spec = create_content_specialist()
        registry.register_specialist(spec)

        engine = SpecialistExecutionEngine(
            registry_client=registry,
        )

        engine.register_handler(ContentGenerationCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(ContentEditingCapabilityHandler(file_adapter=file_adapter))
        engine.register_handler(ContentValidationCapabilityHandler())

        return engine, file_adapter, registry

    def test_engine_content_generation(self, engine_setup):
        engine, file_adapter, _ = engine_setup

        req = make_delegation_request(
            delegation_id="del_e2e_gen_01",
            capability_name="content_generation",
            inputs={
                "purpose": "Autonomous Twin Announcement",
                "content_type": "press_release",
                "channel": "press",
                "tone": "formal",
                "target_audience": "Tech Industry",
                "key_points": ["Deterministic execution", "Audit verified"],
                "call_to_action": "Visit our newsroom",
                "relative_path": "news/announcement.md",
                "workspace_id": "default",
            },
        )

        result: DelegationResult = engine.execute_delegation(req)

        assert result.status == "SUCCESS"
        assert result.evidence.contains_category(EvidenceCategory.ARTIFACT)
        assert len(result.artifacts) == 1


        fs = file_adapter.get_file_service("default")
        file_res = fs.read_file("news/announcement.md")
        assert file_res.success is True
        assert "Autonomous Twin Announcement" in file_res.content

    def test_engine_content_editing(self, engine_setup):
        engine, file_adapter, _ = engine_setup
        fs = file_adapter.get_file_service("default")
        fs.create_file("copy/draft.md", "# Draft Heading\n\nOld copy body.\n")

        req = make_delegation_request(
            delegation_id="del_e2e_edit_01",
            capability_name="content_editing",
            inputs={
                "relative_path": "copy/draft.md",
                "workspace_id": "default",
                "action": "replace_text",
                "target_text": "Old copy body.",
                "replacement_text": "Polished and refined copy body.",
            },
        )

        result: DelegationResult = engine.execute_delegation(req)

        assert result.status == "SUCCESS"
        assert result.evidence.contains_category(EvidenceCategory.ARTIFACT)

        file_res = fs.read_file("copy/draft.md")
        assert file_res.success is True
        assert "Polished and refined copy body." in file_res.content

    def test_engine_content_validation(self, engine_setup):
        engine, _, _ = engine_setup

        piece = ContentPiece(
            metadata=ContentMetadata(content_type=ContentType.BLOG_POST),
            title="Safety Framework",
            body="Comprehensive safety framework guarantees sandbox compliance.",
            call_to_action="Review specifications",
        )

        req = make_delegation_request(
            delegation_id="del_e2e_val_01",
            capability_name="content_validation",
            inputs={
                "content_piece": piece,
                "required_keywords": ["safety", "sandbox"],
                "require_cta": True,
            },
        )

        result: DelegationResult = engine.execute_delegation(req)

        assert result.status == "SUCCESS"
        assert result.evidence.contains_category(EvidenceCategory.VERIFICATION)

    def test_engine_unauthorized_capability_rejection(self, engine_setup):
        engine, _, _ = engine_setup

        req = make_delegation_request(
            delegation_id="del_unauthorized_01",
            capability_name="unauthorized_content_hack",
            inputs={"relative_path": "copy.md"},
        )

        result: DelegationResult = engine.execute_delegation(req)
        assert result.status == "FAILED" or result.status.value == "FAILED"
        assert len(result.errors) > 0


