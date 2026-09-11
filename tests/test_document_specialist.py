"""
Unit tests for Document Specialist (Member 2 Day 2 Item 4).
Verifies Document Specialist metadata, interfaces, capability handlers,
specialist registry integration, FileService persistence, and execution safety.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
import pytest
from pydantic import ValidationError

from executive_twins.client.registry_client import InMemorySpecialistRegistryAdapter
from executive_twins.documents import (
    BlockType,
    BreakBlock,
    CodeBlock,
    DevTestDocumentAdapter,
    Document,
    DocumentBlock,
    DocumentBuilder,
    DocumentEditingCapabilityHandler,
    DocumentFormat,
    DocumentGenerationCapabilityHandler,
    DocumentMetadata,
    DocumentSection,
    DocumentTemplate,
    DocumentValidationCapabilityHandler,
    HeadingBlock,
    IDocumentBuilder,
    IDocumentParser,
    IDocumentRenderer,
    IDocumentSpecialist,
    ImageRefBlock,
    ListBlock,
    MarkdownDocumentParser,
    MarkdownDocumentRenderer,
    ParagraphBlock,
    SectionSpec,
    TableBlock,
    create_document_specialist,
)
from executive_twins.execution.capability_execution_engine import (
    SpecialistExecutionEngine,
)
from executive_twins.files.dev_adapters import DevFileServiceAdapter
from executive_twins.schemas.common import FactState, SecurityContext, SpecialistStatus
from executive_twins.schemas.delegation import DelegationRequest
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
    specialist_id: str = "spec_document_01",
    task: str = "Document task",
    objective: str = "Execute document operation",
    expected_output: str = "Document output",
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


class DummyDocumentSpecialist(IDocumentSpecialist):
    """Test concrete implementation of IDocumentSpecialist interface."""

    def synthesize_document(
        self,
        title: str,
        topic: str,
        outline: Optional[List[Dict[str, Any]]] = None,
    ) -> Document:
        builder = DocumentBuilder(title=title)
        builder.add_paragraph(f"Topic: {topic}")
        if outline:
            for item in outline:
                sec = DocumentSection(title=item.get("title", "Section"))
                builder.add_section(sec)
        return builder.build()

    def edit_document(
        self,
        document: Document,
        instructions: str,
        edits: Dict[str, Any],
    ) -> Document:
        if "append_section" in edits:
            sec = DocumentSection(title=edits["append_section"])
            document.add_section(sec)
        return document

    def validate_document(
        self,
        document: Document,
    ) -> Dict[str, Any]:
        return {
            "valid": len(document.title) > 0,
            "sections": len(document.sections),
        }


class TestDocumentSpecialist:
    """Comprehensive test suite for Document Specialist."""

    # -------------------------------------------------------------------------
    # 1. Interface Conformance
    # -------------------------------------------------------------------------

    def test_document_specialist_interface_conformance(self):
        """1. Verify IDocumentSpecialist contract can be implemented and executed."""
        specialist = DummyDocumentSpecialist()
        doc = specialist.synthesize_document(
            title="Q3 Strategy",
            topic="Market Expansion",
            outline=[{"title": "Overview"}, {"title": "Execution"}],
        )
        assert doc.title == "Q3 Strategy"
        assert len(doc.sections) == 2

        edited = specialist.edit_document(
            document=doc,
            instructions="Add appendix",
            edits={"append_section": "Appendix"},
        )
        assert len(edited.sections) == 3

        val_result = specialist.validate_document(edited)
        assert val_result["valid"] is True
        assert val_result["sections"] == 3

    # -------------------------------------------------------------------------
    # 2. Metadata Factory & Registry Declarations
    # -------------------------------------------------------------------------

    def test_create_document_specialist_metadata(self):
        """2. Factory generates authoritative SpecialistMetadata with all capabilities."""
        meta = create_document_specialist()
        assert meta.specialist_id == "spec_document_01"
        assert meta.name == "Document Specialist"
        assert meta.status == SpecialistStatus.ACTIVE
        assert meta.security_level == "standard"
        assert "file_service" in meta.authorized_tools
        assert "document_builder" in meta.authorized_tools
        assert "document_parser" in meta.authorized_tools
        assert "document_validator" in meta.authorized_tools

        caps = {c.name: c for c in meta.capabilities}
        assert "document_generation" in caps
        assert "document_editing" in caps
        assert "document_validation" in caps

        assert caps["document_generation"].required_tools == ["file_service"]
        assert caps["document_editing"].required_tools == ["file_service"]
        assert caps["document_validation"].required_tools == ["document_validator"]
        assert meta.provenance.registry_id == "local_dev_registry"

    # -------------------------------------------------------------------------
    # 3. Document Generation Capability Handler
    # -------------------------------------------------------------------------

    def test_document_generation_validation_failure(self):
        """3. Parameter validation checks missing title."""
        handler = DocumentGenerationCapabilityHandler()
        # Missing title
        err = handler.validate_parameters({})
        assert err is not None
        assert "Missing required parameter 'title'" in err


    def test_document_generation_execution_pure_model(self):
        """4. Document generation builds structured document with blocks and sections."""
        handler = DocumentGenerationCapabilityHandler()
        meta = create_document_specialist()
        req = make_delegation_request(
            delegation_id="del_doc_gen_01",
            capability_name="document_generation",
            inputs={
                "title": "Autonomous Workforce Architecture",
                "blocks": [
                    {"block_type": "PARAGRAPH", "text": "High-level overview of multi-agent workforce."},
                    {"block_type": "BREAK"},
                ],
                "sections": [
                    {
                        "title": "Specialist Layer",
                        "level": 2,
                        "content": "Specialists perform concrete domain work behind security guard.",
                        "blocks": [
                            {"block_type": "LIST", "items": ["PPT Specialist", "Document Specialist"], "is_ordered": False},
                        ],
                    }
                ],
            },
        )

        output = handler.execute(req, meta)
        assert output.success is True
        assert "Successfully generated document" in output.output_text
        assert len(output.facts) == 1
        assert output.facts[0].source == "document_specialist"
        assert len(output.artifacts) == 1
        assert output.artifacts[0].startswith("workspace://default/")

    def test_document_generation_with_file_service(self):
        """5. Document generation persists rendered markdown file via FileService."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_doc_test")

        handler = DocumentGenerationCapabilityHandler(file_adapter=file_adapter)
        meta = create_document_specialist()
        req = make_delegation_request(
            delegation_id="del_doc_gen_02",
            capability_name="document_generation",
            inputs={
                "title": "Quarterly Operations Report",
                "workspace_id": "ws_doc_test",
                "relative_path": "reports/q3_operations.md",
                "sections": [
                    {
                        "title": "Executive Summary",
                        "content": "All milestones achieved on schedule with 0 regressions.",
                    }
                ],
            },
        )

        output = handler.execute(req, meta)
        assert output.success is True
        assert len(output.artifacts) == 1
        assert "reports/q3_operations.md" in output.artifacts[0]

        # Verify file actually exists in FileService
        fs = file_adapter.get_file_service("ws_doc_test")
        read_res = fs.read_file("reports/q3_operations.md")
        assert read_res.success is True
        assert "# Quarterly Operations Report" in read_res.content
        assert "## Executive Summary" in read_res.content
        assert "All milestones achieved on schedule" in read_res.content

    # -------------------------------------------------------------------------
    # 4. Document Editing Capability Handler
    # -------------------------------------------------------------------------

    def test_document_editing_parameter_validation(self):
        """6. Parameter validation enforces relative_path and edit instructions."""
        handler = DocumentEditingCapabilityHandler()
        # Missing relative_path
        err = handler.validate_parameters({"action": "append_section"})
        assert err is not None
        assert "Missing required parameter 'relative_path'" in err

        # Missing edit specification
        err = handler.validate_parameters({"relative_path": "doc.md"})
        assert err is not None
        assert "Missing edit specification" in err

        # Valid parameters
        err = handler.validate_parameters({
            "relative_path": "doc.md",
            "section_title": "Appendix",
            "new_content": "Extra notes",
        })
        assert err is None

    def test_document_editing_file_not_found(self):
        """7. Document editing fails cleanly if target file does not exist."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_edit_test")

        handler = DocumentEditingCapabilityHandler(file_adapter=file_adapter)
        meta = create_document_specialist()
        req = make_delegation_request(
            delegation_id="del_doc_edit_01",
            capability_name="document_editing",
            inputs={
                "relative_path": "non_existent.md",
                "workspace_id": "ws_edit_test",
                "action": "append_section",
                "section_title": "Notes",
                "new_content": "Some notes",
            },
        )

        output = handler.execute(req, meta)
        assert output.success is False
        assert "DOCUMENT_NOT_FOUND" in output.output_text
        assert len(output.errors) > 0

    def test_document_editing_append_and_update_sections(self):
        """8. Document editing modifies existing document and saves updated markdown."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_edit_test")
        fs = file_adapter.get_file_service("ws_edit_test")

        # Initial Document
        initial_md = "# Product Roadmap\n\n## Phase 1\nInitial MVP release.\n"
        fs.create_file("roadmap.md", initial_md)

        handler = DocumentEditingCapabilityHandler(file_adapter=file_adapter)
        meta = create_document_specialist()

        # 1. Append Section
        req1 = make_delegation_request(
            delegation_id="del_doc_edit_02",
            capability_name="document_editing",
            inputs={
                "relative_path": "roadmap.md",
                "workspace_id": "ws_edit_test",
                "action": "append_section",
                "section_title": "Phase 2",
                "new_content": "Scale infrastructure and autonomous twins.",
            },
        )
        res1 = handler.execute(req1, meta)
        assert res1.success is True
        assert "appended section 'Phase 2'" in res1.output_text

        # Verify content
        read1 = fs.read_file("roadmap.md")
        assert "## Phase 2" in read1.content
        assert "Scale infrastructure" in read1.content

        # 2. Update Section
        req2 = make_delegation_request(
            delegation_id="del_doc_edit_03",
            capability_name="document_editing",
            inputs={
                "relative_path": "roadmap.md",
                "workspace_id": "ws_edit_test",
                "action": "update_section",
                "section_title": "Phase 1",
                "new_content": "Updated MVP release with full testing suite.",
            },
        )
        res2 = handler.execute(req2, meta)
        assert res2.success is True

        read2 = fs.read_file("roadmap.md")
        assert "Updated MVP release with full testing suite." in read2.content

    def test_document_editing_batch_edits(self):
        """9. Document editing handles a list of structured edits."""
        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_edit_test")
        fs = file_adapter.get_file_service("ws_edit_test")

        initial_md = "# System Spec\n\n## Overview\nCore overview.\n"
        fs.create_file("spec.md", initial_md)

        handler = DocumentEditingCapabilityHandler(file_adapter=file_adapter)
        meta = create_document_specialist()

        req = make_delegation_request(
            delegation_id="del_doc_edit_04",
            capability_name="document_editing",
            inputs={
                "relative_path": "spec.md",
                "workspace_id": "ws_edit_test",
                "edits": [
                    {"action": "set_title", "title": "Advanced System Spec"},
                    {"action": "append_section", "section_title": "Security", "new_content": "Sandboxed FileService"},
                    {"action": "append_paragraph", "section_title": "Overview", "content": "Additional details."},
                ],
            },
        )
        res = handler.execute(req, meta)
        assert res.success is True

        read_res = fs.read_file("spec.md")
        assert "# Advanced System Spec" in read_res.content
        assert "## Security" in read_res.content
        assert "Sandboxed FileService" in read_res.content
        assert "Additional details." in read_res.content

    # -------------------------------------------------------------------------
    # 5. Document Validation Capability Handler
    # -------------------------------------------------------------------------

    def test_document_validation_parameter_validation(self):
        """10. Validation handler checks required document parameter."""
        handler = DocumentValidationCapabilityHandler()
        err = handler.validate_parameters({})
        assert err is not None
        assert "Missing required parameter 'document'" in err

    def test_document_validation_success_and_evidence(self):
        """11. Document validation generates VerificationEvidence on valid Document."""
        handler = DocumentValidationCapabilityHandler()
        meta = create_document_specialist()

        doc = (
            DocumentBuilder(title="Validated Technical Report")
            .add_paragraph("Introduction to system architecture.")
            .add_section(DocumentSection(title="Methodology", level=2))
            .build()
        )

        req = make_delegation_request(
            delegation_id="del_doc_val_01",
            capability_name="document_validation",
            inputs={"document": doc, "min_sections": 1, "require_headings": True},
        )

        res = handler.execute(req, meta)
        assert res.success is True
        assert "successfully verified" in res.output_text
        assert len(res.additional_evidence) == 1
        assert isinstance(res.additional_evidence[0], VerificationEvidence)
        assert res.additional_evidence[0].verified_status == "VERIFIED"

    def test_document_validation_failure_conditions(self):
        """12. Document validation rejects empty titles and unmet bounds."""
        handler = DocumentValidationCapabilityHandler()
        meta = create_document_specialist()

        # Unmet minimum sections
        doc = DocumentBuilder(title="Report").build()
        req = make_delegation_request(
            delegation_id="del_doc_val_02",
            capability_name="document_validation",
            inputs={"document": doc, "min_sections": 2},
        )
        res = handler.execute(req, meta)
        assert res.success is False
        assert any("below minimum required" in err for err in res.errors)

    def test_document_validation_dict_input(self):
        """13. Document validation correctly parses raw dictionary input."""
        handler = DocumentValidationCapabilityHandler()
        meta = create_document_specialist()

        raw_dict = {
            "title": "Dictionary Sourced Document",
            "sections": [{"title": "Scope", "level": 2}],
        }
        req = make_delegation_request(
            delegation_id="del_doc_val_03",
            capability_name="document_validation",
            inputs={"document": raw_dict},
        )
        res = handler.execute(req, meta)
        assert res.success is True

    # -------------------------------------------------------------------------
    # 6. Specialist Execution Engine Integration
    # -------------------------------------------------------------------------

    def test_specialist_execution_engine_end_to_end_generation(self):
        """14. Full SpecialistExecutionEngine dispatch to Document Specialist."""
        registry = InMemorySpecialistRegistryAdapter()
        meta = create_document_specialist()
        registry.register_specialist(meta)

        ws_adapter = DevTestWorkspaceAdapter()
        file_adapter = DevFileServiceAdapter(ws_adapter)
        ws_adapter.create_workspace("ws_engine_doc")

        engine = SpecialistExecutionEngine(registry_client=registry)
        gen_handler = DocumentGenerationCapabilityHandler(file_adapter=file_adapter)
        edit_handler = DocumentEditingCapabilityHandler(file_adapter=file_adapter)
        val_handler = DocumentValidationCapabilityHandler()

        engine.register_handler(gen_handler)
        engine.register_handler(edit_handler)
        engine.register_handler(val_handler)

        # 1. Execute document generation
        gen_req = make_delegation_request(
            delegation_id="del_eng_01",
            capability_name="document_generation",
            inputs={
                "title": "Autonomous Strategy Whitepaper",
                "workspace_id": "ws_engine_doc",
                "relative_path": "whitepaper.md",
                "sections": [
                    {"title": "Introduction", "content": "Autonomous workforce primer."},
                    {"title": "Architecture", "content": "Specialist separation of concerns."},
                ],
            },
        )
        gen_result = engine.execute_delegation(gen_req)
        assert gen_result.status == "SUCCESS"
        assert len(gen_result.artifacts) == 1
        assert gen_result.evidence.contains_category(EvidenceCategory.ARTIFACT)

        # 2. Execute document editing
        edit_req = make_delegation_request(
            delegation_id="del_eng_02",
            capability_name="document_editing",
            inputs={
                "relative_path": "whitepaper.md",
                "workspace_id": "ws_engine_doc",
                "action": "append_section",
                "section_title": "Conclusion",
                "new_content": "Empirical validation guarantees safety.",
            },
        )
        edit_result = engine.execute_delegation(edit_req)
        assert edit_result.status == "SUCCESS"
        assert "whitepaper.md" in edit_result.output

        # 3. Read edited file and validate
        fs = file_adapter.get_file_service("ws_engine_doc")
        read_file = fs.read_file("whitepaper.md")
        parser = MarkdownDocumentParser()
        parsed_doc = parser.parse(read_file.content)

        val_req = make_delegation_request(
            delegation_id="del_eng_03",
            capability_name="document_validation",
            inputs={"document": parsed_doc, "min_sections": 3},
        )
        val_result = engine.execute_delegation(val_req)
        assert val_result.status == "SUCCESS"
        assert val_result.evidence.contains_category(EvidenceCategory.VERIFICATION)

    def test_specialist_execution_engine_unauthorized_capability_rejection(self):
        """15. Execution engine rejects capabilities not authorized for Document Specialist."""
        registry = InMemorySpecialistRegistryAdapter()
        meta = create_document_specialist()
        registry.register_specialist(meta)

        engine = SpecialistExecutionEngine(registry_client=registry)
        gen_handler = DocumentGenerationCapabilityHandler()
        engine.register_handler(gen_handler)

        req = make_delegation_request(
            delegation_id="del_eng_unauth",
            capability_name="unauthorized_doc_capability",
            inputs={"title": "Test"},
        )
        result = engine.execute_delegation(req)
        assert result.status == "FAILED"
        assert "CAPABILITY" in result.output

